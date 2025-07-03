from datetime import date, datetime
from unittest import mock

import graphene
import pytest
import pytz
from django.utils import timezone
from django.utils.text import slugify
from freezegun import freeze_time

from ....attribute.models import AttributeValue
from ....attribute.utils import associate_attribute_values_to_instance
from ....page.error_codes import PageErrorCode
from ....page.models import Page, PageType
from ....tests.utils import dummy_editorjs
from ....webhook.event_types import WebhookEventAsyncType
from ....webhook.payloads import generate_page_payload
from ...tests.utils import get_graphql_content, get_graphql_content_from_response

PAGE_QUERY = """
    query PageQuery($id: ID, $slug: String) {
        page(id: $id, slug: $slug) {
            id
            title
            slug
            pageType {
                id
            }
            content
            contentJson
            attributes {
                attribute {
                    slug
                }
                values {
                    id
                    slug
                }
            }
        }
    }
"""


def test_query_published_page(user_api_client, page):
    page.is_published = True
    page.save()

    page_type = page.page_type

    assert page.attributes.count() == 1
    page_attr_assigned = page.attributes.first()
    page_attr = page_attr_assigned.attribute

    assert page_attr_assigned.values.count() == 1
    page_attr_value = page_attr_assigned.values.first()

    # query by ID
    variables = {"id": graphene.Node.to_global_id("Page", page.id)}
    response = user_api_client.post_graphql(PAGE_QUERY, variables)
    content = get_graphql_content(response)
    page_data = content["data"]["page"]
    assert (
        page_data["content"]
        == page_data["contentJson"]
        == dummy_editorjs("Test content.", True)
    )
    assert page_data["title"] == page.title
    assert page_data["slug"] == page.slug
    assert page_data["pageType"]["id"] == graphene.Node.to_global_id(
        "PageType", page.page_type.pk
    )

    expected_attributes = []
    for attr in page_type.page_attributes.all():
        values = (
            [
                {
                    "slug": page_attr_value.slug,
                    "id": graphene.Node.to_global_id(
                        "AttributeValue", page_attr_value.pk
                    ),
                }
            ]
            if attr.slug == page_attr.slug
            else []
        )
        expected_attributes.append({"attribute": {"slug": attr.slug}, "values": values})

    for attr_data in page_data["attributes"]:
        assert attr_data in expected_attributes

    # query by slug
    variables = {"slug": page.slug}
    response = user_api_client.post_graphql(PAGE_QUERY, variables)
    content = get_graphql_content(response)
    assert content["data"]["page"]["id"] == graphene.Node.to_global_id("Page", page.id)


def test_customer_query_unpublished_page(user_api_client, page):
    page.is_published = False
    page.save()

    # query by ID
    variables = {"id": graphene.Node.to_global_id("Page", page.id)}
    response = user_api_client.post_graphql(PAGE_QUERY, variables)
    content = get_graphql_content(response)
    assert content["data"]["page"] is None

    # query by slug
    variables = {"slug": page.slug}
    response = user_api_client.post_graphql(PAGE_QUERY, variables)
    content = get_graphql_content(response)
    assert content["data"]["page"] is None


def test_staff_query_unpublished_page_by_id(
    staff_api_client, page, permission_manage_pages
):
    page.is_published = False
    page.save()

    # query by ID
    variables = {"id": graphene.Node.to_global_id("Page", page.id)}
    response = staff_api_client.post_graphql(
        PAGE_QUERY,
        variables,
        permissions=[permission_manage_pages],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    assert content["data"]["page"]["id"] == variables["id"]


def test_staff_query_unpublished_page_by_id_without_required_permission(
    staff_api_client,
    page,
):
    page.is_published = False
    page.save()

    # query by ID
    variables = {"id": graphene.Node.to_global_id("Page", page.id)}
    response = staff_api_client.post_graphql(PAGE_QUERY, variables)
    content = get_graphql_content(response)
    assert content["data"]["page"] is None


def test_staff_query_unpublished_page_by_slug(
    staff_api_client, page, permission_manage_pages
):
    page.is_published = False
    page.save()

    # query by slug
    variables = {"slug": page.slug}
    response = staff_api_client.post_graphql(
        PAGE_QUERY,
        variables,
        permissions=[permission_manage_pages],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    assert content["data"]["page"]["id"] == graphene.Node.to_global_id("Page", page.id)


def test_staff_query_unpublished_page_by_slug_without_required_permission(
    staff_api_client,
    page,
):
    page.is_published = False
    page.save()

    # query by slug
    variables = {"slug": page.slug}
    response = staff_api_client.post_graphql(PAGE_QUERY, variables)
    content = get_graphql_content(response)
    assert content["data"]["page"] is None


def test_staff_query_page_by_invalid_id(staff_api_client, page):
    id = "bh/"
    variables = {"id": id}
    response = staff_api_client.post_graphql(PAGE_QUERY, variables)
    content = get_graphql_content_from_response(response)
    assert len(content["errors"]) == 1
    assert content["errors"][0]["message"] == f"Couldn't resolve id: {id}."
    assert content["data"]["page"] is None


def test_staff_query_page_with_invalid_object_type(staff_api_client, page):
    variables = {"id": graphene.Node.to_global_id("Order", page.id)}
    response = staff_api_client.post_graphql(PAGE_QUERY, variables)
    content = get_graphql_content(response)
    assert content["data"]["page"] is None


def test_get_page_with_sorted_attribute_values(
    staff_api_client,
    page,
    product_list,
    page_type_product_reference_attribute,
    permission_manage_pages,
):
    # given
    page_type = page.page_type
    page_type.page_attributes.set([page_type_product_reference_attribute])

    attr_value_1 = AttributeValue.objects.create(
        attribute=page_type_product_reference_attribute,
        name=product_list[0].name,
        slug=f"{page.pk}_{product_list[0].pk}",
    )
    attr_value_2 = AttributeValue.objects.create(
        attribute=page_type_product_reference_attribute,
        name=product_list[1].name,
        slug=f"{page.pk}_{product_list[1].pk}",
    )
    attr_value_3 = AttributeValue.objects.create(
        attribute=page_type_product_reference_attribute,
        name=product_list[2].name,
        slug=f"{page.pk}_{product_list[2].pk}",
    )

    attr_values = [attr_value_2, attr_value_1, attr_value_3]
    associate_attribute_values_to_instance(
        page, page_type_product_reference_attribute, *attr_values
    )

    page_id = graphene.Node.to_global_id("Page", page.id)
    variables = {"id": page_id}
    staff_api_client.user.user_permissions.add(permission_manage_pages)

    # when
    response = staff_api_client.post_graphql(PAGE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["page"]
    assert len(data["attributes"]) == 1
    values = data["attributes"][0]["values"]
    assert len(values) == 3
    assert [value["id"] for value in values] == [
        graphene.Node.to_global_id("AttributeValue", val.pk) for val in attr_values
    ]


CREATE_PAGE_MUTATION = """
    mutation CreatePage(
            $slug: String, $title: String, $content: JSONString, $pageType: ID!
            $isPublished: Boolean,
            $attributes: [AttributeValueInput!]) {
        pageCreate(
                input: {
                    slug: $slug, title: $title, pageType: $pageType
                    content: $content
                    isPublished: $isPublished, attributes: $attributes}) {
            page {
                id
                title
                content
                slug
                isPublished
                publicationDate
                pageType {
                    id
                }
                attributes {
                    attribute {
                        slug
                    }
                    values {
                        slug
                        name
                        reference
                        date
                        dateTime
                        file {
                            url
                            contentType
                        }
                    }
                }
            }
            errors {
                field
                code
                message
                attributes
            }
        }
    }
"""


@freeze_time("2020-03-18 12:00:00")
def test_page_create_mutation(staff_api_client, permission_manage_pages, page_type):
    page_slug = "test-slug"
    page_content = dummy_editorjs("test content", True)
    page_title = "test title"
    page_is_published = True
    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)

    # Default attributes defined in product_type fixture
    tag_attr = page_type.page_attributes.get(name="tag")
    tag_value_slug = tag_attr.values.first().slug
    tag_attr_id = graphene.Node.to_global_id("Attribute", tag_attr.id)

    # Add second attribute
    size_attr = page_type.page_attributes.get(name="Page size")
    size_attr_id = graphene.Node.to_global_id("Attribute", size_attr.id)
    non_existent_attr_value = "New value"

    # test creating root page
    variables = {
        "title": page_title,
        "content": page_content,
        "isPublished": page_is_published,
        "slug": page_slug,
        "pageType": page_type_id,
        "attributes": [
            {"id": tag_attr_id, "values": [tag_value_slug]},
            {"id": size_attr_id, "values": [non_existent_attr_value]},
        ],
    }

    response = staff_api_client.post_graphql(
        CREATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages]
    )
    content = get_graphql_content(response)
    data = content["data"]["pageCreate"]
    assert data["errors"] == []
    assert data["page"]["title"] == page_title
    assert data["page"]["content"] == page_content
    assert data["page"]["slug"] == page_slug
    assert data["page"]["isPublished"] == page_is_published
    assert data["page"]["publicationDate"] == "2020-03-18"
    assert data["page"]["pageType"]["id"] == page_type_id
    values = (
        data["page"]["attributes"][0]["values"][0]["slug"],
        data["page"]["attributes"][1]["values"][0]["slug"],
    )
    assert slugify(non_existent_attr_value) in values
    assert tag_value_slug in values


@freeze_time("1914-06-28 10:50")
@mock.patch("saleor.plugins.webhook.plugin._get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_page_create_trigger_page_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    permission_manage_pages,
    page_type,
    settings,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    page_slug = "test-slug"
    page_content = dummy_editorjs("test content", True)
    page_title = "test title"
    page_is_published = True
    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)
    # test creating root page
    variables = {
        "title": page_title,
        "content": page_content,
        "isPublished": page_is_published,
        "slug": page_slug,
        "pageType": page_type_id,
    }

    response = staff_api_client.post_graphql(
        CREATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages]
    )
    content = get_graphql_content(response)
    data = content["data"]["pageCreate"]
    assert data["errors"] == []
    assert data["page"]["title"] == page_title
    assert data["page"]["content"] == page_content
    assert data["page"]["slug"] == page_slug
    assert data["page"]["isPublished"] == page_is_published
    assert data["page"]["pageType"]["id"] == page_type_id
    page = Page.objects.first()
    expected_data = generate_page_payload(page, staff_api_client.user)

    mocked_webhook_trigger.assert_called_once_with(
        expected_data, WebhookEventAsyncType.PAGE_CREATED, [any_webhook]
    )


