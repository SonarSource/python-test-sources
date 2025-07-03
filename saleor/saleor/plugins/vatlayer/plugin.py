from decimal import Decimal
from typing import TYPE_CHECKING, Any, Iterable, List, Optional, Union

import opentracing
import opentracing.tags
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django_countries import countries
from django_countries.fields import Country
from django_prices_vatlayer.utils import (
    fetch_rate_types,
    fetch_rates,
    get_tax_rate_types,
)
from prices import Money, TaxedMoney, TaxedMoneyRange

from ...checkout import base_calculations, calculations
from ...checkout.interface import CheckoutTaxedPricesData
from ...core.taxes import TaxType
from ...graphql.core.utils.error_codes import PluginErrorCode
from ...order.interface import OrderTaxedPricesData
from ...product.models import ProductType
from ..base_plugin import BasePlugin, ConfigurationTypeField
from ..manager import get_plugins_manager
from . import (
    DEFAULT_TAX_RATE_NAME,
    VatlayerConfiguration,
    apply_tax_to_price,
    get_taxed_shipping_price,
    get_taxes_for_country,
)

if TYPE_CHECKING:
    # flake8: noqa
    from ...account.models import Address
    from ...channel.models import Channel
    from ...checkout.fetch import CheckoutInfo, CheckoutLineInfo
    from ...checkout.models import Checkout
    from ...discount import DiscountInfo
    from ...order.models import Order, OrderLine
    from ...product.models import (
        Collection,
        Product,
        ProductVariant,
        ProductVariantChannelListing,
    )
    from ..models import PluginConfiguration


