from collections import defaultdict
from datetime import date
from typing import TYPE_CHECKING, Dict, List

import graphene
from django.core.exceptions import ValidationError

from ....attribute import AttributeInputType, AttributeType
from ....attribute import models as attribute_models
from ....core.permissions import PagePermissions, PageTypePermissions
from ....core.tracing import traced_atomic_transaction
from ....page import models
from ....page.error_codes import PageErrorCode
from ...attribute.types import AttributeValueInput
from ...attribute.utils import AttributeAssignmentMixin
from ...core.mutations import ModelDeleteMutation, ModelMutation
from ...core.types.common import PageError, SeoInput
from ...core.utils import clean_seo_fields, validate_slug_and_generate_if_needed
from ...utils.validators import check_for_duplicates
from ..types import Page, PageType

if TYPE_CHECKING:
    from ....attribute.models import Attribute


class PageInput(graphene.InputObjectType):
    slug = graphene.String(description="Page internal name.")
    title = graphene.String(description="Page title.")
    content = graphene.JSONString(description="Page content in JSON format.")
    attributes = graphene.List(
        graphene.NonNull(AttributeValueInput), description="List of attributes."
    )
    is_published = graphene.Boolean(
        description="Determines if page is visible in the storefront."
    )
    publication_date = graphene.String(
        description="Publication date. ISO 8601 standard."
    )
    seo = SeoInput(description="Search engine optimization fields.")


class PageCreateInput(PageInput):
    page_type = graphene.ID(
        description="ID of the page type that page belongs to.", required=True
    )


class PageCreate(ModelMutation):
    class Arguments:
        input = PageCreateInput(
            required=True, description="Fields required to create a page."
        )

    class Meta:
        description = "Creates a new page."
        model = models.Page
        object_type = Page
        permissions = (PagePermissions.MANAGE_PAGES,)
        error_type_class = PageError
        error_type_field = "page_errors"

    @classmethod
    def clean_attributes(cls, attributes: dict, page_type: models.PageType):
        attributes_qs = page_type.page_attributes
        attributes = AttributeAssignmentMixin.clean_input(
            attributes, attributes_qs, is_page_attributes=True
        )
        return attributes

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)
        try:
            cleaned_input = validate_slug_and_generate_if_needed(
                instance, "title", cleaned_input
            )
        except ValidationError as error:
            error.code = PageErrorCode.REQUIRED
            raise ValidationError({"slug": error})

        is_published = cleaned_input.get("is_published")
        publication_date = cleaned_input.get("publication_date")
        if is_published and not publication_date:
            cleaned_input["publication_date"] = date.today()

        attributes = cleaned_input.get("attributes")
        page_type = (
            instance.page_type if instance.pk else cleaned_input.get("page_type")
        )
        if attributes and page_type:
            try:
                cleaned_input["attributes"] = cls.clean_attributes(
                    attributes, page_type
                )
            except ValidationError as exc:
                raise ValidationError({"attributes": exc})

        clean_seo_fields(cleaned_input)

        return cleaned_input

    @classmethod
    @traced_atomic_transaction()
    def _save_m2m(cls, info, instance, cleaned_data):
        super()._save_m2m(info, instance, cleaned_data)

        attributes = cleaned_data.get("attributes")
        if attributes:
            AttributeAssignmentMixin.save(instance, attributes)

    @classmethod
    def save(cls, info, instance, cleaned_input):
        super().save(info, instance, cleaned_input)
        info.context.plugins.page_created(instance)


class PageUpdate(PageCreate):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a page to update.")
        input = PageInput(
            required=True, description="Fields required to update a page."
        )

    class Meta:
        description = "Updates an existing page."
        model = models.Page
        object_type = Page
        permissions = (PagePermissions.MANAGE_PAGES,)
        error_type_class = PageError
        error_type_field = "page_errors"

    @classmethod
    def clean_attributes(cls, attributes: dict, page_type: models.PageType):
        attributes_qs = page_type.page_attributes
        attributes = AttributeAssignmentMixin.clean_input(
            attributes, attributes_qs, creation=False, is_page_attributes=True
        )
        return attributes

    @classmethod
    def save(cls, info, instance, cleaned_input):
        super(PageCreate, cls).save(info, instance, cleaned_input)
        info.context.plugins.page_updated(instance)


class PageDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a page to delete.")

    class Meta:
        description = "Deletes a page."
        model = models.Page
        object_type = Page
        permissions = (PagePermissions.MANAGE_PAGES,)
        error_type_class = PageError
        error_type_field = "page_errors"

    @classmethod
    @traced_atomic_transaction()
    def perform_mutation(cls, _root, info, **data):
        page = cls.get_instance(info, **data)
        cls.delete_assigned_attribute_values(page)
        response = super().perform_mutation(_root, info, **data)
        info.context.plugins.page_deleted(page)
        return response

    @staticmethod
    def delete_assigned_attribute_values(instance):
        attribute_models.AttributeValue.objects.filter(
            pageassignments__page_id=instance.id,
            attribute__input_type__in=AttributeInputType.TYPES_WITH_UNIQUE_VALUES,
        ).delete()