def test_page_create_required_fields(
    staff_api_client, permission_manage_pages, page_type
):
    variables = {"pageType": graphene.Node.to_global_id("PageType", page_type.pk)}
    response = staff_api_client.post_graphql(
        CREATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages]
    )
    content = get_graphql_content(response)
    errors = content["data"]["pageCreate"]["errors"]

    assert len(errors) == 1
    assert errors[0]["field"] == "title"
    assert errors[0]["code"] == PageErrorCode.REQUIRED.name


def test_create_default_slug(staff_api_client, permission_manage_pages, page_type):
    # test creating root page
    title = "Spanish inquisition"
    variables = {
        "title": title,
        "pageType": graphene.Node.to_global_id("PageType", page_type.pk),
    }
    response = staff_api_client.post_graphql(
        CREATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages]
    )
    content = get_graphql_content(response)
    data = content["data"]["pageCreate"]
    assert not data["errors"]
    assert data["page"]["title"] == title
    assert data["page"]["slug"] == slugify(title)


def test_page_create_mutation_missing_required_attributes(
    staff_api_client, permission_manage_pages, page_type
):
    # given
    page_slug = "test-slug"
    page_content = dummy_editorjs("test content", True)
    page_title = "test title"
    page_is_published = True
    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)

    # Default attributes defined in product_type fixture
    tag_attr = page_type.page_attributes.get(name="tag")
    tag_value_slug = tag_attr.values.first().slug
    tag_attr_id = graphene.Node.to_global_id("Attribute", tag_attr.id)

    # Add second attribute
    size_attr = page_type.page_attributes.get(name="Page size")
    size_attr.value_required = True
    size_attr.save(update_fields=["value_required"])

    # test creating root page
    variables = {
        "title": page_title,
        "content": page_content,
        "isPublished": page_is_published,
        "slug": page_slug,
        "pageType": page_type_id,
        "attributes": [{"id": tag_attr_id, "values": [tag_value_slug]}],
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageCreate"]
    errors = data["errors"]

    assert not data["page"]
    assert len(errors) == 1
    assert errors[0]["field"] == "attributes"
    assert errors[0]["code"] == PageErrorCode.REQUIRED.name
    assert errors[0]["attributes"] == [
        graphene.Node.to_global_id("Attribute", size_attr.pk)
    ]


def test_page_create_mutation_empty_attribute_value(
    staff_api_client, permission_manage_pages, page_type
):
    # given
    page_slug = "test-slug"
    page_content = dummy_editorjs("test content", True)
    page_title = "test title"
    page_is_published = True
    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)

    # Default attributes defined in product_type fixture
    tag_attr = page_type.page_attributes.get(name="tag")
    tag_attr_id = graphene.Node.to_global_id("Attribute", tag_attr.id)

    # test creating root page
    variables = {
        "title": page_title,
        "content": page_content,
        "isPublished": page_is_published,
        "slug": page_slug,
        "pageType": page_type_id,
        "attributes": [{"id": tag_attr_id, "values": ["  "]}],
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageCreate"]
    errors = data["errors"]

    assert not data["page"]
    assert len(errors) == 1
    assert errors[0]["field"] == "attributes"
    assert errors[0]["code"] == PageErrorCode.REQUIRED.name
    assert errors[0]["attributes"] == [
        graphene.Node.to_global_id("Attribute", tag_attr.pk)
    ]


def test_create_page_with_file_attribute(
    staff_api_client, permission_manage_pages, page_type, page_file_attribute
):
    # given
    page_slug = "test-slug"
    page_content = dummy_editorjs("test content", True)
    page_title = "test title"
    page_is_published = True
    page_type = PageType.objects.create(
        name="Test page type 2", slug="test-page-type-2"
    )
    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)

    file_attribute_id = graphene.Node.to_global_id("Attribute", page_file_attribute.pk)
    page_type.page_attributes.add(page_file_attribute)
    attr_value = page_file_attribute.values.first()

    values_count = page_file_attribute.values.count()

    # test creating root page
    variables = {
        "title": page_title,
        "content": page_content,
        "isPublished": page_is_published,
        "slug": page_slug,
        "pageType": page_type_id,
        "attributes": [{"id": file_attribute_id, "file": attr_value.file_url}],
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageCreate"]
    errors = data["errors"]

    assert not errors
    assert data["page"]["title"] == page_title
    assert data["page"]["content"] == page_content
    assert data["page"]["slug"] == page_slug
    assert data["page"]["isPublished"] == page_is_published
    assert data["page"]["pageType"]["id"] == page_type_id
    assert len(data["page"]["attributes"]) == 1
    expected_attr_data = {
        "attribute": {"slug": page_file_attribute.slug},
        "values": [
            {
                "slug": f"{attr_value.slug}-2",
                "name": attr_value.name,
                "file": {
                    "url": f"http://testserver/media/{attr_value.file_url}",
                    "contentType": None,
                },
                "reference": None,
                "date": None,
                "dateTime": None,
            }
        ],
    }
    assert data["page"]["attributes"][0] == expected_attr_data

    page_file_attribute.refresh_from_db()
    assert page_file_attribute.values.count() == values_count + 1


def test_create_page_with_file_attribute_new_attribute_value(
    staff_api_client, permission_manage_pages, page_type, page_file_attribute
):
    # given
    page_slug = "test-slug"
    page_content = dummy_editorjs("test content", True)
    page_title = "test title"
    page_is_published = True
    page_type = PageType.objects.create(
        name="Test page type 2", slug="test-page-type-2"
    )
    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)

    file_attribute_id = graphene.Node.to_global_id("Attribute", page_file_attribute.pk)
    page_type.page_attributes.add(page_file_attribute)
    new_value = "new_test_value.txt"
    new_value_content_type = "text/plain"

    values_count = page_file_attribute.values.count()

    # test creating root page
    variables = {
        "title": page_title,
        "content": page_content,
        "isPublished": page_is_published,
        "slug": page_slug,
        "pageType": page_type_id,
        "attributes": [
            {
                "id": file_attribute_id,
                "file": new_value,
                "contentType": new_value_content_type,
            }
        ],
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageCreate"]
    errors = data["errors"]

    assert not errors
    assert data["page"]["title"] == page_title
    assert data["page"]["content"] == page_content
    assert data["page"]["slug"] == page_slug
    assert data["page"]["isPublished"] == page_is_published
    assert data["page"]["pageType"]["id"] == page_type_id
    assert len(data["page"]["attributes"]) == 1
    expected_attr_data = {
        "attribute": {"slug": page_file_attribute.slug},
        "values": [
            {
                "slug": slugify(new_value),
                "reference": None,
                "name": new_value,
                "file": {
                    "url": "http://testserver/media/" + new_value,
                    "contentType": new_value_content_type,
                },
                "date": None,
                "dateTime": None,
            }
        ],
    }
    assert data["page"]["attributes"][0] == expected_attr_data

    page_file_attribute.refresh_from_db()
    assert page_file_attribute.values.count() == values_count + 1


def test_create_page_with_file_attribute_not_required_no_file_url_given(
    staff_api_client, permission_manage_pages, page_type, page_file_attribute
):
    # given
    page_slug = "test-slug"
    page_content = dummy_editorjs("test content", True)
    page_title = "test title"
    page_is_published = True
    page_type = PageType.objects.create(
        name="Test page type 2", slug="test-page-type-2"
    )
    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)

    file_attribute_id = graphene.Node.to_global_id("Attribute", page_file_attribute.pk)
    page_type.page_attributes.add(page_file_attribute)

    page_file_attribute.value_required = False
    page_file_attribute.save(update_fields=["value_required"])

    # test creating root page
    variables = {
        "title": page_title,
        "content": page_content,
        "isPublished": page_is_published,
        "slug": page_slug,
        "pageType": page_type_id,
        "attributes": [{"id": file_attribute_id, "file": ""}],
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages]
    )

    content = get_graphql_content(response)
    data = content["data"]["pageCreate"]
    assert data["errors"] == []
    assert data["page"]["title"] == page_title
    assert data["page"]["content"] == page_content
    assert data["page"]["slug"] == page_slug
    assert data["page"]["isPublished"] == page_is_published
    assert data["page"]["pageType"]["id"] == page_type_id
    assert len(data["page"]["attributes"]) == 1
    assert len(data["page"]["attributes"][0]["values"]) == 0


