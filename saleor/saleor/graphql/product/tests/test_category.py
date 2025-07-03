import os
from unittest.mock import Mock, patch

import graphene
import pytest
from django.utils.text import slugify
from graphql_relay import to_global_id

from ....product.error_codes import ProductErrorCode
from ....product.models import Category, Product, ProductChannelListing
from ....product.tests.utils import create_image, create_pdf_file_with_image_ext
from ....tests.utils import dummy_editorjs
from ...tests.utils import (
    get_graphql_content,
    get_graphql_content_from_response,
    get_multipart_request_body,
)

QUERY_CATEGORY = """
    query ($id: ID, $slug: String, $channel: String){
        category(
            id: $id,
            slug: $slug,
        ) {
            id
            name
            ancestors(first: 20) {
                edges {
                    node {
                        name
                    }
                }
            }
            children(first: 20) {
                edges {
                    node {
                        name
                    }
                }
            }
            products(first: 10, channel: $channel) {
                edges {
                    node {
                        id
                    }
                }
            }
        }
    }
    """


def test_category_query_by_id(user_api_client, product, channel_USD):
    category = Category.objects.first()
    variables = {
        "id": graphene.Node.to_global_id("Category", category.pk),
        "channel": channel_USD.slug,
    }

    response = user_api_client.post_graphql(QUERY_CATEGORY, variables=variables)
    content = get_graphql_content(response)
    category_data = content["data"]["category"]
    assert category_data is not None
    assert category_data["name"] == category.name
    assert len(category_data["ancestors"]["edges"]) == category.get_ancestors().count()
    assert len(category_data["children"]["edges"]) == category.get_children().count()


