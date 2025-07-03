import graphene
import pytest
from django.utils.text import slugify

from .....attribute.error_codes import AttributeErrorCode
from .....attribute.utils import associate_attribute_values_to_instance
from ....tests.utils import get_graphql_content

UPDATE_ATTRIBUTE_VALUE_MUTATION = """
mutation AttributeValueUpdate(
        $id: ID!, $input: AttributeValueUpdateInput!) {
    attributeValueUpdate(
    id: $id, input: $input) {
        errors {
            field
            message
            code
        }
        attributeValue {
            name
            slug
            value
            file {
                url
                contentType
            }
        }
        attribute {
            choices(first: 10) {
                edges {
                    node {
                        name
                    }
                }
            }
        }
    }
}
"""


def test_update_attribute_value(
    staff_api_client,
    pink_attribute_value,
    permission_manage_product_types_and_attributes,
):
    # given
    query = UPDATE_ATTRIBUTE_VALUE_MUTATION
    value = pink_attribute_value
    node_id = graphene.Node.to_global_id("AttributeValue", value.id)
    name = "Crimson name"
    variables = {"input": {"name": name}, "id": node_id}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["attributeValueUpdate"]
    value.refresh_from_db()
    assert data["attributeValue"]["name"] == name == value.name
    assert data["attributeValue"]["slug"] == slugify(name)
    assert name in [
        value["node"]["name"] for value in data["attribute"]["choices"]["edges"]
    ]


def test_update_attribute_value_name_not_unique(
    staff_api_client,
    pink_attribute_value,
    permission_manage_product_types_and_attributes,
):
    # given
    query = UPDATE_ATTRIBUTE_VALUE_MUTATION
    value = pink_attribute_value.attribute.values.create(
        name="Example Name", slug="example-name", value="#RED"
    )
    node_id = graphene.Node.to_global_id("AttributeValue", value.id)
    variables = {"input": {"name": pink_attribute_value.name}, "id": node_id}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["attributeValueUpdate"]
    assert not data["errors"]
    assert data["attributeValue"]["slug"] == "pink-2"


def test_update_attribute_value_product_search_document_updated(
    staff_api_client,
    pink_attribute_value,
    permission_manage_product_types_and_attributes,
    product,
):
    # given
    query = UPDATE_ATTRIBUTE_VALUE_MUTATION
    attribute = pink_attribute_value.attribute
    value = pink_attribute_value

    product_type = product.product_type
    product_type.product_attributes.add(attribute)

    associate_attribute_values_to_instance(product, attribute, value)

    node_id = graphene.Node.to_global_id("AttributeValue", value.id)
    name = "Crimson name"
    variables = {"input": {"name": name}, "id": node_id}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["attributeValueUpdate"]
    value.refresh_from_db()
    assert data["attributeValue"]["name"] == name == value.name
    assert data["attributeValue"]["slug"] == slugify(name)
    assert name in [
        value["node"]["name"] for value in data["attribute"]["choices"]["edges"]
    ]

    product.refresh_from_db()
    assert name.lower() in product.search_document


def test_update_attribute_value_product_search_document_updated_variant_attribute(
    staff_api_client,
    pink_attribute_value,
    permission_manage_product_types_and_attributes,
    variant,
):
    # given
    query = UPDATE_ATTRIBUTE_VALUE_MUTATION
    attribute = pink_attribute_value.attribute
    value = pink_attribute_value

    product = variant.product
    product_type = product.product_type
    product_type.variant_attributes.add(attribute)

    associate_attribute_values_to_instance(variant, attribute, value)

    node_id = graphene.Node.to_global_id("AttributeValue", value.id)
    name = "Crimson name"
    variables = {"input": {"name": name}, "id": node_id}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["attributeValueUpdate"]
    value.refresh_from_db()
    assert data["attributeValue"]["name"] == name == value.name
    assert data["attributeValue"]["slug"] == slugify(name)
    assert name in [
        value["node"]["name"] for value in data["attribute"]["choices"]["edges"]
    ]

    product.refresh_from_db()
    assert name.lower() in product.search_document


