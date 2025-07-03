from unittest.mock import patch

import graphene
import pytest

from ....account.models import Address
from ....warehouse import WarehouseClickAndCollectOption
from ....warehouse.error_codes import WarehouseErrorCode
from ....warehouse.models import Stock, Warehouse
from ...tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)
from ..enums import WarehouseClickAndCollectOptionEnum

QUERY_WAREHOUSES = """
query {
    warehouses(first:100) {
        totalCount
        edges {
            node {
                id
                name
                companyName
                email
                shippingZones(first:100) {
                    edges {
                        node {
                            name
                            countries {
                                country
                            }
                        }
                    }
                }
                address {
                    city
                    postalCode
                    country {
                        country
                    }
                    phone
                }
            }
        }
    }
}
"""

QUERY_WAREHOUSES_WITH_FILTERS = """
query Warehouses($filters: WarehouseFilterInput) {
    warehouses(first:100, filter: $filters) {
        totalCount
        edges {
            node {
                id
                name
                companyName
                email
            }
        }
    }
}
"""

QUERY_WERHOUSES_WITH_FILTERS_NO_IDS = """
query Warehouses($filters: WarehouseFilterInput) {
    warehouses(first:100, filter: $filters) {
        totalCount
        edges {
            node {
                name
                companyName
                email
            }
        }
    }
}
"""

QUERY_WAREHOUSE = """
query warehouse($id: ID!){
    warehouse(id: $id) {
        id
        name
        companyName
        email
        shippingZones(first: 100) {
            edges {
                node {
                    name
                    countries {
                        country
                    }
                }
            }
        }
        address {
            streetAddress1
            streetAddress2
            postalCode
            city
            phone
        }
    }
}
"""


MUTATION_CREATE_WAREHOUSE = """
mutation createWarehouse($input: WarehouseCreateInput!) {
    createWarehouse(input: $input){
        warehouse {
            id
            name
            slug
            companyName
            address {
                id
            }
        }
        errors {
            message
            field
            code
        }
    }
}
"""


MUTATION_UPDATE_WAREHOUSE = """
mutation updateWarehouse($input: WarehouseUpdateInput!, $id: ID!) {
    updateWarehouse(id: $id, input: $input) {
        errors {
            message
            field
            code
        }
        warehouse {
            name
            slug
            companyName
            isPrivate
            clickAndCollectOption
            address {
                id
                streetAddress1
                streetAddress2
            }
        }
    }
}
"""


MUTATION_DELETE_WAREHOUSE = """
mutation deleteWarehouse($id: ID!) {
    deleteWarehouse(id: $id) {
        errors {
            message
            field
            code
        }
    }
}
"""


MUTATION_ASSIGN_SHIPPING_ZONE_WAREHOUSE = """
mutation assignWarehouseShippingZone($id: ID!, $shippingZoneIds: [ID!]!) {
  assignWarehouseShippingZone(id: $id, shippingZoneIds: $shippingZoneIds) {
    errors {
      field
      message
      code
    }
  }
}

"""


MUTATION_UNASSIGN_SHIPPING_ZONE_WAREHOUSE = """
mutation unassignWarehouseShippingZone($id: ID!, $shippingZoneIds: [ID!]!) {
  unassignWarehouseShippingZone(id: $id, shippingZoneIds: $shippingZoneIds) {
    errors {
      field
      message
      code
    }
  }
}

"""


def test_warehouse_query(staff_api_client, warehouse, permission_manage_products):
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)

    response = staff_api_client.post_graphql(
        QUERY_WAREHOUSE,
        variables={"id": warehouse_id},
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)

    queried_warehouse = content["data"]["warehouse"]
    assert queried_warehouse["name"] == warehouse.name
    assert queried_warehouse["email"] == warehouse.email

    shipping_zones = queried_warehouse["shippingZones"]["edges"]
    assert len(shipping_zones) == warehouse.shipping_zones.count()
    queried_shipping_zone = shipping_zones[0]["node"]
    shipipng_zone = warehouse.shipping_zones.first()
    assert queried_shipping_zone["name"] == shipipng_zone.name
    assert len(queried_shipping_zone["countries"]) == len(shipipng_zone.countries)

    address = warehouse.address
    queried_address = queried_warehouse["address"]
    assert queried_address["streetAddress1"] == address.street_address_1
    assert queried_address["postalCode"] == address.postal_code


