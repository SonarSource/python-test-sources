from unittest.mock import Mock

import pytest
import requests
from django.core.exceptions import ValidationError

from ..installation_utils import install_app
from ..models import App
from ..types import AppExtensionMount, AppExtensionTarget


def test_install_app_created_app(
    app_manifest, app_installation, monkeypatch, permission_manage_products
):
    # given
    app_manifest["permissions"] = ["MANAGE_PRODUCTS"]
    mocked_get_response = Mock()
    mocked_get_response.json.return_value = app_manifest

    monkeypatch.setattr(requests, "get", Mock(return_value=mocked_get_response))
    monkeypatch.setattr("saleor.app.installation_utils.send_app_token", Mock())

    app_installation.permissions.set([permission_manage_products])

    # when
    app = install_app(app_installation, activate=True)

    # then
    assert App.objects.get().id == app.id
    assert list(app.permissions.all()) == [permission_manage_products]


def test_install_app_with_extension(
    app_manifest,
    app_installation,
    monkeypatch,
    permission_manage_products,
    permission_manage_orders,
):
    # given
    label = "Create product with app"
    url = "http://127.0.0.1:8080/app-extension"
    app_manifest["permissions"] = ["MANAGE_PRODUCTS", "MANAGE_ORDERS"]
    app_manifest["extensions"] = [
        {
            "label": label,
            "url": url,
            "mount": "PRODUCT_OVERVIEW_CREATE",
            "permissions": ["MANAGE_PRODUCTS"],
        }
    ]
    mocked_get_response = Mock()
    mocked_get_response.json.return_value = app_manifest

    monkeypatch.setattr(requests, "get", Mock(return_value=mocked_get_response))
    monkeypatch.setattr("saleor.app.installation_utils.send_app_token", Mock())

    app_installation.permissions.set(
        [permission_manage_products, permission_manage_orders]
    )

    # when
    app = install_app(app_installation, activate=True)

    # then
    assert App.objects.get().id == app.id
    app_extension = app.extensions.get()

    assert app_extension.label == label
    assert app_extension.url == url
    assert app_extension.mount == AppExtensionMount.PRODUCT_OVERVIEW_CREATE
    assert app_extension.target == AppExtensionTarget.POPUP
    assert list(app_extension.permissions.all()) == [permission_manage_products]


@pytest.mark.parametrize(
    "app_permissions, extension_permissions",
    [
        ([], ["MANAGE_PRODUCTS"]),
        (["MANAGE_PRODUCTS"], ["MANAGE_PRODUCTS", "MANAGE_APPS"]),
    ],
)
def test_install_app_extension_permission_out_of_scope(
    app_permissions, extension_permissions, app_manifest, app_installation, monkeypatch
):
    # given
    label = "Create product with app"
    url = "http://127.0.0.1:8080/app-extension"
    view = "PRODUCT"
    type = "OVERVIEW"
    target = "CREATE"
    app_manifest["permissions"] = app_permissions
    app_manifest["extensions"] = [
        {
            "label": label,
            "url": url,
            "view": view,
            "type": type,
            "target": target,
            "permissions": extension_permissions,
        }
    ]
    mocked_get_response = Mock()
    mocked_get_response.json.return_value = app_manifest

    monkeypatch.setattr(requests, "get", Mock(return_value=mocked_get_response))
    monkeypatch.setattr("saleor.app.installation_utils.send_app_token", Mock())

    # when & then
    with pytest.raises(ValidationError):
        install_app(app_installation, activate=True)


@pytest.mark.parametrize(
    "url",
    [
        "http:/127.0.0.1:8080/app",
        "127.0.0.1:8080/app",
        "",
        "/app",
        "www.example.com/app",
    ],
)
def test_install_app_extension_incorrect_url(
    url, app_manifest, app_installation, monkeypatch
):
    # given
    app_manifest["permissions"] = ["MANAGE_PRODUCTS"]
    app_manifest["extensions"] = [
        {
            "url": url,
            "label": "Create product with app",
            "view": "PRODUCT",
            "type": "OVERVIEW",
            "target": "CREATE",
            "permissions": ["MANAGE_PRODUCTS"],
        }
    ]
    mocked_get_response = Mock()
    mocked_get_response.json.return_value = app_manifest

    monkeypatch.setattr(requests, "get", Mock(return_value=mocked_get_response))
    monkeypatch.setattr("saleor.app.installation_utils.send_app_token", Mock())

    # when & then
    with pytest.raises(ValidationError):
        install_app(app_installation, activate=True)


def test_install_app_extension_ivalid_permission(
    app_manifest, app_installation, monkeypatch
):
    # given
    label = "Create product with app"
    url = "http://127.0.0.1:8080/app-extension"
    view = "PRODUCT"
    type = "OVERVIEW"
    target = "CREATE"
    app_manifest["permissions"] = ["MANAGE_PRODUCTS"]
    app_manifest["extensions"] = [
        {
            "label": label,
            "url": url,
            "view": view,
            "type": type,
            "target": target,
            "permissions": ["INVALID_PERM"],
        }
    ]
    mocked_get_response = Mock()
    mocked_get_response.json.return_value = app_manifest

    monkeypatch.setattr(requests, "get", Mock(return_value=mocked_get_response))
    monkeypatch.setattr("saleor.app.installation_utils.send_app_token", Mock())

    # when & then
    with pytest.raises(ValidationError):
        install_app(app_installation, activate=True)


@pytest.mark.parametrize(
    "incorrect_field",
    [
        "view",
        "type",
        "target",
    ],
)
def test_install_app_extension_incorrect_values(
    incorrect_field, app_manifest, app_installation, monkeypatch
):
    # given
    label = "Create product with app"
    url = "http://127.0.0.1:8080/app-extension"
    view = "PRODUCT"
    type = "OVERVIEW"
    target = "CREATE"
    app_manifest["permissions"] = []
    app_manifest["extensions"] = [
        {
            "label": label,
            "url": url,
            "view": view,
            "type": type,
            "target": target,
            "permissions": ["MANAGE_PRODUCTS"],
        }
    ]
    app_manifest["extensions"][0][incorrect_field] = "wrong-value"
    mocked_get_response = Mock()
    mocked_get_response.json.return_value = app_manifest

    monkeypatch.setattr(requests, "get", Mock(return_value=mocked_get_response))
    monkeypatch.setattr("saleor.app.installation_utils.send_app_token", Mock())

    # when & then
    with pytest.raises(ValidationError):
        install_app(app_installation, activate=True)