def test_create_page_with_file_attribute_required_no_file_url_given(
    staff_api_client, permission_manage_pages, page_type, page_file_attribute
):
    # given
    page_slug = "test-slug"
    page_content = dummy_editorjs("test content", True)
    page_title = "test title"
    page_is_published = True
    page_type = PageType.objects.create(
        name="Test page type 2", slug="test-page-type-2"
    )
    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)

    file_attribute_id = graphene.Node.to_global_id("Attribute", page_file_attribute.pk)
    page_type.page_attributes.add(page_file_attribute)

    page_file_attribute.value_required = True
    page_file_attribute.save(update_fields=["value_required"])

    # test creating root page
    variables = {
        "title": page_title,
        "content": page_content,
        "isPublished": page_is_published,
        "slug": page_slug,
        "pageType": page_type_id,
        "attributes": [{"id": file_attribute_id, "file": ""}],
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages]
    )

    content = get_graphql_content(response)
    data = content["data"]["pageCreate"]
    errors = data["errors"]
    assert not data["page"]
    assert len(errors) == 1
    assert errors[0]["code"] == PageErrorCode.REQUIRED.name
    assert errors[0]["field"] == "attributes"
    assert errors[0]["attributes"] == [file_attribute_id]


def test_create_page_with_page_reference_attribute(
    staff_api_client,
    permission_manage_pages,
    page_type,
    page_type_page_reference_attribute,
    page,
):
    # given
    page_slug = "test-slug"
    page_content = dummy_editorjs("test content", True)
    page_title = "test title"
    page_is_published = True
    page_type = PageType.objects.create(
        name="Test page type 2", slug="test-page-type-2"
    )
    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)

    ref_attribute_id = graphene.Node.to_global_id(
        "Attribute", page_type_page_reference_attribute.pk
    )
    page_type.page_attributes.add(page_type_page_reference_attribute)
    reference = graphene.Node.to_global_id("Page", page.pk)

    values_count = page_type_page_reference_attribute.values.count()

    # test creating root page
    variables = {
        "title": page_title,
        "content": page_content,
        "isPublished": page_is_published,
        "slug": page_slug,
        "pageType": page_type_id,
        "attributes": [{"id": ref_attribute_id, "references": [reference]}],
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageCreate"]
    errors = data["errors"]

    assert not errors
    assert data["page"]["title"] == page_title
    assert data["page"]["content"] == page_content
    assert data["page"]["slug"] == page_slug
    assert data["page"]["isPublished"] == page_is_published
    assert data["page"]["pageType"]["id"] == page_type_id
    assert len(data["page"]["attributes"]) == 1
    page_id = data["page"]["id"]
    _, new_page_pk = graphene.Node.from_global_id(page_id)
    expected_attr_data = {
        "attribute": {"slug": page_type_page_reference_attribute.slug},
        "values": [
            {
                "slug": f"{new_page_pk}_{page.pk}",
                "file": None,
                "name": page.title,
                "reference": reference,
                "date": None,
                "dateTime": None,
            }
        ],
    }
    assert data["page"]["attributes"][0] == expected_attr_data

    page_type_page_reference_attribute.refresh_from_db()
    assert page_type_page_reference_attribute.values.count() == values_count + 1


@freeze_time(datetime(2020, 5, 5, 5, 5, 5, tzinfo=pytz.utc))
def test_create_page_with_date_attribute(
    staff_api_client,
    permission_manage_pages,
    page_type,
    date_attribute,
    page,
):
    # given
    page_type.page_attributes.add(date_attribute)

    page_title = "test title"
    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)
    date_attribute_id = graphene.Node.to_global_id("Attribute", date_attribute.id)
    date_time_value = datetime.now(tz=pytz.utc)
    date_value = date_time_value.date()

    variables = {
        "title": page_title,
        "pageType": page_type_id,
        "attributes": [
            {"id": date_attribute_id, "date": date_value},
        ],
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageCreate"]
    errors = data["errors"]

    assert not errors
    assert data["page"]["title"] == page_title
    assert data["page"]["pageType"]["id"] == page_type_id
    page_id = data["page"]["id"]
    _, new_page_pk = graphene.Node.from_global_id(page_id)
    expected_attributes_data = {
        "attribute": {"slug": "release-date"},
        "values": [
            {
                "file": None,
                "reference": None,
                "dateTime": None,
                "date": str(date_value),
                "name": str(date_value),
                "slug": f"{new_page_pk}_{date_attribute.id}",
            }
        ],
    }

    assert expected_attributes_data in data["page"]["attributes"]


@freeze_time(datetime(2020, 5, 5, 5, 5, 5, tzinfo=pytz.utc))
def test_create_page_with_date_time_attribute(
    staff_api_client,
    permission_manage_pages,
    page_type,
    date_time_attribute,
    page,
):
    # given
    page_type.page_attributes.add(date_time_attribute)

    page_title = "test title"
    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)
    date_time_attribute_id = graphene.Node.to_global_id(
        "Attribute", date_time_attribute.id
    )
    date_time_value = datetime.now(tz=pytz.utc)
    variables = {
        "title": page_title,
        "pageType": page_type_id,
        "attributes": [
            {"id": date_time_attribute_id, "dateTime": date_time_value},
        ],
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageCreate"]
    errors = data["errors"]

    assert not errors
    assert data["page"]["title"] == page_title
    assert data["page"]["pageType"]["id"] == page_type_id
    page_id = data["page"]["id"]
    _, new_page_pk = graphene.Node.from_global_id(page_id)
    expected_attributes_data = {
        "attribute": {"slug": "release-date-time"},
        "values": [
            {
                "file": None,
                "reference": None,
                "dateTime": date_time_value.isoformat(),
                "date": None,
                "name": str(date_time_value),
                "slug": f"{new_page_pk}_{date_time_attribute.id}",
            }
        ],
    }

    assert expected_attributes_data in data["page"]["attributes"]


def test_create_page_with_page_reference_attribute_not_required_no_references_given(
    staff_api_client,
    permission_manage_pages,
    page_type,
    page_type_page_reference_attribute,
):
    # given
    page_slug = "test-slug"
    page_content = dummy_editorjs("test content", True)
    page_title = "test title"
    page_is_published = True
    page_type = PageType.objects.create(
        name="Test page type 2", slug="test-page-type-2"
    )
    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)

    file_attribute_id = graphene.Node.to_global_id(
        "Attribute", page_type_page_reference_attribute.pk
    )
    page_type.page_attributes.add(page_type_page_reference_attribute)

    page_type_page_reference_attribute.value_required = False
    page_type_page_reference_attribute.save(update_fields=["value_required"])

    # test creating root page
    variables = {
        "title": page_title,
        "content": page_content,
        "isPublished": page_is_published,
        "slug": page_slug,
        "pageType": page_type_id,
        "attributes": [{"id": file_attribute_id, "file": ""}],
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages]
    )

    content = get_graphql_content(response)
    data = content["data"]["pageCreate"]
    assert data["errors"] == []
    assert data["page"]["title"] == page_title
    assert data["page"]["content"] == page_content
    assert data["page"]["slug"] == page_slug
    assert data["page"]["isPublished"] == page_is_published
    assert data["page"]["pageType"]["id"] == page_type_id
    assert len(data["page"]["attributes"]) == 1
    assert len(data["page"]["attributes"][0]["values"]) == 0