def test_category_query_invalid_id(user_api_client, product, channel_USD):
    category_id = "'"
    variables = {
        "id": category_id,
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(QUERY_CATEGORY, variables)
    content = get_graphql_content_from_response(response)
    assert len(content["errors"]) == 1
    assert content["errors"][0]["message"] == f"Couldn't resolve id: {category_id}."
    assert content["data"]["category"] is None


def test_category_query_object_with_given_id_does_not_exist(
    user_api_client, product, channel_USD
):
    category_id = graphene.Node.to_global_id("Category", -1)
    variables = {
        "id": category_id,
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(QUERY_CATEGORY, variables)
    content = get_graphql_content(response)
    assert content["data"]["category"] is None


def test_category_query_object_with_invalid_object_type(
    user_api_client, product, channel_USD
):
    category = Category.objects.first()
    category_id = graphene.Node.to_global_id("Product", category.pk)
    variables = {
        "id": category_id,
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(QUERY_CATEGORY, variables)
    content = get_graphql_content(response)
    assert content["data"]["category"] is None


def test_category_query_description(user_api_client, product, channel_USD):
    category = Category.objects.first()
    description = dummy_editorjs("Test description.", json_format=True)
    category.description = dummy_editorjs("Test description.")
    category.save()
    variables = {
        "id": graphene.Node.to_global_id("Category", category.pk),
        "channel": channel_USD.slug,
    }
    query = """
    query ($id: ID, $slug: String){
        category(
            id: $id,
            slug: $slug,
        ) {
            id
            name
            description
            descriptionJson
        }
    }
    """
    response = user_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)
    category_data = content["data"]["category"]
    assert category_data["description"] == description
    assert category_data["descriptionJson"] == description


def test_category_query_without_description(user_api_client, product, channel_USD):
    category = Category.objects.first()
    category.save()
    variables = {
        "id": graphene.Node.to_global_id("Category", category.pk),
        "channel": channel_USD.slug,
    }
    query = """
    query ($id: ID, $slug: String){
        category(
            id: $id,
            slug: $slug,
        ) {
            id
            name
            description
            descriptionJson
        }
    }
    """
    response = user_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)
    category_data = content["data"]["category"]
    assert category_data["description"] is None
    assert category_data["descriptionJson"] == "{}"


def test_category_query_by_slug(user_api_client, product, channel_USD):
    category = Category.objects.first()
    variables = {"slug": category.slug, "channel": channel_USD.slug}
    response = user_api_client.post_graphql(QUERY_CATEGORY, variables=variables)
    content = get_graphql_content(response)
    category_data = content["data"]["category"]
    assert category_data is not None
    assert category_data["name"] == category.name
    assert len(category_data["ancestors"]["edges"]) == category.get_ancestors().count()
    assert len(category_data["children"]["edges"]) == category.get_children().count()


def test_category_query_error_when_id_and_slug_provided(
    user_api_client, product, graphql_log_handler, channel_USD
):
    category = Category.objects.first()
    variables = {
        "id": graphene.Node.to_global_id("Category", category.pk),
        "slug": category.slug,
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(QUERY_CATEGORY, variables=variables)
    assert graphql_log_handler.messages == [
        "saleor.graphql.errors.handled[INFO].GraphQLError"
    ]
    content = get_graphql_content(response, ignore_errors=True)
    assert len(content["errors"]) == 1


def test_category_query_error_when_no_param(
    user_api_client, product, graphql_log_handler
):
    variables = {}
    response = user_api_client.post_graphql(QUERY_CATEGORY, variables=variables)
    assert graphql_log_handler.messages == [
        "saleor.graphql.errors.handled[INFO].GraphQLError"
    ]
    content = get_graphql_content(response, ignore_errors=True)
    assert len(content["errors"]) == 1


def test_query_category_product_only_visible_in_listings_as_customer(
    user_api_client, product_list, channel_USD
):
    # given
    category = Category.objects.first()

    product_list[0].channel_listings.all().update(visible_in_listings=False)

    product_count = Product.objects.count()

    variables = {
        "id": graphene.Node.to_global_id("Category", category.pk),
        "channel": channel_USD.slug,
    }

    # when
    response = user_api_client.post_graphql(QUERY_CATEGORY, variables=variables)

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert len(content["data"]["category"]["products"]["edges"]) == product_count - 1


def test_query_category_product_visible_in_listings_as_staff_without_manage_products(
    staff_api_client, product_list, channel_USD
):
    # given
    category = Category.objects.first()

    product_list[0].channel_listings.all().update(visible_in_listings=False)

    product_count = Product.objects.count()

    variables = {
        "id": graphene.Node.to_global_id("Category", category.pk),
        "channel": channel_USD.slug,
    }

    # when
    response = staff_api_client.post_graphql(QUERY_CATEGORY, variables=variables)

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert (
        len(content["data"]["category"]["products"]["edges"]) == product_count - 1
    )  # invisible doesn't count


def test_query_category_product_only_visible_in_listings_as_staff_with_perm(
    staff_api_client, product_list, permission_manage_products
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)

    category = Category.objects.first()

    product_list[0].channel_listings.all().update(visible_in_listings=False)

    product_count = Product.objects.count()

    variables = {"id": graphene.Node.to_global_id("Category", category.pk)}

    # when
    response = staff_api_client.post_graphql(QUERY_CATEGORY, variables=variables)

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert len(content["data"]["category"]["products"]["edges"]) == product_count


def test_query_category_product_only_visible_in_listings_as_app_without_manage_products(
    app_api_client, product_list, channel_USD
):
    # given
    category = Category.objects.first()

    product_list[0].channel_listings.all().update(visible_in_listings=False)

    product_count = Product.objects.count()

    variables = {
        "id": graphene.Node.to_global_id("Category", category.pk),
        "channel": channel_USD.slug,
    }

    # when
    response = app_api_client.post_graphql(QUERY_CATEGORY, variables=variables)

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert (
        len(content["data"]["category"]["products"]["edges"]) == product_count - 1
    )  # invisible doesn't count


def test_query_category_product_only_visible_in_listings_as_app_with_perm(
    app_api_client, product_list, permission_manage_products
):
    # given
    app_api_client.app.permissions.add(permission_manage_products)

    category = Category.objects.first()

    product_list[0].channel_listings.all().update(visible_in_listings=False)

    product_count = Product.objects.count()

    variables = {"id": graphene.Node.to_global_id("Category", category.pk)}

    # when
    response = app_api_client.post_graphql(QUERY_CATEGORY, variables=variables)

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert len(content["data"]["category"]["products"]["edges"]) == product_count


CATEGORY_CREATE_MUTATION = """
        mutation(
                $name: String, $slug: String,
                $description: JSONString, $backgroundImage: Upload,
                $backgroundImageAlt: String, $parentId: ID) {
            categoryCreate(
                input: {
                    name: $name
                    slug: $slug
                    description: $description
                    backgroundImage: $backgroundImage
                    backgroundImageAlt: $backgroundImageAlt
                },
                parent: $parentId
            ) {
                category {
                    id
                    name
                    slug
                    description
                    parent {
                        name
                        id
                    }
                    backgroundImage{
                        alt
                    }
                }
                errors {
                    field
                    code
                    message
                }
            }
        }
    """


def test_category_create_mutation(
    monkeypatch, staff_api_client, permission_manage_products, media_root
):
    query = CATEGORY_CREATE_MUTATION

    mock_create_thumbnails = Mock(return_value=None)
    monkeypatch.setattr(
        (
            "saleor.product.thumbnails."
            "create_category_background_image_thumbnails.delay"
        ),
        mock_create_thumbnails,
    )

    category_name = "Test category"
    description = "description"
    category_slug = slugify(category_name)
    category_description = dummy_editorjs(description, True)
    image_file, image_name = create_image()
    image_alt = "Alt text for an image."

    # test creating root category
    variables = {
        "name": category_name,
        "description": category_description,
        "backgroundImage": image_name,
        "backgroundImageAlt": image_alt,
        "slug": category_slug,
    }
    body = get_multipart_request_body(query, variables, image_file, image_name)
    response = staff_api_client.post_multipart(
        body, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["categoryCreate"]
    assert data["errors"] == []
    assert data["category"]["name"] == category_name
    assert data["category"]["description"] == category_description
    assert not data["category"]["parent"]
    category = Category.objects.get(name=category_name)
    assert category.description_plaintext == description
    assert category.background_image.file
    img_name, format = os.path.splitext(image_file._name)
    file_name = category.background_image.name
    assert file_name != image_file._name
    assert file_name.startswith(f"category-backgrounds/{img_name}")
    assert file_name.endswith(format)
    mock_create_thumbnails.assert_called_once_with(category.pk)
    assert data["category"]["backgroundImage"]["alt"] == image_alt

    # test creating subcategory
    parent_id = data["category"]["id"]
    variables = {
        "name": category_name,
        "description": category_description,
        "parentId": parent_id,
        "slug": f"{category_slug}-2",
    }
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["categoryCreate"]
    assert data["errors"] == []
    assert data["category"]["parent"]["id"] == parent_id


@pytest.mark.parametrize(
    "input_slug, expected_slug",
    (
        ("test-slug", "test-slug"),
        (None, "test-category"),
        ("", "test-category"),
        ("わたし-わ-にっぽん-です", "わたし-わ-にっぽん-です"),
    ),
)
def test_create_category_with_given_slug(
    staff_api_client, permission_manage_products, input_slug, expected_slug
):
    query = CATEGORY_CREATE_MUTATION
    name = "Test category"
    variables = {"name": name, "slug": input_slug}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["categoryCreate"]
    assert not data["errors"]
    assert data["category"]["slug"] == expected_slug


def test_create_category_name_with_unicode(
    staff_api_client, permission_manage_products
):
    query = CATEGORY_CREATE_MUTATION
    name = "わたし-わ にっぽん です"
    variables = {"name": name}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["categoryCreate"]
    assert not data["errors"]
    assert data["category"]["name"] == name
    assert data["category"]["slug"] == "わたし-わ-にっぽん-です"


def test_category_create_mutation_without_background_image(
    monkeypatch, staff_api_client, permission_manage_products
):
    query = CATEGORY_CREATE_MUTATION
    description = dummy_editorjs("description", True)

    mock_create_thumbnails = Mock(return_value=None)
    monkeypatch.setattr(
        (
            "saleor.product.thumbnails."
            "create_category_background_image_thumbnails.delay"
        ),
        mock_create_thumbnails,
    )

    # test creating root category
    category_name = "Test category"
    variables = {
        "name": category_name,
        "description": description,
        "slug": slugify(category_name),
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["categoryCreate"]
    assert data["errors"] == []
    assert mock_create_thumbnails.call_count == 0


MUTATION_CATEGORY_UPDATE_MUTATION = """
    mutation($id: ID!, $name: String, $slug: String,
            $backgroundImage: Upload, $backgroundImageAlt: String,
            $description: JSONString) {

        categoryUpdate(
            id: $id
            input: {
                name: $name
                description: $description
                backgroundImage: $backgroundImage
                backgroundImageAlt: $backgroundImageAlt
                slug: $slug
            }
        ) {
            category {
                id
                name
                description
                parent {
                    id
                }
                backgroundImage{
                    alt
                }
            }
            errors {
                field
                message
            }
        }
    }
    """


def test_category_update_mutation(
    monkeypatch, staff_api_client, category, permission_manage_products, media_root
):
    mock_create_thumbnails = Mock(return_value=None)
    monkeypatch.setattr(
        (
            "saleor.product.thumbnails."
            "create_category_background_image_thumbnails.delay"
        ),
        mock_create_thumbnails,
    )

    # create child category and test that the update mutation won't change
    # it's parent
    child_category = category.children.create(name="child")

    category_name = "Updated name"
    description = "description"
    category_slug = slugify(category_name)
    category_description = dummy_editorjs(description, True)

    image_file, image_name = create_image()
    image_alt = "Alt text for an image."

    category_id = graphene.Node.to_global_id("Category", child_category.pk)
    variables = {
        "name": category_name,
        "description": category_description,
        "backgroundImage": image_name,
        "backgroundImageAlt": image_alt,
        "id": category_id,
        "slug": category_slug,
    }
    body = get_multipart_request_body(
        MUTATION_CATEGORY_UPDATE_MUTATION, variables, image_file, image_name
    )
    response = staff_api_client.post_multipart(
        body, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["categoryUpdate"]
    assert data["errors"] == []
    assert data["category"]["id"] == category_id
    assert data["category"]["name"] == category_name
    assert data["category"]["description"] == category_description

    parent_id = graphene.Node.to_global_id("Category", category.pk)
    assert data["category"]["parent"]["id"] == parent_id
    category = Category.objects.get(name=category_name)
    assert category.description_plaintext == description
    assert category.background_image.file
    mock_create_thumbnails.assert_called_once_with(category.pk)
    assert data["category"]["backgroundImage"]["alt"] == image_alt


def test_category_update_mutation_invalid_background_image(
    staff_api_client, category, permission_manage_products
):
    image_file, image_name = create_pdf_file_with_image_ext()
    image_alt = "Alt text for an image."
    variables = {
        "name": "new-name",
        "slug": "new-slug",
        "id": to_global_id("Category", category.id),
        "backgroundImage": image_name,
        "backgroundImageAlt": image_alt,
        "isPublished": True,
    }
    body = get_multipart_request_body(
        MUTATION_CATEGORY_UPDATE_MUTATION, variables, image_file, image_name
    )
    response = staff_api_client.post_multipart(
        body, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["categoryUpdate"]
    assert data["errors"][0]["field"] == "backgroundImage"
    assert data["errors"][0]["message"] == "Invalid file type."


def test_category_update_mutation_without_background_image(
    monkeypatch, staff_api_client, category, permission_manage_products
):
    query = """
        mutation($id: ID!, $name: String, $slug: String, $description: JSONString) {
            categoryUpdate(
                id: $id
                input: {
                    name: $name
                    description: $description
                    slug: $slug
                }
            ) {
                errors {
                    field
                    message
                }
            }
        }
    """

    mock_create_thumbnails = Mock(return_value=None)
    monkeypatch.setattr(
        (
            "saleor.product.thumbnails."
            "create_category_background_image_thumbnails.delay"
        ),
        mock_create_thumbnails,
    )

    category_name = "Updated name"
    variables = {
        "id": graphene.Node.to_global_id(
            "Category", category.children.create(name="child").pk
        ),
        "name": category_name,
        "description": dummy_editorjs("description", True),
        "slug": slugify(category_name),
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    content = get_graphql_content(response)
    data = content["data"]["categoryUpdate"]
    assert data["errors"] == []
    assert mock_create_thumbnails.call_count == 0


UPDATE_CATEGORY_SLUG_MUTATION = """
    mutation($id: ID!, $slug: String) {
        categoryUpdate(
            id: $id
            input: {
                slug: $slug
            }
        ) {
            category{
                name
                slug
            }
            errors {
                field
                message
                code
            }
        }
    }
"""


@pytest.mark.parametrize(
    "input_slug, expected_slug, error_message",
    [
        ("test-slug", "test-slug", None),
        ("", "", "Slug value cannot be blank."),
        (None, "", "Slug value cannot be blank."),
    ],
)
def test_update_category_slug(
    staff_api_client,
    category,
    permission_manage_products,
    input_slug,
    expected_slug,
    error_message,
):
    query = UPDATE_CATEGORY_SLUG_MUTATION
    old_slug = category.slug

    assert old_slug != input_slug

    node_id = graphene.Node.to_global_id("Category", category.id)
    variables = {"slug": input_slug, "id": node_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["categoryUpdate"]
    errors = data["errors"]
    if not error_message:
        assert not errors
        assert data["category"]["slug"] == expected_slug
    else:
        assert errors
        assert errors[0]["field"] == "slug"
        assert errors[0]["code"] == ProductErrorCode.REQUIRED.name


def test_update_category_slug_exists(
    staff_api_client, category, permission_manage_products
):
    query = UPDATE_CATEGORY_SLUG_MUTATION
    input_slug = "test-slug"

    second_category = Category.objects.get(pk=category.pk)
    second_category.pk = None
    second_category.slug = input_slug
    second_category.save()

    assert input_slug != category.slug

    node_id = graphene.Node.to_global_id("Category", category.id)
    variables = {"slug": input_slug, "id": node_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["categoryUpdate"]
    errors = data["errors"]
    assert errors
    assert errors[0]["field"] == "slug"
    assert errors[0]["code"] == ProductErrorCode.UNIQUE.name


@pytest.mark.parametrize(
    "input_slug, expected_slug, input_name, error_message, error_field",
    [
        ("test-slug", "test-slug", "New name", None, None),
        ("", "", "New name", "Slug value cannot be blank.", "slug"),
        (None, "", "New name", "Slug value cannot be blank.", "slug"),
        ("test-slug", "", None, "This field cannot be blank.", "name"),
        ("test-slug", "", "", "This field cannot be blank.", "name"),
        (None, None, None, "Slug value cannot be blank.", "slug"),
    ],
)
def test_update_category_slug_and_name(
    staff_api_client,
    category,
    permission_manage_products,
    input_slug,
    expected_slug,
    input_name,
    error_message,
    error_field,
):
    query = """
            mutation($id: ID!, $name: String, $slug: String) {
            categoryUpdate(
                id: $id
                input: {
                    name: $name
                    slug: $slug
                }
            ) {
                category{
                    name
                    slug
                }
                errors {
                    field
                    message
                    code
                }
            }
        }
    """

    old_name = category.name
    old_slug = category.slug

    assert input_slug != old_slug
    assert input_name != old_name

    node_id = graphene.Node.to_global_id("Category", category.id)
    variables = {"slug": input_slug, "name": input_name, "id": node_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    category.refresh_from_db()
    data = content["data"]["categoryUpdate"]
    errors = data["errors"]
    if not error_message:
        assert data["category"]["name"] == input_name == category.name
        assert data["category"]["slug"] == input_slug == category.slug
    else:
        assert errors
        assert errors[0]["field"] == error_field
        assert errors[0]["code"] == ProductErrorCode.REQUIRED.name


MUTATION_CATEGORY_DELETE = """
    mutation($id: ID!) {
        categoryDelete(id: $id) {
            category {
                name
            }
            errors {
                field
                message
            }
        }
    }
"""


@patch("saleor.product.signals.delete_versatile_image")
def test_category_delete_mutation(
    delete_versatile_image_mock,
    staff_api_client,
    category,
    permission_manage_products,
):
    variables = {"id": graphene.Node.to_global_id("Category", category.id)}
    response = staff_api_client.post_graphql(
        MUTATION_CATEGORY_DELETE, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["categoryDelete"]
    assert data["category"]["name"] == category.name
    with pytest.raises(category._meta.model.DoesNotExist):
        category.refresh_from_db()

    delete_versatile_image_mock.assert_not_called()


@patch("saleor.product.signals.delete_versatile_image")
def test_delete_category_with_background_image(
    delete_versatile_image_mock,
    staff_api_client,
    category_with_image,
    permission_manage_products,
    media_root,
):
    """Ensure deleting category deletes background image from storage."""
    category = category_with_image
    variables = {"id": graphene.Node.to_global_id("Category", category.id)}
    response = staff_api_client.post_graphql(
        MUTATION_CATEGORY_DELETE, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["categoryDelete"]
    assert data["category"]["name"] == category.name
    with pytest.raises(category._meta.model.DoesNotExist):
        category.refresh_from_db()
    delete_versatile_image_mock.assert_called_once_with(category.background_image)


@patch("saleor.product.utils.update_products_discounted_prices_task")
def test_category_delete_mutation_for_categories_tree(
    mock_update_products_discounted_prices_task,
    staff_api_client,
    categories_tree_with_published_products,
    permission_manage_products,
):
    parent = categories_tree_with_published_products
    parent_product = parent.products.first()
    child_product = parent.children.first().products.first()

    product_list = [child_product, parent_product]

    variables = {"id": graphene.Node.to_global_id("Category", parent.id)}
    response = staff_api_client.post_graphql(
        MUTATION_CATEGORY_DELETE, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["categoryDelete"]
    assert data["category"]["name"] == parent.name
    with pytest.raises(parent._meta.model.DoesNotExist):
        parent.refresh_from_db()

    mock_update_products_discounted_prices_task.delay.assert_called_once()
    (
        _call_args,
        call_kwargs,
    ) = mock_update_products_discounted_prices_task.delay.call_args
    assert set(call_kwargs["product_ids"]) == set(p.pk for p in product_list)

    product_channel_listings = ProductChannelListing.objects.filter(
        product__in=product_list
    )
    for product_channel_listing in product_channel_listings:
        assert product_channel_listing.is_published is False
        assert not product_channel_listing.publication_date
    assert product_channel_listings.count() == 4


@patch("saleor.product.utils.update_products_discounted_prices_task")
def test_category_delete_mutation_for_children_from_categories_tree(
    mock_update_products_discounted_prices_task,
    staff_api_client,
    categories_tree_with_published_products,
    permission_manage_products,
):
    parent = categories_tree_with_published_products
    child = parent.children.first()
    parent_product = parent.products.first()
    child_product = child.products.first()

    variables = {"id": graphene.Node.to_global_id("Category", child.id)}
    response = staff_api_client.post_graphql(
        MUTATION_CATEGORY_DELETE, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["categoryDelete"]
    assert data["category"]["name"] == child.name
    with pytest.raises(child._meta.model.DoesNotExist):
        child.refresh_from_db()

    mock_update_products_discounted_prices_task.delay.assert_called_once_with(
        product_ids=[child_product.pk]
    )

    parent_product.refresh_from_db()
    assert parent_product.category
    product_channel_listings = ProductChannelListing.objects.filter(
        product=parent_product
    )
    for product_channel_listing in product_channel_listings:
        assert product_channel_listing.is_published is True
        assert product_channel_listing.publication_date

    child_product.refresh_from_db()
    assert not child_product.category
    product_channel_listings = ProductChannelListing.objects.filter(
        product=child_product
    )
    for product_channel_listing in product_channel_listings:
        assert product_channel_listing.is_published is False
        assert not product_channel_listing.publication_date


LEVELED_CATEGORIES_QUERY = """
    query leveled_categories($level: Int) {
        categories(level: $level, first: 20) {
            edges {
                node {
                    name
                    parent {
                        name
                    }
                }
            }
        }
    }
    """


def test_category_level(user_api_client, category):
    query = LEVELED_CATEGORIES_QUERY
    child = Category.objects.create(name="child", slug="chi-ld", parent=category)
    variables = {"level": 0}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    category_data = content["data"]["categories"]["edges"][0]["node"]
    assert category_data["name"] == category.name
    assert category_data["parent"] is None

    variables = {"level": 1}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    category_data = content["data"]["categories"]["edges"][0]["node"]
    assert category_data["name"] == child.name
    assert category_data["parent"]["name"] == category.name


NOT_EXISTS_IDS_CATEGORIES_QUERY = """
    query ($filter: CategoryFilterInput!) {
        categories(first: 5, filter: $filter) {
            edges {
                node {
                    id
                    name
                }
            }
        }
    }
"""


def test_categories_query_ids_not_exists(user_api_client, category):
    query = NOT_EXISTS_IDS_CATEGORIES_QUERY
    variables = {"filter": {"ids": ["W3KATGDn3fq3ZH4=", "zH9pYmz7yWD3Hy8="]}}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response, ignore_errors=True)
    message_error = '{"ids": [{"message": "Invalid ID specified.", "code": ""}]}'
    assert len(content["errors"]) == 1
    assert content["errors"][0]["message"] == message_error
    assert content["data"]["categories"] is None


FETCH_CATEGORY_QUERY = """
    query fetchCategory($id: ID!){
        category(id: $id) {
            name
            backgroundImage(size: 120) {
            url
            alt
            }
        }
    }
    """


def test_category_image_query(user_api_client, non_default_category, media_root):
    alt_text = "Alt text for an image."
    category = non_default_category
    image_file, image_name = create_image()
    category.background_image = image_file
    category.background_image_alt = alt_text
    category.save()
    category_id = graphene.Node.to_global_id("Category", category.pk)
    variables = {"id": category_id}
    response = user_api_client.post_graphql(FETCH_CATEGORY_QUERY, variables)
    content = get_graphql_content(response)
    data = content["data"]["category"]
    thumbnail_url = category.background_image.thumbnail["120x120"].url
    assert thumbnail_url in data["backgroundImage"]["url"]
    assert data["backgroundImage"]["alt"] == alt_text


def test_category_image_query_without_associated_file(
    user_api_client, non_default_category
):
    category = non_default_category
    category_id = graphene.Node.to_global_id("Category", category.pk)
    variables = {"id": category_id}
    response = user_api_client.post_graphql(FETCH_CATEGORY_QUERY, variables)
    content = get_graphql_content(response)
    data = content["data"]["category"]
    assert data["name"] == category.name
    assert data["backgroundImage"] is None


def test_update_category_mutation_remove_background_image(
    staff_api_client, category_with_image, permission_manage_products
):
    query = """
        mutation updateCategory($id: ID!, $backgroundImage: Upload) {
            categoryUpdate(
                id: $id, input: {
                    backgroundImage: $backgroundImage
                }
            ) {
                category {
                    backgroundImage{
                        url
                    }
                }
                errors {
                    field
                    message
                }
            }
        }
    """
    assert category_with_image.background_image
    variables = {
        "id": to_global_id("Category", category_with_image.id),
        "backgroundImage": None,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["categoryUpdate"]["category"]
    assert not data["backgroundImage"]
    category_with_image.refresh_from_db()
    assert not category_with_image.background_image


def test_query_category_for_federation(api_client, non_default_category):
    category_id = graphene.Node.to_global_id("Category", non_default_category.pk)
    variables = {
        "representations": [
            {
                "__typename": "Category",
                "id": category_id,
            },
        ],
    }
    query = """
      query GetCategoryInFederation($representations: [_Any]) {
        _entities(representations: $representations) {
          __typename
          ... on Category {
            id
            name
          }
        }
      }
    """

    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content["data"]["_entities"] == [
        {
            "__typename": "Category",
            "id": category_id,
            "name": non_default_category.name,
        }
    ]