class PageTypeCreateInput(graphene.InputObjectType):
    name = graphene.String(description="Name of the page type.")
    slug = graphene.String(description="Page type slug.")
    add_attributes = graphene.List(
        graphene.NonNull(graphene.ID),
        description="List of attribute IDs to be assigned to the page type.",
    )


class PageTypeUpdateInput(PageTypeCreateInput):
    remove_attributes = graphene.List(
        graphene.NonNull(graphene.ID),
        description="List of attribute IDs to be assigned to the page type.",
    )


class PageTypeMixin:
    @classmethod
    def validate_attributes(
        cls,
        errors: Dict[str, List[ValidationError]],
        attributes: List["Attribute"],
        field: str,
    ):
        """All attributes must be page type attribute.

        Raise an error if any of the attributes are not page attribute.
        """
        if attributes:
            not_valid_attributes = [
                graphene.Node.to_global_id("Attribute", attr.pk)
                for attr in attributes
                if attr.type != AttributeType.PAGE_TYPE
            ]
            if not_valid_attributes:
                error = ValidationError(
                    "Only page type attributes allowed.",
                    code=PageErrorCode.INVALID.value,
                    params={"attributes": not_valid_attributes},
                )
                errors[field].append(error)


class PageTypeCreate(PageTypeMixin, ModelMutation):
    class Arguments:
        input = PageTypeCreateInput(
            description="Fields required to create page type.", required=True
        )

    class Meta:
        description = "Create a new page type."
        model = models.PageType
        object_type = PageType
        permissions = (PageTypePermissions.MANAGE_PAGE_TYPES_AND_ATTRIBUTES,)
        error_type_class = PageError
        error_type_field = "page_errors"

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)
        errors = defaultdict(list)
        try:
            cleaned_input = validate_slug_and_generate_if_needed(
                instance, "name", cleaned_input
            )
        except ValidationError as error:
            error.code = PageErrorCode.REQUIRED.value
            errors["slug"].append(error)

        cls.validate_attributes(
            errors, cleaned_input.get("add_attributes"), "add_attributes"
        )

        if errors:
            raise ValidationError(errors)

        return cleaned_input

    @classmethod
    def _save_m2m(cls, info, instance, cleaned_data):
        super()._save_m2m(info, instance, cleaned_data)
        attributes = cleaned_data.get("add_attributes")
        if attributes is not None:
            instance.page_attributes.add(*attributes)


class PageTypeUpdate(PageTypeMixin, ModelMutation):
    class Arguments:
        id = graphene.ID(description="ID of the page type to update.")
        input = PageTypeUpdateInput(
            description="Fields required to update page type.", required=True
        )

    class Meta:
        description = "Update page type."
        model = models.PageType
        object_type = PageType
        permissions = (PageTypePermissions.MANAGE_PAGE_TYPES_AND_ATTRIBUTES,)
        error_type_class = PageError
        error_type_field = "page_errors"

    @classmethod
    def clean_input(cls, info, instance, data):
        errors = defaultdict(list)
        error = check_for_duplicates(
            data, "add_attributes", "remove_attributes", "attributes"
        )
        if error:
            error.code = PageErrorCode.DUPLICATED_INPUT_ITEM.value
            errors["attributes"].append(error)

        cleaned_input = super().clean_input(info, instance, data)
        try:
            cleaned_input = validate_slug_and_generate_if_needed(
                instance, "name", cleaned_input
            )
        except ValidationError as error:
            error.code = PageErrorCode.REQUIRED
            errors["slug"].append(error)

        add_attributes = cleaned_input.get("add_attributes")
        cls.validate_attributes(errors, add_attributes, "add_attributes")

        remove_attributes = cleaned_input.get("remove_attributes")
        cls.validate_attributes(errors, remove_attributes, "remove_attributes")

        if errors:
            raise ValidationError(errors)

        return cleaned_input

    @classmethod
    def _save_m2m(cls, info, instance, cleaned_data):
        super()._save_m2m(info, instance, cleaned_data)
        remove_attributes = cleaned_data.get("remove_attributes")
        add_attributes = cleaned_data.get("add_attributes")
        if remove_attributes is not None:
            instance.page_attributes.remove(*remove_attributes)
        if add_attributes is not None:
            instance.page_attributes.add(*add_attributes)


class PageTypeDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of the page type to delete.")

    class Meta:
        description = "Delete a page type."
        model = models.PageType
        object_type = PageType
        permissions = (PageTypePermissions.MANAGE_PAGE_TYPES_AND_ATTRIBUTES,)
        error_type_class = PageError
        error_type_field = "page_errors"

    @classmethod
    @traced_atomic_transaction()
    def perform_mutation(cls, _root, info, **data):
        node_id = data.get("id")
        page_type_pk = cls.get_global_id_or_error(
            node_id, only_type=PageType, field="pk"
        )
        cls.delete_assigned_attribute_values(page_type_pk)
        return super().perform_mutation(_root, info, **data)

    @staticmethod
    def delete_assigned_attribute_values(instance_pk):
        attribute_models.AttributeValue.objects.filter(
            attribute__input_type__in=AttributeInputType.TYPES_WITH_UNIQUE_VALUES,
            pageassignments__assignment__page_type_id=instance_pk,
        ).delete()