def test_create_page_with_page_reference_attribute_required_no_references_given(
    staff_api_client,
    permission_manage_pages,
    page_type,
    page_type_page_reference_attribute,
):
    # given
    page_slug = "test-slug"
    page_content = dummy_editorjs("test content", True)
    page_title = "test title"
    page_is_published = True
    page_type = PageType.objects.create(
        name="Test page type 2", slug="test-page-type-2"
    )
    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)

    file_attribute_id = graphene.Node.to_global_id(
        "Attribute", page_type_page_reference_attribute.pk
    )
    page_type.page_attributes.add(page_type_page_reference_attribute)

    page_type_page_reference_attribute.value_required = True
    page_type_page_reference_attribute.save(update_fields=["value_required"])

    # test creating root page
    variables = {
        "title": page_title,
        "content": page_content,
        "isPublished": page_is_published,
        "slug": page_slug,
        "pageType": page_type_id,
        "attributes": [{"id": file_attribute_id, "file": ""}],
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages]
    )

    content = get_graphql_content(response)
    data = content["data"]["pageCreate"]
    errors = data["errors"]
    assert not data["page"]
    assert len(errors) == 1
    assert errors[0]["code"] == PageErrorCode.REQUIRED.name
    assert errors[0]["field"] == "attributes"
    assert errors[0]["attributes"] == [file_attribute_id]


def test_create_page_with_product_reference_attribute(
    staff_api_client,
    permission_manage_pages,
    page_type,
    page_type_product_reference_attribute,
    product,
):
    # given
    page_slug = "test-slug"
    page_content = dummy_editorjs("test content", True)
    page_title = "test title"
    page_is_published = True
    page_type = PageType.objects.create(
        name="Test page type 2", slug="test-page-type-2"
    )
    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)

    ref_attribute_id = graphene.Node.to_global_id(
        "Attribute", page_type_product_reference_attribute.pk
    )
    page_type.page_attributes.add(page_type_product_reference_attribute)
    reference = graphene.Node.to_global_id("Product", product.pk)

    values_count = page_type_product_reference_attribute.values.count()

    # test creating root page
    variables = {
        "title": page_title,
        "content": page_content,
        "isPublished": page_is_published,
        "slug": page_slug,
        "pageType": page_type_id,
        "attributes": [{"id": ref_attribute_id, "references": [reference]}],
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageCreate"]
    errors = data["errors"]

    assert not errors
    assert data["page"]["title"] == page_title
    assert data["page"]["content"] == page_content
    assert data["page"]["slug"] == page_slug
    assert data["page"]["isPublished"] == page_is_published
    assert data["page"]["pageType"]["id"] == page_type_id
    assert len(data["page"]["attributes"]) == 1
    page_id = data["page"]["id"]
    _, new_page_pk = graphene.Node.from_global_id(page_id)
    expected_attr_data = {
        "attribute": {"slug": page_type_product_reference_attribute.slug},
        "values": [
            {
                "slug": f"{new_page_pk}_{product.pk}",
                "file": None,
                "name": product.name,
                "reference": reference,
                "dateTime": None,
                "date": None,
            }
        ],
    }
    assert data["page"]["attributes"][0] == expected_attr_data

    page_type_product_reference_attribute.refresh_from_db()
    assert page_type_product_reference_attribute.values.count() == values_count + 1


def test_create_page_with_product_reference_attribute_not_required_no_references_given(
    staff_api_client,
    permission_manage_pages,
    page_type,
    page_type_product_reference_attribute,
):
    # given
    page_slug = "test-slug"
    page_content = dummy_editorjs("test content", True)
    page_title = "test title"
    page_is_published = True
    page_type = PageType.objects.create(
        name="Test page type 2", slug="test-page-type-2"
    )
    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)

    file_attribute_id = graphene.Node.to_global_id(
        "Attribute", page_type_product_reference_attribute.pk
    )
    page_type.page_attributes.add(page_type_product_reference_attribute)

    page_type_product_reference_attribute.value_required = False
    page_type_product_reference_attribute.save(update_fields=["value_required"])

    # test creating root page
    variables = {
        "title": page_title,
        "content": page_content,
        "isPublished": page_is_published,
        "slug": page_slug,
        "pageType": page_type_id,
        "attributes": [{"id": file_attribute_id, "file": ""}],
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages]
    )

    content = get_graphql_content(response)
    data = content["data"]["pageCreate"]
    assert data["errors"] == []
    assert data["page"]["title"] == page_title
    assert data["page"]["content"] == page_content
    assert data["page"]["slug"] == page_slug
    assert data["page"]["isPublished"] == page_is_published
    assert data["page"]["pageType"]["id"] == page_type_id
    assert len(data["page"]["attributes"]) == 1
    assert len(data["page"]["attributes"][0]["values"]) == 0