def test_update_swatch_attribute_value(
    staff_api_client,
    swatch_attribute,
    permission_manage_product_types_and_attributes,
):
    # given
    query = UPDATE_ATTRIBUTE_VALUE_MUTATION
    value = swatch_attribute.values.filter(value__isnull=False).first()
    node_id = graphene.Node.to_global_id("AttributeValue", value.id)
    name = "New name"
    variables = {"input": {"name": name, "value": "", "fileUrl": ""}, "id": node_id}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["attributeValueUpdate"]
    value.refresh_from_db()
    assert data["attributeValue"]["name"] == value.name
    assert data["attributeValue"]["slug"] == value.slug
    assert data["attributeValue"]["value"] == ""
    assert data["attributeValue"]["file"] is None
    assert value.name in [
        value["node"]["name"] for value in data["attribute"]["choices"]["edges"]
    ]


@pytest.mark.parametrize("additional_field", [{"value": ""}, {"value": None}, {}])
def test_update_swatch_attribute_value_clear_value(
    additional_field,
    staff_api_client,
    swatch_attribute,
    permission_manage_product_types_and_attributes,
):
    # given
    query = UPDATE_ATTRIBUTE_VALUE_MUTATION
    value = swatch_attribute.values.filter(value__isnull=False).first()
    node_id = graphene.Node.to_global_id("AttributeValue", value.id)
    file_url = "http://mirumee.com/test_media/test_file.jpeg"
    variables = {"input": {"fileUrl": file_url, **additional_field}, "id": node_id}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["attributeValueUpdate"]
    value.refresh_from_db()
    assert data["attributeValue"]["name"] == value.name
    assert data["attributeValue"]["slug"] == value.slug
    assert data["attributeValue"]["value"] == ""
    assert data["attributeValue"]["file"]["url"] == file_url
    assert value.name in [
        value["node"]["name"] for value in data["attribute"]["choices"]["edges"]
    ]


@pytest.mark.parametrize("additional_field", [{"fileUrl": ""}, {"fileUrl": None}, {}])
def test_update_swatch_attribute_value_clear_file_value(
    additional_field,
    staff_api_client,
    swatch_attribute,
    permission_manage_product_types_and_attributes,
):
    # given
    query = UPDATE_ATTRIBUTE_VALUE_MUTATION
    value = swatch_attribute.values.filter(file_url__isnull=False).first()
    node_id = graphene.Node.to_global_id("AttributeValue", value.id)
    input_value = "#ffffff"
    variables = {"input": {"value": input_value, **additional_field}, "id": node_id}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["attributeValueUpdate"]
    value.refresh_from_db()
    assert data["attributeValue"]["name"] == value.name
    assert data["attributeValue"]["slug"] == value.slug
    assert data["attributeValue"]["value"] == input_value
    assert data["attributeValue"]["file"] is None
    assert value.name in [
        value["node"]["name"] for value in data["attribute"]["choices"]["edges"]
    ]


@pytest.mark.parametrize(
    "field, input_value",
    [
        ("fileUrl", "http://mirumee.com/test_media/test_file.jpeg"),
        ("contentType", "jpeg"),
    ],
)
def test_update_attribute_value_invalid_input_data(
    field,
    input_value,
    staff_api_client,
    pink_attribute_value,
    permission_manage_product_types_and_attributes,
):
    # given
    query = UPDATE_ATTRIBUTE_VALUE_MUTATION
    value = pink_attribute_value
    node_id = graphene.Node.to_global_id("AttributeValue", value.id)
    name = "Crimson name"
    variables = {"input": {"name": name, field: input_value}, "id": node_id}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["attributeValueUpdate"]
    value.refresh_from_db()
    assert not data["attributeValue"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["code"] == AttributeErrorCode.INVALID.name
    assert data["errors"][0]["field"] == field