class VatlayerPlugin(BasePlugin):
    PLUGIN_ID = "mirumee.taxes.vatlayer"
    PLUGIN_NAME = "Vatlayer"
    META_CODE_KEY = "vatlayer.code"
    META_DESCRIPTION_KEY = "vatlayer.description"

    DEFAULT_CONFIGURATION = [
        {"name": "Access key", "value": None},
        {"name": "origin_country", "value": None},
        {"name": "countries_to_calculate_taxes_from_origin", "value": None},
        {"name": "excluded_countries", "value": None},
    ]

    CONFIG_STRUCTURE = {
        "origin_country": {
            "type": ConfigurationTypeField.STRING,
            "help_test": (
                "Country code in ISO format, required to calculate taxes for countries "
                "from `Countries for which taxes will be calculated from origin "
                "country`."
            ),
            "label": "Origin country",
        },
        "countries_to_calculate_taxes_from_origin": {
            "type": ConfigurationTypeField.STRING,
            "help_text": (
                "List of destination countries (separated by comma), in ISO format "
                "which will use origin country to calculate taxes."
            ),
            "label": "Countries for which taxes will be calculated from origin country",
        },
        "excluded_countries": {
            "type": ConfigurationTypeField.STRING,
            "help_text": (
                "List of countries (separated by comma), in ISO format for which no "
                "VAT should be added."
            ),
            "label": "Countries for which no VAT will be added.",
        },
        "Access key": {
            "type": ConfigurationTypeField.PASSWORD,
            "help_text": "Required to authenticate to Vatlayer API.",
            "label": "Access key",
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Convert to dict to easier take config elements
        configuration = {item["name"]: item["value"] for item in self.configuration}

        origin_country = configuration["origin_country"] or ""
        origin_country = countries.alpha2(origin_country.strip())

        countries_from_origin = configuration[
            "countries_to_calculate_taxes_from_origin"
        ]
        countries_from_origin = countries_from_origin or ""
        countries_from_origin = [
            countries.alpha2(c.strip()) for c in countries_from_origin.split(",")
        ]
        countries_from_origin = list(filter(None, countries_from_origin))

        excluded_countries = configuration["excluded_countries"] or ""
        excluded_countries = [
            countries.alpha2(c.strip()) for c in excluded_countries.split(",")
        ]
        excluded_countries = list(filter(None, excluded_countries))

        self.config = VatlayerConfiguration(
            access_key=configuration["Access key"],
            origin_country=origin_country,
            excluded_countries=excluded_countries,
            countries_from_origin=countries_from_origin,
        )
        self._cached_taxes = {}

    def _skip_plugin(
        self,
        previous_value: Union[
            TaxedMoney,
            TaxedMoneyRange,
            Decimal,
            CheckoutTaxedPricesData,
            OrderTaxedPricesData,
        ],
    ) -> bool:
        if not self.active or not self.config.access_key:
            return True

        # The previous plugin already calculated taxes so we can skip our logic
        if isinstance(previous_value, TaxedMoneyRange):
            start = previous_value.start
            stop = previous_value.stop

            return start.net != start.gross and stop.net != stop.gross

        if isinstance(previous_value, TaxedMoney):
            return previous_value.net != previous_value.gross

        if isinstance(previous_value, CheckoutTaxedPricesData):
            return (
                previous_value.price_with_sale.net
                != previous_value.price_with_sale.gross
            )

        if isinstance(previous_value, OrderTaxedPricesData):
            return (
                previous_value.price_with_discounts.net
                != previous_value.price_with_discounts.gross
            )

        return False

    def calculate_checkout_total(
        self,
        checkout_info: "CheckoutInfo",
        lines: List["CheckoutLineInfo"],
        address: Optional["Address"],
        discounts: List["DiscountInfo"],
        previous_value: TaxedMoney,
    ) -> TaxedMoney:
        if self._skip_plugin(previous_value):
            return previous_value

        manager = get_plugins_manager()
        return (
            calculations.checkout_subtotal(
                manager=manager,
                checkout_info=checkout_info,
                lines=lines,
                address=address,
                discounts=discounts,
            )
            + calculations.checkout_shipping_price(
                manager=manager,
                checkout_info=checkout_info,
                lines=lines,
                address=address,
                discounts=discounts,
            )
            - checkout_info.checkout.discount
        )

    def _get_taxes_for_country(self, country: Country):
        """Try to fetch cached taxes on the plugin level.

        If the plugin doesn't have cached taxes for a given country it will fetch it
        from cache or db.
        """
        if not country:
            origin_country_code = self.config.origin_country
            if not origin_country_code:
                company_address = Site.objects.get_current().settings.company_address
                origin_country_code = (
                    company_address.country
                    if company_address
                    else settings.DEFAULT_COUNTRY
                )

            country = Country(origin_country_code)
        country_code = country.code

        if country_code in self.config.countries_from_origin:
            country_code = self.config.origin_country

        if country_code in self.config.excluded_countries:
            return None

        if country_code in self._cached_taxes:
            return self._cached_taxes[country_code]

        country = Country(country_code)
        taxes = get_taxes_for_country(country)
        self._cached_taxes[country_code] = taxes
        return taxes

    def calculate_checkout_shipping(
        self,
        checkout_info: "CheckoutInfo",
        lines: List["CheckoutLineInfo"],
        address: Optional["Address"],
        discounts: List["DiscountInfo"],
        previous_value: TaxedMoney,
    ) -> TaxedMoney:
        """Calculate shipping gross for checkout."""
        if self._skip_plugin(previous_value):
            return previous_value

        taxes = None
        if address:
            taxes = self._get_taxes_for_country(address.country)
        if not checkout_info.delivery_method_info.delivery_method:
            return previous_value
        shipping_price = getattr(
            checkout_info.delivery_method_info.delivery_method, "price", previous_value
        )
        return get_taxed_shipping_price(shipping_price, taxes)

    def calculate_order_shipping(
        self, order: "Order", previous_value: TaxedMoney
    ) -> TaxedMoney:
        if self._skip_plugin(previous_value):
            return previous_value

        address = order.shipping_address or order.billing_address
        taxes = None
        if address:
            taxes = self._get_taxes_for_country(address.country)
        if not order.shipping_method:
            return previous_value
        shipping_price = order.shipping_method.channel_listings.get(
            channel_id=order.channel_id
        ).price
        return get_taxed_shipping_price(shipping_price, taxes)

    def calculate_checkout_line_total(
        self,
        checkout_info: "CheckoutInfo",
        lines: List["CheckoutLineInfo"],
        checkout_line_info: "CheckoutLineInfo",
        address: Optional["Address"],
        discounts: Iterable["DiscountInfo"],
        previous_value: CheckoutTaxedPricesData,
    ) -> CheckoutTaxedPricesData:
        unit_taxed_prices_data = self.__calculate_checkout_line_unit_price(
            checkout_line_info,
            checkout_info.channel,
            discounts,
            address,
            previous_value,
        )
        if not unit_taxed_prices_data:
            return previous_value

        quantity = checkout_line_info.line.quantity
        return CheckoutTaxedPricesData(
            price_with_discounts=unit_taxed_prices_data.price_with_discounts * quantity,
            price_with_sale=unit_taxed_prices_data.price_with_sale * quantity,
            undiscounted_price=unit_taxed_prices_data.undiscounted_price * quantity,
        )

    def calculate_order_line_total(
        self,
        order: "Order",
        order_line: "OrderLine",
        variant: "ProductVariant",
        product: "Product",
        previous_value: OrderTaxedPricesData,
    ) -> OrderTaxedPricesData:
        unit_price_data = self.__calculate_order_line_unit(
            order,
            order_line,
            variant,
            product,
            previous_value,
        )
        if unit_price_data is None:
            return previous_value
        quantity = order_line.quantity
        return OrderTaxedPricesData(
            undiscounted_price=unit_price_data.undiscounted_price * quantity,
            price_with_discounts=unit_price_data.price_with_discounts * quantity,
        )

    def calculate_checkout_line_unit_price(
        self,
        checkout_info: "CheckoutInfo",
        lines: Iterable["CheckoutLineInfo"],
        checkout_line_info: "CheckoutLineInfo",
        address: Optional["Address"],
        discounts: Iterable["DiscountInfo"],
        previous_value: CheckoutTaxedPricesData,
    ) -> CheckoutTaxedPricesData:
        unit_taxed_prices_data = self.__calculate_checkout_line_unit_price(
            checkout_line_info,
            checkout_info.channel,
            discounts,
            address,
            previous_value,
        )
        return unit_taxed_prices_data if unit_taxed_prices_data else previous_value

    def __calculate_checkout_line_unit_price(
        self,
        checkout_line_info: "CheckoutLineInfo",
        channel: "Channel",
        discounts: Iterable["DiscountInfo"],
        address: Optional["Address"],
        previous_value: CheckoutTaxedPricesData,
    ):
        if self._skip_plugin(previous_value):
            return

        prices_data = base_calculations.calculate_base_line_unit_price(
            checkout_line_info,
            channel,
            discounts,
        )

        country = address.country if address else None
        taxed_prices_data = CheckoutTaxedPricesData(
            price_with_sale=self.__apply_taxes_to_product(
                checkout_line_info.product, prices_data.price_with_sale, country
            ),
            undiscounted_price=self.__apply_taxes_to_product(
                checkout_line_info.product, prices_data.undiscounted_price, country
            ),
            price_with_discounts=self.__apply_taxes_to_product(
                checkout_line_info.product, prices_data.price_with_discounts, country
            ),
        )
        return taxed_prices_data

    def calculate_order_line_unit(
        self,
        order: "Order",
        order_line: "OrderLine",
        variant: "ProductVariant",
        product: "Product",
        previous_value: OrderTaxedPricesData,
    ) -> OrderTaxedPricesData:
        unit_price_data = self.__calculate_order_line_unit(
            order, order_line, variant, product, previous_value
        )
        return unit_price_data if unit_price_data is not None else previous_value

    def __calculate_order_line_unit(
        self,
        order: "Order",
        order_line: "OrderLine",
        variant: "ProductVariant",
        product: "Product",
        previous_value: OrderTaxedPricesData,
    ):
        if self._skip_plugin(previous_value):
            return

        address = order.shipping_address or order.billing_address
        country = address.country if address else None
        if not variant:
            return
        taxed_prices_data = OrderTaxedPricesData(
            undiscounted_price=self.__apply_taxes_to_product(
                product, order_line.undiscounted_unit_price, country
            ),
            price_with_discounts=self.__apply_taxes_to_product(
                product, order_line.unit_price, country
            ),
        )
        return taxed_prices_data

    def get_checkout_line_tax_rate(
        self,
        checkout_info: "CheckoutInfo",
        lines: Iterable["CheckoutLineInfo"],
        checkout_line_info: "CheckoutLineInfo",
        address: Optional["Address"],
        discounts: Iterable["DiscountInfo"],
        previous_value: Decimal,
    ) -> Decimal:
        return self._get_tax_rate(checkout_line_info.product, address, previous_value)

    def get_order_line_tax_rate(
        self,
        order: "Order",
        product: "Product",
        variant: "ProductVariant",
        address: Optional["Address"],
        previous_value: Decimal,
    ) -> Decimal:
        return self._get_tax_rate(product, address, previous_value)

    def _get_tax_rate(
        self, product: "Product", address: Optional["Address"], previous_value: Decimal
    ):
        if self._skip_plugin(previous_value):
            return previous_value
        country = address.country if address else None
        taxes, tax_rate = self.__get_tax_data_for_product(product, country)
        if not taxes or not tax_rate:
            return previous_value
        tax = taxes.get(tax_rate) or taxes.get(DEFAULT_TAX_RATE_NAME)
        # tax value is given in percentage so it need be be converted into decimal value
        return Decimal(tax["value"] / 100)

    def get_checkout_shipping_tax_rate(
        self,
        checkout_info: "CheckoutInfo",
        lines: Iterable["CheckoutLineInfo"],
        address: Optional["Address"],
        discounts: Iterable["DiscountInfo"],
        previous_value: Decimal,
    ):
        return self._get_shipping_tax_rate(address, previous_value)

    def get_order_shipping_tax_rate(self, order: "Order", previous_value: Decimal):
        address = order.shipping_address or order.billing_address
        return self._get_shipping_tax_rate(address, previous_value)

    def _get_shipping_tax_rate(
        self, address: Optional["Address"], previous_value: Decimal
    ):
        if self._skip_plugin(previous_value):
            return previous_value
        country = address.country if address else None
        taxes = self._get_taxes_for_country(country)
        if not taxes:
            return previous_value
        tax = taxes.get(DEFAULT_TAX_RATE_NAME)
        # tax value is given in percentage so it need be be converted into decimal value
        return Decimal(tax["value"]) / 100

    def get_tax_rate_type_choices(
        self, previous_value: List["TaxType"]
    ) -> List["TaxType"]:
        if not self.active:
            return previous_value

        rate_types = get_tax_rate_types() + [DEFAULT_TAX_RATE_NAME]
        choices = [
            TaxType(code=rate_name, description=rate_name) for rate_name in rate_types
        ]
        # sort choices alphabetically by translations
        return sorted(choices, key=lambda x: x.code)

    def show_taxes_on_storefront(self, previous_value: bool) -> bool:
        if not self.active:
            return previous_value
        return True

    def apply_taxes_to_product(
        self,
        product: "Product",
        price: Money,
        country: Country,
        previous_value: TaxedMoney,
    ) -> TaxedMoney:
        if self._skip_plugin(previous_value):
            return previous_value
        return self.__apply_taxes_to_product(product, price, country)

    def __apply_taxes_to_product(
        self, product: "Product", price: Money, country: Country
    ):
        taxes, tax_rate = self.__get_tax_data_for_product(product, country)
        return apply_tax_to_price(taxes, tax_rate, price)

    def __get_tax_data_for_product(self, product: "Product", country: Country):
        taxes = None
        if country and product.charge_taxes:
            taxes = self._get_taxes_for_country(country)
        product_tax_rate = self.__get_tax_code_from_object_meta(product).code
        tax_rate = (
            product_tax_rate
            or self.__get_tax_code_from_object_meta(product.product_type).code
        )
        return taxes, tax_rate

    def assign_tax_code_to_object_meta(
        self,
        obj: Union["Product", "ProductType"],
        tax_code: Optional[str],
        previous_value: Any,
    ):
        if not self.active:
            return previous_value

        if tax_code is None and obj.pk:
            obj.delete_value_from_metadata(self.META_CODE_KEY)
            obj.delete_value_from_metadata(self.META_DESCRIPTION_KEY)
            return previous_value

        tax_item = {self.META_CODE_KEY: tax_code, self.META_DESCRIPTION_KEY: tax_code}
        obj.store_value_in_metadata(items=tax_item)
        return previous_value

    def get_tax_code_from_object_meta(
        self, obj: Union["Product", "ProductType"], previous_value: "TaxType"
    ) -> "TaxType":
        if not self.active:
            return previous_value
        return self.__get_tax_code_from_object_meta(obj)

    def __get_tax_code_from_object_meta(
        self, obj: Union["Product", "ProductType"]
    ) -> "TaxType":

        # Product has None as it determines if we overwrite taxes for the product
        default_tax_code = None
        default_tax_description = None
        if isinstance(obj, ProductType):
            default_tax_code = DEFAULT_TAX_RATE_NAME
            default_tax_description = DEFAULT_TAX_RATE_NAME

        tax_code = obj.get_value_from_metadata(self.META_CODE_KEY, default_tax_code)
        tax_description = obj.get_value_from_metadata(
            self.META_DESCRIPTION_KEY, default_tax_description
        )
        return TaxType(code=tax_code, description=tax_description)

    def get_tax_rate_percentage_value(
        self, obj: Union["Product", "ProductType"], country: Country, previous_value
    ) -> Decimal:
        """Return tax rate percentage value for given tax rate type in the country."""
        if not self.active:
            return previous_value
        taxes = self._get_taxes_for_country(country)
        if not taxes:
            return Decimal(0)
        rate_name = self.__get_tax_code_from_object_meta(obj).code
        tax = taxes.get(rate_name) or taxes.get(DEFAULT_TAX_RATE_NAME)
        return Decimal(tax["value"])

    def fetch_taxes_data(self, previous_value: Any) -> Any:
        """Triggered when ShopFetchTaxRates mutation is called."""
        if not self.active:
            return previous_value
        with opentracing.global_tracer().start_active_span(
            "vatlayer.fetch_taxes_data"
        ) as scope:
            span = scope.span
            span.set_tag(opentracing.tags.COMPONENT, "tax")
            span.set_tag("service.name", "vatlayer")
            fetch_rates(self.config.access_key)
        return True

    @classmethod
    def validate_plugin_configuration(
        cls, plugin_configuration: "PluginConfiguration", **kwargs
    ):
        """Validate if provided configuration is correct."""
        configuration = plugin_configuration.configuration
        configuration = {item["name"]: item["value"] for item in configuration}

        access_key = configuration.get("Access key")
        if plugin_configuration.active and not access_key:
            raise ValidationError(
                {
                    "Access key": ValidationError(
                        "Cannot be enabled without provided Access key",
                        code=PluginErrorCode.INVALID.value,
                    )
                }
            )
        if access_key and plugin_configuration.active:
            # let's check if access_key works
            fetched_data = fetch_rate_types(access_key=access_key)
            if not fetched_data["success"]:
                raise ValidationError(
                    {
                        "Access key": ValidationError(
                            "Cannot enable Vatlayer. Incorrect API key.",
                            code=PluginErrorCode.INVALID.value,
                        )
                    }
                )
        countries_from_origin = configuration.get(
            "countries_to_calculate_taxes_from_origin"
        )
        origin_country = configuration.get("origin_country")
        if countries_from_origin and not origin_country:
            raise ValidationError(
                {
                    "origin_country": ValidationError(
                        "Source country required when `Countries for which taxes will "
                        "be calculated from origin country` provided.",
                        code=PluginErrorCode.INVALID.value,
                    )
                }
            )