def test_warehouse_query_as_staff_with_manage_orders(
    staff_api_client, warehouse, permission_manage_orders
):
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)

    response = staff_api_client.post_graphql(
        QUERY_WAREHOUSE,
        variables={"id": warehouse_id},
        permissions=[permission_manage_orders],
    )
    content = get_graphql_content(response)

    queried_warehouse = content["data"]["warehouse"]
    assert queried_warehouse["name"] == warehouse.name
    assert queried_warehouse["email"] == warehouse.email

    shipping_zones = queried_warehouse["shippingZones"]["edges"]
    assert len(shipping_zones) == warehouse.shipping_zones.count()
    queried_shipping_zone = shipping_zones[0]["node"]
    shipipng_zone = warehouse.shipping_zones.first()
    assert queried_shipping_zone["name"] == shipipng_zone.name
    assert len(queried_shipping_zone["countries"]) == len(shipipng_zone.countries)

    address = warehouse.address
    queried_address = queried_warehouse["address"]
    assert queried_address["streetAddress1"] == address.street_address_1
    assert queried_address["postalCode"] == address.postal_code


def test_warehouse_query_as_staff_with_manage_shipping(
    staff_api_client, warehouse, permission_manage_shipping
):
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)

    response = staff_api_client.post_graphql(
        QUERY_WAREHOUSE,
        variables={"id": warehouse_id},
        permissions=[permission_manage_shipping],
    )
    content = get_graphql_content(response)

    queried_warehouse = content["data"]["warehouse"]
    assert queried_warehouse["name"] == warehouse.name
    assert queried_warehouse["email"] == warehouse.email

    shipping_zones = queried_warehouse["shippingZones"]["edges"]
    assert len(shipping_zones) == warehouse.shipping_zones.count()
    queried_shipping_zone = shipping_zones[0]["node"]
    shipipng_zone = warehouse.shipping_zones.first()
    assert queried_shipping_zone["name"] == shipipng_zone.name
    assert len(queried_shipping_zone["countries"]) == len(shipipng_zone.countries)

    address = warehouse.address
    queried_address = queried_warehouse["address"]
    assert queried_address["streetAddress1"] == address.street_address_1
    assert queried_address["postalCode"] == address.postal_code


def test_warehouse_query_as_staff_with_manage_apps(
    staff_api_client, warehouse, permission_manage_apps
):
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)

    response = staff_api_client.post_graphql(
        QUERY_WAREHOUSE,
        variables={"id": warehouse_id},
        permissions=[permission_manage_apps],
    )

    assert_no_permission(response)


def test_warehouse_query_as_customer(user_api_client, warehouse):
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)

    response = user_api_client.post_graphql(
        QUERY_WAREHOUSE,
        variables={"id": warehouse_id},
    )

    assert_no_permission(response)


def test_staff_query_warehouse_by_invalid_id(
    staff_api_client, warehouse, permission_manage_shipping
):
    id = "bh/"
    variables = {"id": id}
    response = staff_api_client.post_graphql(
        QUERY_WAREHOUSE, variables, permissions=[permission_manage_shipping]
    )
    content = get_graphql_content_from_response(response)
    assert len(content["errors"]) == 1
    assert content["errors"][0]["message"] == f"Couldn't resolve id: {id}."
    assert content["data"]["warehouse"] is None


def test_staff_query_warehouse_with_invalid_object_type(
    staff_api_client, permission_manage_shipping, warehouse
):
    variables = {"id": graphene.Node.to_global_id("Order", warehouse.pk)}
    response = staff_api_client.post_graphql(
        QUERY_WAREHOUSE, variables, permissions=[permission_manage_shipping]
    )
    content = get_graphql_content(response)
    assert content["data"]["warehouse"] is None


def test_query_warehouses_as_staff_with_manage_orders(
    staff_api_client, warehouse, permission_manage_orders
):
    response = staff_api_client.post_graphql(
        QUERY_WAREHOUSES, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)["data"]
    assert content["warehouses"]["totalCount"] == Warehouse.objects.count()
    warehouses = content["warehouses"]["edges"]
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)
    warehouse_first = warehouses[0]["node"]
    assert warehouse_first["id"] == warehouse_id
    assert warehouse_first["name"] == warehouse.name
    assert (
        len(warehouse_first["shippingZones"]["edges"])
        == warehouse.shipping_zones.count()
    )


