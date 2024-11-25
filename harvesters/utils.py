"""Small utilities module for the fetching and processing of the metadata and access rights.
"""

import re


def util_slugify(text: str) -> str:
    """
    Converts a string to a slug by replacing spaces with underscores and converting to lowercase.

    Args:
      text (str): Input string to slugify.

    Returns:
      str: Slugified string.
    """
    s = text.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_-]+", "_", s)
    s = re.sub(r"(^-+)|(-+$)", "", s)
    return s


def transform_value(d: dict, rules: dict[str, dict]) -> dict:
    """
    Change the value of a key in a dictionary.

    Args:
      d (dict): Input dictionary.
      rules (dict[str, dict]): Column/value transformation rules.

    Returns:
      dict: Dictionary with the updated key value.
    """
    transformed = {}

    for key in d.keys():
        slugified_key = util_slugify(key)
        transformed[slugified_key] = d[key]

    for key_with_rule, rule in rules.items():
        if "copy_value_from_field" in rule:
            val = transformed[rule["copy_value_from_field"]]
            del transformed[key_with_rule]
            transformed[key_with_rule] = val
        if "split_values_by_re" in rule:
            transformed[key_with_rule] = [
                x
                for x in re.split(
                    rule["split_values_by_re"], transformed[key_with_rule]
                )
                if x.strip()
            ]
        if "rename_key_to" in rule:
            transformed[rule["rename_key_to"]] = transformed[key_with_rule]
            del transformed[key_with_rule]
        if "remove_key" in rule:
            del transformed[key_with_rule]

    return transformed
