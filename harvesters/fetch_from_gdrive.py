import fire
import re
import gspread
import random
import json

SPLIT_PATTERN = r"\s*,\s*"
LANG_SPLIT_PATTERN = r"\s* \s*"

METADATA_RULES = {
    "acronym": {  # to remove ?
        "copy_value_from_field": "newspaper_acronym",
    },
    "bibliographic_record_link": {
        "rename_key_to": "bib_record_link",
    },
    "bibliographic_record_text": {
        "rename_key_to": "bib_record_text",
    },
    "date_of_first_issue_in_the_interface": {
        "rename_key_to": "first_issuedate_interface",
    },
    "date_of_last_issue_in_the_interface": {
        "rename_key_to": "last_issuedate_interface",
    },
    "date_of_first_publication": {
        "rename_key_to": "newspaper_start_year",
    },
    "date_of_last_publication": {
        "rename_key_to": "newspaper_end_year",
    },
    "partner_id": {
        "rename_key_to": "partner_uid",
    },
    "known_lang": {
        "rename_key_to": "languages",
        "split_values_by_re": LANG_SPLIT_PATTERN,
    },
    "largest_geographic_outreach": {
        "rename_key_to": "geographic_outreach",
    },
    "local_geographical_area": {
        "rename_key_to": "geographic_area",
    },
    "newspaper_title": {
        "rename_key_to": "title",
    },
    "periodicity": {
        "rename_key_to": "latest_periodicity",
    },
    "change_in_periodicity": {
        "rename_key_to": "change_periodicity",
    },
    "resource_holder_names": {
        "split_values_by_re": SPLIT_PATTERN,
    },
    "resource_holder_links": {
        "split_values_by_re": SPLIT_PATTERN,
    },
    "resource_holder_logos": {
        "split_values_by_re": SPLIT_PATTERN,
    },
    "ocr_format_before_ingestion_in_impresso": {
        "rename_key_to": "ocr_format",
    },
    "uid": {
        "copy_value_from_field": "newspaper_acronym",
    },
}

ACCESS_RIGHTS_RULES = {
    "alias": {"rename_key_to": "title_alias"},
    "title": {"rename_key_to": "full_title"},
    "included_time_period_start_date_1st_january_to_be_filled_only_if_it_applies": {
        "rename_key_to": "start_year"
    },
    "included_time_period_end_date_31st_december_to_be_filled_only_if_it_applies": {
        "rename_key_to": "end_year"
    },
    "do_you_provide_only_metadata_and_not_also_content": {
        "rename_key_to": "metadata_only"
    },
    "what_is_the_copyright_status_of_this_title_for_the_given_time_period_if_public_domain_no_need_to_fill_in_the_other_columns_whose_values_are_then_understood_as_yes": {
        "rename_key_to": "copyright_status"
    },
    "to_which_registered_user_statuses_do_you_want_to_restrict_the_explore_action_on_this_title": {
        "rename_key_to": "explore_status"
    },
    "to_which_registered_user_statuses_do_you_want_to_restrict_the_get_action_on_transcripts_of_this_title_registered_user_statuses_are_impresso_account_creation_tou_student_check_of_status_at_account_creation_academic_check_of_affiliation_at_account_creation": {
        "rename_key_to": "get_transcript_status"
    },
    "to_which_registered_user_statuses_do_you_want_to_restrict_the_get_action_on_images_any_part_of_the_facsimile_of_this_title_registered_user_statuses_are_impresso_account_creation_tou_student_check_of_status_at_account_creation_academic_check_of_affiliation_at_account_creation": {
        "rename_key_to": "get_facsimile_status"
    },
    "for_which_statuses_do_you_want_to_validate_the_user_account_yourself": {
        "rename_key_to": "status_to_validate"
    },
}


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


def transform_value(d: dict, is_metadata: bool = True) -> dict:
    """
    Change the value of a key in a dictionary.

    Args:
      d (dict): Input dictionary.
      key (str): Key to change.
      value (str): New value for the key.

    Returns:
      dict: Dictionary with the updated key value.
    """
    transformed = {}

    for key in d.keys():
        slugified_key = util_slugify(key)
        transformed[slugified_key] = d[key]

    # depending on the data to fetch, different rules should be applied.
    rules = METADATA_RULES if is_metadata else ACCESS_RIGHTS_RULES

    for key_with_rule, rule in rules.items():
        if "copy_value_from_field" in rule:
            transformed[key_with_rule] = transformed[rule["copy_value_from_field"]]
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

    return transformed


def download(
    spreadsheet_id: str,  # Use spreadsheet id instead of URL
    worksheet_name: str = "impresso1-collection",  # Default worksheet name
    credentials_path: str = "credentials.json",  # Default credentials path
    output_file: str = "data.json",  # Default output filename
    is_metadata: bool = False,  # Default type of data to fetch
) -> None:
    """
    Downloads data from a specified Google Sheet and saves it as a JSON file.

    Args:
      spreadsheet_id (str): spreadsheet_id of the Google Sheet
      worksheet_name (str): Name of the worksheet to download  (default: Sheet1).
      credentials_path (str): Path to the credentials JSON file  (default: credentials.json).
      output_file (str): Name of the output JSON file (default: data.json).
    """
    print("Downloading data from Google Sheet... 📥")
    print(f"spreadsheet_id: {spreadsheet_id}")
    print(f"worksheet_name: {worksheet_name}")
    print(f"credentials_path: {credentials_path}")
    print(f"output_file: {output_file}")
    print(f"is_metadata: {is_metadata}")
    # Initialize gspread client
    gc = gspread.service_account(filename=credentials_path)

    # Open spreadsheet using URL
    sheet = gc.open_by_key(spreadsheet_id)
    worksheet_list = sheet.worksheets()

    if worksheet_name not in [worksheet.title for worksheet in worksheet_list]:
        print(
            f"Worksheet {worksheet_name} not found in the spreadsheet. Available sheets:"
        )
        print(worksheet_list)
        return
    # Open worksheet by name
    worksheet = sheet.worksheet(worksheet_name)

    # Get worksheet data
    values = worksheet.get_all_records(head=1 if is_metadata else 2)

    # convert is_metadata to an array for the map
    is_metadata = [is_metadata] * len(values)
    # use transform_records as a mapper function
    transformed_values = list(map(transform_value, values, is_metadata))

    # get random index for the values list
    idx = random.randint(0, len(transformed_values) - 1)
    print(f"Random value: {json.dumps(transformed_values[idx],indent=2)}")

    # Write data to JSON file
    with open(output_file, "w", encoding="utf-8") as outfile:
        json.dump(transformed_values, outfile, indent=2)


if __name__ == "__main__":
    fire.Fire(download)