def test_query_warehouses_as_staff_with_manage_shipping(
    staff_api_client, warehouse, permission_manage_shipping
):
    response = staff_api_client.post_graphql(
        QUERY_WAREHOUSES, permissions=[permission_manage_shipping]
    )
    content = get_graphql_content(response)["data"]
    assert content["warehouses"]["totalCount"] == Warehouse.objects.count()
    warehouses = content["warehouses"]["edges"]
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)
    warehouse_first = warehouses[0]["node"]
    assert warehouse_first["id"] == warehouse_id
    assert warehouse_first["name"] == warehouse.name
    assert (
        len(warehouse_first["shippingZones"]["edges"])
        == warehouse.shipping_zones.count()
    )


def test_query_warehouses_as_staff_with_manage_apps(
    staff_api_client, warehouse, permission_manage_apps
):
    response = staff_api_client.post_graphql(
        QUERY_WAREHOUSES, permissions=[permission_manage_apps]
    )
    assert_no_permission(response)


def test_query_warehouses_as_customer(
    user_api_client, warehouse, permission_manage_apps
):
    response = user_api_client.post_graphql(QUERY_WAREHOUSES)
    assert_no_permission(response)


def test_query_warehouses(staff_api_client, warehouse, permission_manage_products):
    response = staff_api_client.post_graphql(
        QUERY_WAREHOUSES, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)["data"]
    assert content["warehouses"]["totalCount"] == Warehouse.objects.count()
    warehouses = content["warehouses"]["edges"]
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)
    warehouse_first = warehouses[0]["node"]
    assert warehouse_first["id"] == warehouse_id
    assert warehouse_first["name"] == warehouse.name
    assert (
        len(warehouse_first["shippingZones"]["edges"])
        == warehouse.shipping_zones.count()
    )


def test_query_warehouses_with_filters_name(
    staff_api_client, permission_manage_products, warehouse
):
    variables_exists = {"filters": {"search": "warehouse"}}
    response = staff_api_client.post_graphql(
        QUERY_WAREHOUSES_WITH_FILTERS,
        variables=variables_exists,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.id)
    content_warehouse = content["data"]["warehouses"]["edges"][0]["node"]
    assert content_warehouse["id"] == warehouse_id
    variables_does_not_exists = {"filters": {"search": "Absolutelywrong name"}}
    response1 = staff_api_client.post_graphql(
        QUERY_WAREHOUSES_WITH_FILTERS, variables=variables_does_not_exists
    )
    content1 = get_graphql_content(response1)
    total_count = content1["data"]["warehouses"]["totalCount"]
    assert total_count == 0


def test_query_warehouse_with_filters_email(
    staff_api_client, permission_manage_products, warehouse
):
    variables_exists = {"filters": {"search": "test"}}
    response_exists = staff_api_client.post_graphql(
        QUERY_WAREHOUSES_WITH_FILTERS,
        variables=variables_exists,
        permissions=[permission_manage_products],
    )
    content_exists = get_graphql_content(response_exists)
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.id)
    content_warehouse = content_exists["data"]["warehouses"]["edges"][0]["node"]
    assert content_warehouse["id"] == warehouse_id

    variable_does_not_exists = {"filters": {"search": "Bad@email.pl"}}
    response_not_exists = staff_api_client.post_graphql(
        QUERY_WAREHOUSES_WITH_FILTERS, variables=variable_does_not_exists
    )
    content_not_exists = get_graphql_content(response_not_exists)
    total_count = content_not_exists["data"]["warehouses"]["totalCount"]
    assert total_count == 0


def test_query_warehouse_with_filters_by_ids(
    staff_api_client, permission_manage_products, warehouse, warehouse_no_shipping_zone
):
    warehouse_ids = [
        graphene.Node.to_global_id("Warehouse", warehouse.id),
        graphene.Node.to_global_id("Warehouse", warehouse_no_shipping_zone.id),
    ]
    variables_exists = {"filters": {"ids": warehouse_ids}}
    response_exists = staff_api_client.post_graphql(
        QUERY_WAREHOUSES_WITH_FILTERS,
        variables=variables_exists,
        permissions=[permission_manage_products],
    )
    content_exists = get_graphql_content(response_exists)

    content_warehouses = content_exists["data"]["warehouses"]["edges"]
    for content_warehouse in content_warehouses:
        assert content_warehouse["node"]["id"] in warehouse_ids
    assert content_exists["data"]["warehouses"]["totalCount"] == 2


