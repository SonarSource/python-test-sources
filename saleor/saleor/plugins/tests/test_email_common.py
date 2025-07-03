from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError

from saleor.plugins.email_common import (
    DEFAULT_EMAIL_CONFIGURATION,
    validate_default_email_configuration,
)
from saleor.plugins.error_codes import PluginErrorCode


@pytest.mark.parametrize(
    "email",
    (
        "this_is_not_an_email",
        "@",
        ".@.test",
        "almost_correct_email@",
    ),
)
def test_validate_default_email_configuration_bad_email(
    email, plugin_configuration, email_configuration
):
    email_configuration["sender_address"] = email

    with pytest.raises(ValidationError) as e:
        validate_default_email_configuration(plugin_configuration, email_configuration)

    assert "sender_address" in e.value.args[0]
    assert e.value.args[0]["sender_address"].code == PluginErrorCode.INVALID.value


@patch("saleor.plugins.email_common.validate_email_config")
def test_validate_default_email_configuration_correct_email(
    mock_email_config, plugin_configuration, email_configuration
):

    email_configuration["sender_address"] = "this_is@correct.email"
    validate_default_email_configuration(plugin_configuration, email_configuration)


@patch("saleor.plugins.email_common.validate_email_config")
def test_validate_default_email_configuration_backend_raises(
    validate_email_config_mock, plugin_configuration, email_configuration
):
    validate_email_config_mock.side_effect = Exception("[Errno 61] Connection refused")
    email_configuration["sender_address"] = "this_is@correct.email"

    with pytest.raises(ValidationError) as e:
        validate_default_email_configuration(plugin_configuration, email_configuration)

    expected_keys = [item["name"] for item in DEFAULT_EMAIL_CONFIGURATION]
    assert list(e.value.error_dict.keys()) == expected_keys

    for message in e.value.messages:
        assert message == (
            "Unable to connect to email backend."
            " Make sure that you provided correct values."
            " [Errno 61] Connection refused"
        )
