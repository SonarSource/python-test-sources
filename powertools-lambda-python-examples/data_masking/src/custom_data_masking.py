from __future__ import annotations

from aws_lambda_powertools.utilities.data_masking import DataMasking
from aws_lambda_powertools.utilities.typing import LambdaContext

data_masker = DataMasking()


def lambda_handler(event: dict, context: LambdaContext) -> dict:
    data: dict = event.get("body", {})

    # Masking rules for each field
    masking_rules = {
        "email": {"regex_pattern": "(.)(.*)(@.*)", "mask_format": r"\1****\3"},
        "age": {"dynamic_mask": True},
        "address.zip": {"custom_mask": "xxx"},
        "$.other_address[?(@.postcode > 12000)]": {"custom_mask": "Masked"},
    }

    result = data_masker.erase(data, masking_rules=masking_rules)

    return result