def test_query_warehouse_with_filters_by_id(
    staff_api_client, permission_manage_products, warehouse, warehouse_no_shipping_zone
):
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.id)
    variables_exists = {"filters": {"ids": [warehouse_id]}}
    response_exists = staff_api_client.post_graphql(
        QUERY_WAREHOUSES_WITH_FILTERS,
        variables=variables_exists,
        permissions=[permission_manage_products],
    )
    content_exists = get_graphql_content(response_exists)

    content_warehouses = content_exists["data"]["warehouses"]["edges"]
    assert content_warehouses[0]["node"]["id"] == warehouse_id
    assert content_exists["data"]["warehouses"]["totalCount"] == 1


@pytest.mark.parametrize(
    "graphql_filter, db_filter", [("true", True), ("false", False)]
)
def test_query_warehouse_with_filters_by_is_private(
    staff_api_client,
    permission_manage_products,
    warehouses_for_cc,
    graphql_filter,
    db_filter,
):
    db_count = Warehouse.objects.filter(is_private=db_filter).count()
    variables_exists = {"filters": {"isPrivate": graphql_filter}}
    response_exists = staff_api_client.post_graphql(
        QUERY_WAREHOUSES_WITH_FILTERS,
        variables=variables_exists,
        permissions=[permission_manage_products],
    )
    content_exists = get_graphql_content(response_exists)

    assert content_exists["data"]["warehouses"]["totalCount"] == db_count


@pytest.mark.parametrize(
    "db_option, graphql_option",
    [
        (WarehouseClickAndCollectOption.DISABLED, "DISABLED"),
        (WarehouseClickAndCollectOption.ALL_WAREHOUSES, "ALL"),
        (WarehouseClickAndCollectOption.LOCAL_STOCK, "LOCAL"),
    ],
)
def test_query_warehouse_with_filters_by_click_and_collect_option(
    staff_api_client,
    permission_manage_products,
    warehouses_for_cc,
    db_option,
    graphql_option,
):
    db_count = Warehouse.objects.filter(click_and_collect_option=db_option).count()
    variables_exists = {"filters": {"clickAndCollectOption": graphql_option}}
    response_exists = staff_api_client.post_graphql(
        QUERY_WAREHOUSES_WITH_FILTERS,
        variables=variables_exists,
        permissions=[permission_manage_products],
    )
    content_exists = get_graphql_content(response_exists)
    assert content_exists["data"]["warehouses"]["totalCount"] == db_count


def test_query_warehouses_with_filters_and_no_id(
    staff_api_client, permission_manage_products, warehouse
):
    variables_exists = {"filters": {"search": "test"}}
    response_exists = staff_api_client.post_graphql(
        QUERY_WAREHOUSES_WITH_FILTERS,
        variables=variables_exists,
        permissions=[permission_manage_products],
    )
    content_exists = get_graphql_content(response_exists)
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.id)
    content_warehouse = content_exists["data"]["warehouses"]["edges"][0]["node"]
    assert content_warehouse["id"] == warehouse_id

    variable_does_not_exists = {"filters": {"search": "Bad@email.pl"}}
    response_not_exists = staff_api_client.post_graphql(
        QUERY_WAREHOUSES_WITH_FILTERS, variables=variable_does_not_exists
    )
    content_not_exists = get_graphql_content(response_not_exists)
    total_count = content_not_exists["data"]["warehouses"]["totalCount"]
    assert total_count == 0