def test_create_page_with_product_reference_attribute_required_no_references_given(
    staff_api_client,
    permission_manage_pages,
    page_type,
    page_type_product_reference_attribute,
):
    # given
    page_slug = "test-slug"
    page_content = dummy_editorjs("test content", True)
    page_title = "test title"
    page_is_published = True
    page_type = PageType.objects.create(
        name="Test page type 2", slug="test-page-type-2"
    )
    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)

    file_attribute_id = graphene.Node.to_global_id(
        "Attribute", page_type_product_reference_attribute.pk
    )
    page_type.page_attributes.add(page_type_product_reference_attribute)

    page_type_product_reference_attribute.value_required = True
    page_type_product_reference_attribute.save(update_fields=["value_required"])

    # test creating root page
    variables = {
        "title": page_title,
        "content": page_content,
        "isPublished": page_is_published,
        "slug": page_slug,
        "pageType": page_type_id,
        "attributes": [{"id": file_attribute_id, "file": ""}],
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages]
    )

    content = get_graphql_content(response)
    data = content["data"]["pageCreate"]
    errors = data["errors"]
    assert not data["page"]
    assert len(errors) == 1
    assert errors[0]["code"] == PageErrorCode.REQUIRED.name
    assert errors[0]["field"] == "attributes"
    assert errors[0]["attributes"] == [file_attribute_id]


PAGE_DELETE_MUTATION = """
    mutation DeletePage($id: ID!) {
        pageDelete(id: $id) {
            page {
                title
                id
            }
            errors {
                field
                code
                message
            }
        }
    }
"""


def test_page_delete_mutation(staff_api_client, page, permission_manage_pages):
    variables = {"id": graphene.Node.to_global_id("Page", page.id)}
    response = staff_api_client.post_graphql(
        PAGE_DELETE_MUTATION, variables, permissions=[permission_manage_pages]
    )
    content = get_graphql_content(response)
    data = content["data"]["pageDelete"]
    assert data["page"]["title"] == page.title
    with pytest.raises(page._meta.model.DoesNotExist):
        page.refresh_from_db()