def test_mutation_create_warehouse(
    staff_api_client, permission_manage_products, shipping_zone
):
    variables = {
        "input": {
            "name": "Test warehouse",
            "slug": "test-warhouse",
            "email": "test-admin@example.com",
            "address": {
                "streetAddress1": "Teczowa 8",
                "city": "Wroclaw",
                "country": "PL",
                "postalCode": "53-601",
                "companyName": "Amazing Company Inc",
            },
            "shippingZones": [
                graphene.Node.to_global_id("ShippingZone", shipping_zone.id)
            ],
        }
    }

    response = staff_api_client.post_graphql(
        MUTATION_CREATE_WAREHOUSE,
        variables=variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    assert Warehouse.objects.count() == 1
    warehouse = Warehouse.objects.first()
    created_warehouse = content["data"]["createWarehouse"]["warehouse"]
    assert created_warehouse["id"] == graphene.Node.to_global_id(
        "Warehouse", warehouse.id
    )
    assert created_warehouse["name"] == warehouse.name
    assert created_warehouse["slug"] == warehouse.slug
    assert created_warehouse["companyName"] == warehouse.address.company_name


def test_mutation_create_warehouse_does_not_create_when_name_is_empty_string(
    staff_api_client, permission_manage_products, shipping_zone
):
    variables = {
        "input": {
            "name": "  ",
            "slug": "test-warhouse",
            "email": "test-admin@example.com",
            "address": {
                "streetAddress1": "Teczowa 8",
                "city": "Wroclaw",
                "country": "PL",
                "postalCode": "53-601",
                "companyName": "Amazing Company Inc",
            },
            "shippingZones": [
                graphene.Node.to_global_id("ShippingZone", shipping_zone.id)
            ],
        }
    }

    response = staff_api_client.post_graphql(
        MUTATION_CREATE_WAREHOUSE,
        variables=variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    data = content["data"]["createWarehouse"]
    errors = data["errors"]
    assert Warehouse.objects.count() == 0
    assert len(errors) == 1
    assert errors[0]["field"] == "name"
    assert errors[0]["code"] == WarehouseErrorCode.REQUIRED.name


def test_create_warehouse_creates_address(
    staff_api_client, permission_manage_products, shipping_zone
):
    variables = {
        "input": {
            "name": "Test warehouse",
            "email": "test-admin@example.com",
            "address": {
                "streetAddress1": "Teczowa 8",
                "city": "Wroclaw",
                "country": "PL",
                "companyName": "Amazing Company Inc",
                "postalCode": "53-601",
            },
            "shippingZones": [
                graphene.Node.to_global_id("ShippingZone", shipping_zone.id)
            ],
        }
    }
    assert not Address.objects.exists()
    response = staff_api_client.post_graphql(
        MUTATION_CREATE_WAREHOUSE,
        variables=variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    errors = content["data"]["createWarehouse"]["errors"]
    assert len(errors) == 0
    assert Address.objects.count() == 1
    address = Address.objects.get(street_address_1="Teczowa 8", city="WROCLAW")
    address_id = graphene.Node.to_global_id("Address", address.id)
    warehouse_data = content["data"]["createWarehouse"]["warehouse"]
    assert warehouse_data["address"]["id"] == address_id
    assert address.street_address_1 == "Teczowa 8"
    assert address.company_name == "Amazing Company Inc"
    assert address.city == "WROCLAW"


@pytest.mark.parametrize(
    "input_slug, expected_slug",
    (
        ("test-slug", "test-slug"),
        (None, "test-warehouse"),
        ("", "test-warehouse"),
    ),
)
def test_create_warehouse_with_given_slug(
    staff_api_client, permission_manage_products, input_slug, expected_slug
):
    query = MUTATION_CREATE_WAREHOUSE
    name = "Test warehouse"
    variables = {"name": name, "slug": input_slug}
    variables = {
        "input": {
            "name": name,
            "slug": input_slug,
            "address": {
                "streetAddress1": "Teczowa 8",
                "city": "Wroclaw",
                "country": "PL",
                "postalCode": "53-601",
            },
        }
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["createWarehouse"]
    assert not data["errors"]
    assert data["warehouse"]["slug"] == expected_slug


def test_mutation_update_warehouse(
    staff_api_client, warehouse, permission_manage_products
):
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.id)
    warehouse_old_name = warehouse.name
    warehouse_slug = warehouse.slug
    variables = {
        "id": warehouse_id,
        "input": {"name": "New name"},
    }
    staff_api_client.post_graphql(
        MUTATION_UPDATE_WAREHOUSE,
        variables=variables,
        permissions=[permission_manage_products],
    )
    warehouse.refresh_from_db()
    assert not (warehouse.name == warehouse_old_name)
    assert warehouse.name == "New name"
    assert warehouse.slug == warehouse_slug


def test_mutation_update_warehouse_can_update_address(
    staff_api_client, warehouse, permission_manage_products
):
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)
    address_id = graphene.Node.to_global_id("Address", warehouse.address.pk)
    address = warehouse.address
    variables = {
        "id": warehouse_id,
        "input": {
            "name": warehouse.name,
            "address": {
                "streetAddress1": "Teczowa 8",
                "streetAddress2": "Ground floor",
                "companyName": "",
                "city": address.city,
                "country": address.country.code,
                "postalCode": "53-601",
            },
        },
    }
    response = staff_api_client.post_graphql(
        MUTATION_UPDATE_WAREHOUSE,
        variables=variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    content_address = content["data"]["updateWarehouse"]["warehouse"]["address"]
    assert content_address["id"] == address_id
    address.refresh_from_db()
    assert address.street_address_1 == "Teczowa 8"
    assert address.street_address_2 == "Ground floor"


@pytest.mark.parametrize(
    "input_slug, expected_slug, error_message",
    [
        ("test-slug", "test-slug", None),
        ("", "", "Slug value cannot be blank."),
        (None, "", "Slug value cannot be blank."),
    ],
)
def test_update_warehouse_slug(
    staff_api_client,
    warehouse,
    permission_manage_products,
    input_slug,
    expected_slug,
    error_message,
):
    query = MUTATION_UPDATE_WAREHOUSE
    old_slug = warehouse.slug

    assert old_slug != input_slug

    node_id = graphene.Node.to_global_id("Warehouse", warehouse.id)
    variables = {"id": node_id, "input": {"slug": input_slug}}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["updateWarehouse"]
    errors = data["errors"]
    if not error_message:
        assert not errors
        assert data["warehouse"]["slug"] == expected_slug
    else:
        assert errors
        assert errors[0]["field"] == "slug"
        assert errors[0]["code"] == WarehouseErrorCode.REQUIRED.name


def test_update_warehouse_slug_exists(
    staff_api_client, warehouse, permission_manage_products
):
    query = MUTATION_UPDATE_WAREHOUSE
    input_slug = "test-slug"

    second_warehouse = Warehouse.objects.get(pk=warehouse.pk)
    second_warehouse.pk = None
    second_warehouse.slug = input_slug
    second_warehouse.save()

    assert input_slug != warehouse.slug

    node_id = graphene.Node.to_global_id("Warehouse", warehouse.id)
    variables = {"id": node_id, "input": {"slug": input_slug}}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["updateWarehouse"]
    errors = data["errors"]
    assert errors
    assert errors[0]["field"] == "slug"
    assert errors[0]["code"] == WarehouseErrorCode.UNIQUE.name


@pytest.mark.parametrize(
    "input_slug, expected_slug, input_name, expected_name, error_message, error_field",
    [
        ("test-slug", "test-slug", "New name", "New name", None, None),
        (
            "test-slug",
            "test-slug",
            " stripped ",
            "stripped",
            None,
            None,
        ),
        ("", "", "New name", "New name", "Slug value cannot be blank.", "slug"),
        (None, "", "New name", "New name", "Slug value cannot be blank.", "slug"),
        ("test-slug", "", None, None, "This field cannot be blank.", "name"),
        ("test-slug", "", "", None, "This field cannot be blank.", "name"),
        (None, None, None, None, "Slug value cannot be blank.", "slug"),
        ("test-slug", "test-slug", "  ", None, "Name value cannot be blank", "name"),
    ],
)
def test_update_warehouse_slug_and_name(
    staff_api_client,
    warehouse,
    permission_manage_products,
    input_slug,
    expected_slug,
    input_name,
    expected_name,
    error_message,
    error_field,
):
    query = MUTATION_UPDATE_WAREHOUSE

    old_name = warehouse.name
    old_slug = warehouse.slug

    assert input_slug != old_slug
    assert input_name != old_name

    node_id = graphene.Node.to_global_id("Warehouse", warehouse.id)
    variables = {"input": {"slug": input_slug, "name": input_name}, "id": node_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    warehouse.refresh_from_db()
    data = content["data"]["updateWarehouse"]
    errors = data["errors"]
    if not error_message:
        assert data["warehouse"]["name"] == expected_name == warehouse.name
        assert (
            data["warehouse"]["slug"] == input_slug == warehouse.slug == expected_slug
        )
    else:
        assert errors
        assert errors[0]["field"] == error_field
        assert errors[0]["code"] == WarehouseErrorCode.REQUIRED.name


@pytest.mark.parametrize(
    "expected_private, expected_cc_option",
    [
        (private, option)
        for private in (True, False)
        for option in [
            WarehouseClickAndCollectOptionEnum.ALL.name,
            WarehouseClickAndCollectOptionEnum.DISABLED.name,
        ]
    ]
    + [(False, WarehouseClickAndCollectOptionEnum.LOCAL.name)],
)
def test_update_click_and_collect_option(
    staff_api_client,
    warehouse,
    permission_manage_products,
    expected_private,
    expected_cc_option,
):
    query = MUTATION_UPDATE_WAREHOUSE

    assert warehouse.is_private
    assert warehouse.click_and_collect_option == WarehouseClickAndCollectOption.DISABLED

    node_id = graphene.Node.to_global_id("Warehouse", warehouse.id)
    variables = {
        "input": {
            "isPrivate": expected_private,
            "clickAndCollectOption": expected_cc_option,
        },
        "id": node_id,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    warehouse.refresh_from_db()
    data = content["data"]["updateWarehouse"]
    errors = data["errors"]

    assert not errors
    assert data["warehouse"]["isPrivate"] == expected_private == warehouse.is_private
    assert (
        data["warehouse"]["clickAndCollectOption"]
        == expected_cc_option
        == warehouse.click_and_collect_option.upper()
    )


def test_update_click_and_collect_option_invalid_input(
    staff_api_client, warehouse, permission_manage_products
):
    query = MUTATION_UPDATE_WAREHOUSE

    warehouse_is_private = warehouse.is_private
    warehouse_click_and_collect = warehouse.click_and_collect_option
    assert warehouse_is_private
    assert warehouse_click_and_collect == WarehouseClickAndCollectOption.DISABLED

    node_id = graphene.Node.to_global_id("Warehouse", warehouse.id)
    variables = {
        "input": {
            "isPrivate": True,
            "clickAndCollectOption": WarehouseClickAndCollectOptionEnum.LOCAL.name,
        },
        "id": node_id,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    warehouse.refresh_from_db()
    data = content["data"]["updateWarehouse"]
    errors = data["errors"]

    assert len(errors) == 1
    assert (
        errors[0]["message"]
        == "Local warehouse can be toggled only for non-private warehouse stocks"
    )
    assert errors[0]["field"] == "clickAndCollectOption"

    assert warehouse.is_private == warehouse_is_private
    assert warehouse.click_and_collect_option == warehouse_click_and_collect


def test_delete_warehouse_mutation(
    staff_api_client, warehouse, permission_manage_products
):
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)
    assert Warehouse.objects.count() == 1
    response = staff_api_client.post_graphql(
        MUTATION_DELETE_WAREHOUSE,
        variables={"id": warehouse_id},
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    errors = content["data"]["deleteWarehouse"]["errors"]
    assert len(errors) == 0
    assert not Warehouse.objects.exists()


@patch("saleor.plugins.manager.PluginsManager.product_variant_out_of_stock")
def test_delete_warehouse_mutation_with_webhooks(
    product_variant_out_of_stock_webhook,
    staff_api_client,
    warehouse,
    permission_manage_products,
    variant_with_many_stocks,
):
    old_first_stock = Stock.objects.first()
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)
    assert Warehouse.objects.count() == 3
    assert Stock.objects.count() == 3
    response = staff_api_client.post_graphql(
        MUTATION_DELETE_WAREHOUSE,
        variables={"id": warehouse_id},
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    errors = content["data"]["deleteWarehouse"]["errors"]
    assert len(errors) == 0
    assert Warehouse.objects.count() == 2
    assert Stock.objects.count() == 2
    product_variant_out_of_stock_webhook.assert_called_once_with(old_first_stock)


@patch("saleor.plugins.manager.PluginsManager.product_variant_out_of_stock")
def test_delete_warehouse_mutation_with_webhooks_for_many_product_variants(
    product_variant_out_of_stock_webhook,
    staff_api_client,
    warehouse,
    permission_manage_products,
    product_with_two_variants,
):

    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)
    assert Warehouse.objects.count() == 1
    assert Stock.objects.count() == 2
    response = staff_api_client.post_graphql(
        MUTATION_DELETE_WAREHOUSE,
        variables={"id": warehouse_id},
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    errors = content["data"]["deleteWarehouse"]["errors"]
    assert len(errors) == 0
    assert Warehouse.objects.count() == 0
    assert Stock.objects.count() == 0
    assert product_variant_out_of_stock_webhook.call_count == 2


def test_delete_warehouse_deletes_associated_address(
    staff_api_client, warehouse, permission_manage_products
):
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)
    assert Address.objects.count() == 1
    response = staff_api_client.post_graphql(
        MUTATION_DELETE_WAREHOUSE,
        variables={"id": warehouse_id},
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    errors = content["data"]["deleteWarehouse"]["errors"]
    assert len(errors) == 0
    assert not Address.objects.exists()


def test_shipping_zone_can_be_assigned_only_to_one_warehouse(
    staff_api_client, warehouse, permission_manage_products
):
    used_shipping_zone = warehouse.shipping_zones.first()
    used_shipping_zone_id = graphene.Node.to_global_id(
        "ShippingZone", used_shipping_zone.pk
    )

    variables = {
        "input": {
            "name": "Warehouse #q",
            "email": "test@example.com",
            "address": {
                "streetAddress1": "Teczowa 8",
                "city": "Wroclaw",
                "country": "PL",
                "companyName": "Big Company",
                "postalCode": "53-601",
            },
            "shippingZones": [used_shipping_zone_id],
        }
    }

    response = staff_api_client.post_graphql(
        MUTATION_CREATE_WAREHOUSE,
        variables=variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    errors = content["data"]["createWarehouse"]["errors"]
    assert len(errors) == 1
    assert (
        errors[0]["message"] == "Shipping zone can be assigned only to one warehouse."
    )
    used_shipping_zone.refresh_from_db()
    assert used_shipping_zone.warehouses.count() == 1


def test_shipping_zone_assign_to_warehouse(
    staff_api_client,
    warehouse_no_shipping_zone,
    shipping_zone,
    permission_manage_products,
):
    assert not warehouse_no_shipping_zone.shipping_zones.all()
    staff_api_client.user.user_permissions.add(permission_manage_products)
    variables = {
        "id": graphene.Node.to_global_id("Warehouse", warehouse_no_shipping_zone.pk),
        "shippingZoneIds": [
            graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
        ],
    }

    staff_api_client.post_graphql(
        MUTATION_ASSIGN_SHIPPING_ZONE_WAREHOUSE, variables=variables
    )
    warehouse_no_shipping_zone.refresh_from_db()
    shipping_zone.refresh_from_db()
    assert warehouse_no_shipping_zone.shipping_zones.first().pk == shipping_zone.pk


def test_empty_shipping_zone_assign_to_warehouse(
    staff_api_client,
    warehouse_no_shipping_zone,
    shipping_zone,
    permission_manage_products,
):
    assert not warehouse_no_shipping_zone.shipping_zones.all()
    staff_api_client.user.user_permissions.add(permission_manage_products)
    variables = {
        "id": graphene.Node.to_global_id("Warehouse", warehouse_no_shipping_zone.pk),
        "shippingZoneIds": [],
    }

    response = staff_api_client.post_graphql(
        MUTATION_ASSIGN_SHIPPING_ZONE_WAREHOUSE, variables=variables
    )
    content = get_graphql_content(response)
    errors = content["data"]["assignWarehouseShippingZone"]["errors"]
    warehouse_no_shipping_zone.refresh_from_db()
    shipping_zone.refresh_from_db()

    assert not warehouse_no_shipping_zone.shipping_zones.all()
    assert errors[0]["field"] == "shippingZoneId"
    assert errors[0]["code"] == "GRAPHQL_ERROR"


def test_shipping_zone_unassign_from_warehouse(
    staff_api_client, warehouse, shipping_zone, permission_manage_products
):
    assert warehouse.shipping_zones.first().pk == shipping_zone.pk
    staff_api_client.user.user_permissions.add(permission_manage_products)
    variables = {
        "id": graphene.Node.to_global_id("Warehouse", warehouse.pk),
        "shippingZoneIds": [
            graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
        ],
    }

    staff_api_client.post_graphql(
        MUTATION_UNASSIGN_SHIPPING_ZONE_WAREHOUSE, variables=variables
    )
    warehouse.refresh_from_db()
    shipping_zone.refresh_from_db()
    assert not warehouse.shipping_zones.all()