@freeze_time("1914-06-28 10:50")
@mock.patch("saleor.plugins.webhook.plugin._get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_page_delete_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    page,
    permission_manage_pages,
    settings,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    variables = {"id": graphene.Node.to_global_id("Page", page.id)}
    response = staff_api_client.post_graphql(
        PAGE_DELETE_MUTATION, variables, permissions=[permission_manage_pages]
    )
    content = get_graphql_content(response)
    data = content["data"]["pageDelete"]
    assert data["page"]["title"] == page.title
    with pytest.raises(page._meta.model.DoesNotExist):
        page.refresh_from_db()
    expected_data = generate_page_payload(page, staff_api_client.user)
    mocked_webhook_trigger.assert_called_once_with(
        expected_data, WebhookEventAsyncType.PAGE_DELETED, [any_webhook]
    )


@mock.patch("saleor.attribute.signals.delete_from_storage_task.delay")
def test_page_delete_with_file_attribute(
    delete_from_storage_task_mock,
    staff_api_client,
    page,
    permission_manage_pages,
    page_file_attribute,
):
    # given
    page_type = page.page_type
    page_type.page_attributes.add(page_file_attribute)
    existing_value = page_file_attribute.values.first()
    associate_attribute_values_to_instance(page, page_file_attribute, existing_value)

    variables = {"id": graphene.Node.to_global_id("Page", page.id)}

    # when
    response = staff_api_client.post_graphql(
        PAGE_DELETE_MUTATION, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageDelete"]
    assert data["page"]["title"] == page.title
    with pytest.raises(page._meta.model.DoesNotExist):
        page.refresh_from_db()
    with pytest.raises(existing_value._meta.model.DoesNotExist):
        existing_value.refresh_from_db()
    delete_from_storage_task_mock.assert_called_once_with(existing_value.file_url)


UPDATE_PAGE_MUTATION = """
    mutation updatePage(
        $id: ID!, $input: PageInput!
    ) {
        pageUpdate(
            id: $id, input: $input
        ) {
            page {
                id
                title
                slug
                isPublished
                publicationDate
                attributes {
                    attribute {
                        slug
                    }
                    values {
                        slug
                        name
                        reference
                        file {
                            url
                            contentType
                        }
                    }
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


def test_update_page(staff_api_client, permission_manage_pages, page):
    # given
    query = UPDATE_PAGE_MUTATION

    page_type = page.page_type
    tag_attr = page_type.page_attributes.get(name="tag")
    tag_attr_id = graphene.Node.to_global_id("Attribute", tag_attr.id)
    new_value = "Rainbow"

    page_title = page.title
    new_slug = "new-slug"
    assert new_slug != page.slug

    page_id = graphene.Node.to_global_id("Page", page.id)

    variables = {
        "id": page_id,
        "input": {
            "slug": new_slug,
            "isPublished": True,
            "attributes": [{"id": tag_attr_id, "values": [new_value]}],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageUpdate"]

    assert not data["errors"]
    assert data["page"]["title"] == page_title
    assert data["page"]["slug"] == new_slug

    expected_attributes = []
    page_attr = page.attributes.all()
    for attr in page_type.page_attributes.all():
        if attr.slug != tag_attr.slug:
            values = [
                {"slug": slug, "file": None, "name": name, "reference": None}
                for slug, name in page_attr.filter(
                    assignment__attribute=attr
                ).values_list("values__slug", "values__name")
            ]
        else:
            values = [
                {
                    "slug": slugify(new_value),
                    "file": None,
                    "name": new_value,
                    "reference": None,
                }
            ]
        attr_data = {
            "attribute": {"slug": attr.slug},
            "values": values,
        }
        expected_attributes.append(attr_data)

    attributes = data["page"]["attributes"]
    assert len(attributes) == len(expected_attributes)
    for attr_data in attributes:
        assert attr_data in expected_attributes


@mock.patch("saleor.plugins.webhook.plugin._get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
@freeze_time("2020-03-18 12:00:00")
def test_update_page_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    permission_manage_pages,
    page,
    settings,
):
    query = UPDATE_PAGE_MUTATION

    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    mocked_get_webhooks_for_event.return_value = [any_webhook]

    page_title = page.title
    new_slug = "new-slug"
    assert new_slug != page.slug

    page_id = graphene.Node.to_global_id("Page", page.id)

    variables = {
        "id": page_id,
        "input": {
            "slug": new_slug,
            "isPublished": True,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageUpdate"]

    assert not data["errors"]
    assert data["page"]["title"] == page_title
    assert data["page"]["slug"] == new_slug
    page.publication_date = date(2020, 3, 18)
    expected_data = generate_page_payload(page, staff_api_client.user)
    mocked_webhook_trigger.assert_called_once_with(
        expected_data, WebhookEventAsyncType.PAGE_UPDATED, [any_webhook]
    )


def test_update_page_only_title(staff_api_client, permission_manage_pages, page):
    """Ensures that updating page field without providing attributes is allowed."""
    # given
    query = UPDATE_PAGE_MUTATION

    page_type = page.page_type
    page_title = page.title
    new_slug = "new-slug"
    assert new_slug != page.slug

    page_id = graphene.Node.to_global_id("Page", page.id)

    variables = {
        "id": page_id,
        "input": {
            "slug": new_slug,
            "isPublished": True,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageUpdate"]

    assert not data["errors"]
    assert data["page"]["title"] == page_title
    assert data["page"]["slug"] == new_slug

    expected_attributes = []
    page_attr = page.attributes.all()
    for attr in page_type.page_attributes.all():
        values = [
            {"slug": slug, "file": None, "name": name, "reference": None}
            for slug, name in page_attr.filter(assignment__attribute=attr).values_list(
                "values__slug", "values__name"
            )
        ]
        attr_data = {
            "attribute": {"slug": attr.slug},
            "values": values,
        }
        expected_attributes.append(attr_data)

    attributes = data["page"]["attributes"]
    assert len(attributes) == len(expected_attributes)
    for attr_data in attributes:
        assert attr_data in expected_attributes


def test_update_page_with_file_attribute_value(
    staff_api_client, permission_manage_pages, page, page_file_attribute
):
    # given
    query = UPDATE_PAGE_MUTATION

    page_type = page.page_type
    page_type.page_attributes.add(page_file_attribute)
    new_value = "test.txt"
    page_file_attribute_id = graphene.Node.to_global_id(
        "Attribute", page_file_attribute.pk
    )

    page_id = graphene.Node.to_global_id("Page", page.id)

    variables = {
        "id": page_id,
        "input": {"attributes": [{"id": page_file_attribute_id, "file": new_value}]},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageUpdate"]

    assert not data["errors"]
    assert data["page"]
    updated_attribute = {
        "attribute": {"slug": page_file_attribute.slug},
        "values": [
            {
                "slug": slugify(new_value),
                "name": new_value,
                "reference": None,
                "file": {
                    "url": "http://testserver/media/" + new_value,
                    "contentType": None,
                },
            }
        ],
    }
    assert updated_attribute in data["page"]["attributes"]


def test_update_page_with_file_attribute_new_value_is_not_created(
    staff_api_client, permission_manage_pages, page, page_file_attribute
):
    # given
    query = UPDATE_PAGE_MUTATION

    page_type = page.page_type
    page_type.page_attributes.add(page_file_attribute)
    page_file_attribute_id = graphene.Node.to_global_id(
        "Attribute", page_file_attribute.pk
    )
    existing_value = page_file_attribute.values.first()
    associate_attribute_values_to_instance(page, page_file_attribute, existing_value)

    page_id = graphene.Node.to_global_id("Page", page.id)

    variables = {
        "id": page_id,
        "input": {
            "attributes": [
                {"id": page_file_attribute_id, "file": existing_value.file_url}
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageUpdate"]

    assert not data["errors"]
    assert data["page"]
    updated_attribute = {
        "attribute": {"slug": page_file_attribute.slug},
        "values": [
            {
                "slug": existing_value.slug,
                "name": existing_value.name,
                "reference": None,
                "file": {
                    "url": f"http://testserver/media/{existing_value.file_url}",
                    "contentType": existing_value.content_type,
                },
            }
        ],
    }
    assert updated_attribute in data["page"]["attributes"]


def test_update_page_clear_values(staff_api_client, permission_manage_pages, page):
    # given
    query = UPDATE_PAGE_MUTATION

    page_attr = page.attributes.first()
    attribute = page_attr.assignment.attribute
    attribute.value_required = False
    attribute.save(update_fields=["value_required"])

    page_file_attribute_id = graphene.Node.to_global_id("Attribute", attribute.pk)

    page_id = graphene.Node.to_global_id("Page", page.id)

    variables = {
        "id": page_id,
        "input": {"attributes": [{"id": page_file_attribute_id, "file": ""}]},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageUpdate"]

    assert not data["errors"]
    assert data["page"]
    assert not data["page"]["attributes"][0]["values"]

    with pytest.raises(page_attr._meta.model.DoesNotExist):
        page_attr.refresh_from_db()


def test_update_page_with_page_reference_attribute_new_value(
    staff_api_client,
    permission_manage_pages,
    page_list,
    page_type_page_reference_attribute,
):
    # given
    query = UPDATE_PAGE_MUTATION

    page = page_list[0]
    ref_page = page_list[1]
    page_type = page.page_type
    page_type.page_attributes.add(page_type_page_reference_attribute)

    values_count = page_type_page_reference_attribute.values.count()
    ref_attribute_id = graphene.Node.to_global_id(
        "Attribute", page_type_page_reference_attribute.pk
    )
    reference = graphene.Node.to_global_id("Page", ref_page.pk)

    page_id = graphene.Node.to_global_id("Page", page.id)

    variables = {
        "id": page_id,
        "input": {"attributes": [{"id": ref_attribute_id, "references": [reference]}]},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageUpdate"]

    assert not data["errors"]
    assert data["page"]
    updated_attribute = {
        "attribute": {"slug": page_type_page_reference_attribute.slug},
        "values": [
            {
                "slug": f"{page.pk}_{ref_page.pk}",
                "name": page.title,
                "file": None,
                "reference": reference,
            }
        ],
    }
    assert updated_attribute in data["page"]["attributes"]

    page_type_page_reference_attribute.refresh_from_db()
    assert page_type_page_reference_attribute.values.count() == values_count + 1


def test_update_page_with_page_reference_attribute_existing_value(
    staff_api_client,
    permission_manage_pages,
    page_list,
    page_type_page_reference_attribute,
):
    # given
    query = UPDATE_PAGE_MUTATION

    page = page_list[0]
    ref_page = page_list[1]
    page_type = page.page_type
    page_type.page_attributes.add(page_type_page_reference_attribute)

    attr_value = AttributeValue.objects.create(
        attribute=page_type_page_reference_attribute,
        name=page.title,
        slug=f"{page.pk}_{ref_page.pk}",
    )
    associate_attribute_values_to_instance(
        page, page_type_page_reference_attribute, attr_value
    )

    values_count = page_type_page_reference_attribute.values.count()
    ref_attribute_id = graphene.Node.to_global_id(
        "Attribute", page_type_page_reference_attribute.pk
    )
    reference = graphene.Node.to_global_id("Page", ref_page.pk)

    page_id = graphene.Node.to_global_id("Page", page.id)

    variables = {
        "id": page_id,
        "input": {"attributes": [{"id": ref_attribute_id, "references": [reference]}]},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageUpdate"]

    assert not data["errors"]
    assert data["page"]
    updated_attribute = {
        "attribute": {"slug": page_type_page_reference_attribute.slug},
        "values": [
            {
                "slug": attr_value.slug,
                "file": None,
                "name": page.title,
                "reference": reference,
            }
        ],
    }
    assert updated_attribute in data["page"]["attributes"]

    page_type_page_reference_attribute.refresh_from_db()
    assert page_type_page_reference_attribute.values.count() == values_count


def test_update_page_with_product_reference_attribute_new_value(
    staff_api_client,
    permission_manage_pages,
    page,
    page_type_product_reference_attribute,
    product,
):
    # given
    query = UPDATE_PAGE_MUTATION

    page_type = page.page_type
    page_type.page_attributes.add(page_type_product_reference_attribute)

    values_count = page_type_product_reference_attribute.values.count()
    ref_attribute_id = graphene.Node.to_global_id(
        "Attribute", page_type_product_reference_attribute.pk
    )
    reference = graphene.Node.to_global_id("Product", product.pk)

    page_id = graphene.Node.to_global_id("Page", page.id)

    variables = {
        "id": page_id,
        "input": {"attributes": [{"id": ref_attribute_id, "references": [reference]}]},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageUpdate"]

    assert not data["errors"]
    assert data["page"]
    updated_attribute = {
        "attribute": {"slug": page_type_product_reference_attribute.slug},
        "values": [
            {
                "slug": f"{page.pk}_{product.pk}",
                "name": product.name,
                "file": None,
                "reference": reference,
            }
        ],
    }
    assert updated_attribute in data["page"]["attributes"]

    page_type_product_reference_attribute.refresh_from_db()
    assert page_type_product_reference_attribute.values.count() == values_count + 1


def test_update_page_with_product_reference_attribute_existing_value(
    staff_api_client,
    permission_manage_pages,
    page,
    page_type_product_reference_attribute,
    product,
):
    # given
    query = UPDATE_PAGE_MUTATION

    page_type = page.page_type
    page_type.page_attributes.add(page_type_product_reference_attribute)

    attr_value = AttributeValue.objects.create(
        attribute=page_type_product_reference_attribute,
        name=page.title,
        slug=f"{page.pk}_{product.pk}",
    )
    associate_attribute_values_to_instance(
        page, page_type_product_reference_attribute, attr_value
    )

    values_count = page_type_product_reference_attribute.values.count()
    ref_attribute_id = graphene.Node.to_global_id(
        "Attribute", page_type_product_reference_attribute.pk
    )
    reference = graphene.Node.to_global_id("Product", product.pk)

    page_id = graphene.Node.to_global_id("Page", page.id)

    variables = {
        "id": page_id,
        "input": {"attributes": [{"id": ref_attribute_id, "references": [reference]}]},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageUpdate"]

    assert not data["errors"]
    assert data["page"]
    updated_attribute = {
        "attribute": {"slug": page_type_product_reference_attribute.slug},
        "values": [
            {
                "slug": attr_value.slug,
                "file": None,
                "name": page.title,
                "reference": reference,
            }
        ],
    }
    assert updated_attribute in data["page"]["attributes"]

    page_type_product_reference_attribute.refresh_from_db()
    assert page_type_product_reference_attribute.values.count() == values_count


@freeze_time("2020-03-18 12:00:00")
def test_public_page_sets_publication_date(
    staff_api_client, permission_manage_pages, page_type
):
    data = {
        "slug": "test-url",
        "title": "Test page",
        "content": dummy_editorjs("Content for page 1"),
        "is_published": False,
        "page_type": page_type,
    }
    page = Page.objects.create(**data)
    page_id = graphene.Node.to_global_id("Page", page.id)
    variables = {"id": page_id, "input": {"isPublished": True, "slug": page.slug}}
    response = staff_api_client.post_graphql(
        UPDATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages]
    )
    content = get_graphql_content(response)
    data = content["data"]["pageUpdate"]

    assert not data["errors"]
    assert data["page"]["isPublished"] is True
    assert data["page"]["publicationDate"] == "2020-03-18"


@pytest.mark.parametrize("slug_value", [None, ""])
def test_update_page_blank_slug_value(
    staff_api_client, permission_manage_pages, page, slug_value
):
    query = UPDATE_PAGE_MUTATION
    assert slug_value != page.slug

    page_id = graphene.Node.to_global_id("Page", page.id)
    variables = {"id": page_id, "input": {"slug": slug_value, "isPublished": True}}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_pages]
    )
    content = get_graphql_content(response)
    errors = content["data"]["pageUpdate"]["errors"]

    assert len(errors) == 1
    assert errors[0]["field"] == "slug"
    assert errors[0]["code"] == PageErrorCode.REQUIRED.name


@pytest.mark.parametrize("slug_value", [None, ""])
def test_update_page_with_title_value_and_without_slug_value(
    staff_api_client, permission_manage_pages, page, slug_value
):
    query = """
        mutation updatePage($id: ID!, $title: String, $slug: String) {
        pageUpdate(id: $id, input: {title: $title, slug: $slug}) {
            page {
                id
                title
                slug
            }
            errors {
                field
                code
                message
            }
        }
    }
    """
    page_id = graphene.Node.to_global_id("Page", page.id)
    variables = {"id": page_id, "title": "test", "slug": slug_value}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_pages]
    )
    content = get_graphql_content(response)
    errors = content["data"]["pageUpdate"]["errors"]

    assert len(errors) == 1
    assert errors[0]["field"] == "slug"
    assert errors[0]["code"] == PageErrorCode.REQUIRED.name


UPDATE_PAGE_ATTRIBUTES_MUTATION = """
    mutation updatePage(
        $id: ID!, $input: PageInput!
    ) {
        pageUpdate(
            id: $id, input: $input
        ) {
            page {
                id
                title
                slug
                attributes {
                    attribute {
                        slug
                    }
                    values {
                        id
                        slug
                        name
                    }
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


def test_update_page_change_attribute_values_ordering(
    staff_api_client,
    permission_manage_pages,
    page,
    product_list,
    page_type_product_reference_attribute,
):
    # given
    page_type = page.page_type
    page_type.page_attributes.set([page_type_product_reference_attribute])

    page_id = graphene.Node.to_global_id("Page", page.pk)

    attribute_id = graphene.Node.to_global_id(
        "Attribute", page_type_product_reference_attribute.pk
    )

    attr_value_1 = AttributeValue.objects.create(
        attribute=page_type_product_reference_attribute,
        name=product_list[0].name,
        slug=f"{page.pk}_{product_list[0].pk}",
    )
    attr_value_2 = AttributeValue.objects.create(
        attribute=page_type_product_reference_attribute,
        name=product_list[1].name,
        slug=f"{page.pk}_{product_list[1].pk}",
    )
    attr_value_3 = AttributeValue.objects.create(
        attribute=page_type_product_reference_attribute,
        name=product_list[2].name,
        slug=f"{page.pk}_{product_list[2].pk}",
    )

    associate_attribute_values_to_instance(
        page,
        page_type_product_reference_attribute,
        attr_value_3,
        attr_value_2,
        attr_value_1,
    )

    assert list(
        page.attributes.first().pagevalueassignment.values_list("value_id", flat=True)
    ) == [attr_value_3.pk, attr_value_2.pk, attr_value_1.pk]

    new_ref_order = [product_list[1], product_list[0], product_list[2]]
    variables = {
        "id": page_id,
        "input": {
            "attributes": [
                {
                    "id": attribute_id,
                    "references": [
                        graphene.Node.to_global_id("Product", ref.pk)
                        for ref in new_ref_order
                    ],
                }
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        UPDATE_PAGE_ATTRIBUTES_MUTATION,
        variables,
        permissions=[permission_manage_pages],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageUpdate"]
    assert data["errors"] == []

    attributes = data["page"]["attributes"]

    assert len(attributes) == 1
    values = attributes[0]["values"]
    assert len(values) == 3
    assert [value["id"] for value in values] == [
        graphene.Node.to_global_id("AttributeValue", val.pk)
        for val in [attr_value_2, attr_value_1, attr_value_3]
    ]
    page.refresh_from_db()
    assert list(
        page.attributes.first().pagevalueassignment.values_list("value_id", flat=True)
    ) == [attr_value_2.pk, attr_value_1.pk, attr_value_3.pk]


def test_paginate_pages(user_api_client, page, page_type):
    page.is_published = True
    data_02 = {
        "slug": "test02-url",
        "title": "Test page",
        "content": dummy_editorjs("Content for page 1"),
        "is_published": True,
        "page_type": page_type,
    }
    data_03 = {
        "slug": "test03-url",
        "title": "Test page",
        "content": dummy_editorjs("Content for page 1"),
        "is_published": True,
        "page_type": page_type,
    }

    Page.objects.create(**data_02)
    Page.objects.create(**data_03)
    query = """
        query PagesQuery {
            pages(first: 2) {
                edges {
                    node {
                        id
                        title
                    }
                }
            }
        }
        """
    response = user_api_client.post_graphql(query)
    content = get_graphql_content(response)
    pages_data = content["data"]["pages"]
    assert len(pages_data["edges"]) == 2


MUTATION_PUBLISH_PAGES = """
    mutation publishManyPages($ids: [ID]!, $is_published: Boolean!) {
        pageBulkPublish(ids: $ids, isPublished: $is_published) {
            count
        }
    }
    """


def test_bulk_publish(staff_api_client, page_list_unpublished, permission_manage_pages):
    page_list = page_list_unpublished
    assert not any(page.is_published for page in page_list)

    variables = {
        "ids": [graphene.Node.to_global_id("Page", page.id) for page in page_list],
        "is_published": True,
    }
    response = staff_api_client.post_graphql(
        MUTATION_PUBLISH_PAGES, variables, permissions=[permission_manage_pages]
    )
    content = get_graphql_content(response)
    page_list = Page.objects.filter(id__in=[page.pk for page in page_list])

    assert content["data"]["pageBulkPublish"]["count"] == len(page_list)
    assert all(page.is_published for page in page_list)


def test_bulk_unpublish(staff_api_client, page_list, permission_manage_pages):
    assert all(page.is_published for page in page_list)
    variables = {
        "ids": [graphene.Node.to_global_id("Page", page.id) for page in page_list],
        "is_published": False,
    }
    response = staff_api_client.post_graphql(
        MUTATION_PUBLISH_PAGES, variables, permissions=[permission_manage_pages]
    )
    content = get_graphql_content(response)
    page_list = Page.objects.filter(id__in=[page.pk for page in page_list])

    assert content["data"]["pageBulkPublish"]["count"] == len(page_list)
    assert not any(page.is_published for page in page_list)


QUERY_PAGES_WITH_FILTER = """
    query ($filter: PageFilterInput) {
        pages(first: 5, filter:$filter) {
            totalCount
            edges {
                node {
                    id
                }
            }
        }
    }
"""


@pytest.mark.parametrize(
    "page_filter, count",
    [
        ({"search": "Page1"}, 2),
        ({"search": "about"}, 1),
        ({"search": "test"}, 1),
        ({"search": "slug"}, 3),
        ({"search": "Page"}, 2),
    ],
)
def test_pages_query_with_filter(
    page_filter, count, staff_api_client, permission_manage_pages, page_type
):
    query = QUERY_PAGES_WITH_FILTER
    Page.objects.create(
        title="Page1",
        slug="slug_page_1",
        content=dummy_editorjs("Content for page 1"),
        page_type=page_type,
    )
    Page.objects.create(
        title="Page2",
        slug="slug_page_2",
        content=dummy_editorjs("Content for page 2"),
        page_type=page_type,
    )
    Page.objects.create(
        title="About",
        slug="slug_about",
        content=dummy_editorjs("About test content"),
        page_type=page_type,
    )
    variables = {"filter": page_filter}
    staff_api_client.user.user_permissions.add(permission_manage_pages)
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content["data"]["pages"]["totalCount"] == count


def test_pages_query_with_filter_by_page_type(
    staff_api_client, permission_manage_pages, page_type_list
):
    query = QUERY_PAGES_WITH_FILTER
    page_type_ids = [
        graphene.Node.to_global_id("PageType", page_type.id)
        for page_type in page_type_list
    ][:2]

    variables = {"filter": {"pageTypes": page_type_ids}}
    staff_api_client.user.user_permissions.add(permission_manage_pages)
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content["data"]["pages"]["totalCount"] == 2


def test_pages_query_with_filter_by_ids(
    staff_api_client, permission_manage_pages, page_list, page_list_unpublished
):
    query = QUERY_PAGES_WITH_FILTER

    page_ids = [
        graphene.Node.to_global_id("Page", page.pk)
        for page in [page_list[0], page_list_unpublished[-1]]
    ]
    variables = {"filter": {"ids": page_ids}}
    staff_api_client.user.user_permissions.add(permission_manage_pages)
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content["data"]["pages"]["totalCount"] == len(page_ids)


QUERY_PAGE_WITH_SORT = """
    query ($sort_by: PageSortingInput!) {
        pages(first:5, sortBy: $sort_by) {
            edges{
                node{
                    title
                }
            }
        }
    }
"""


@pytest.mark.parametrize(
    "page_sort, result_order",
    [
        ({"field": "TITLE", "direction": "ASC"}, ["About", "Page1", "Page2"]),
        ({"field": "TITLE", "direction": "DESC"}, ["Page2", "Page1", "About"]),
        ({"field": "SLUG", "direction": "ASC"}, ["About", "Page2", "Page1"]),
        ({"field": "SLUG", "direction": "DESC"}, ["Page1", "Page2", "About"]),
        ({"field": "VISIBILITY", "direction": "ASC"}, ["Page2", "About", "Page1"]),
        ({"field": "VISIBILITY", "direction": "DESC"}, ["Page1", "About", "Page2"]),
        ({"field": "CREATION_DATE", "direction": "ASC"}, ["Page1", "About", "Page2"]),
        ({"field": "CREATION_DATE", "direction": "DESC"}, ["Page2", "About", "Page1"]),
        (
            {"field": "PUBLICATION_DATE", "direction": "ASC"},
            ["Page1", "Page2", "About"],
        ),
        (
            {"field": "PUBLICATION_DATE", "direction": "DESC"},
            ["About", "Page2", "Page1"],
        ),
    ],
)
def test_query_pages_with_sort(
    page_sort, result_order, staff_api_client, permission_manage_pages, page_type
):
    with freeze_time("2017-05-31 12:00:01"):
        Page.objects.create(
            title="Page1",
            slug="slug_page_1",
            content=dummy_editorjs("p1."),
            is_published=True,
            publication_date=timezone.now().replace(year=2018, month=12, day=5),
            page_type=page_type,
        )
    with freeze_time("2019-05-31 12:00:01"):
        Page.objects.create(
            title="Page2",
            slug="page_2",
            content=dummy_editorjs("p2."),
            is_published=False,
            publication_date=timezone.now().replace(year=2019, month=12, day=5),
            page_type=page_type,
        )
    with freeze_time("2018-05-31 12:00:01"):
        Page.objects.create(
            title="About",
            slug="about",
            content=dummy_editorjs("Ab."),
            is_published=True,
            page_type=page_type,
        )
    variables = {"sort_by": page_sort}
    staff_api_client.user.user_permissions.add(permission_manage_pages)
    response = staff_api_client.post_graphql(QUERY_PAGE_WITH_SORT, variables)
    content = get_graphql_content(response)
    pages = content["data"]["pages"]["edges"]

    for order, page_name in enumerate(result_order):
        assert pages[order]["node"]["title"] == page_name
