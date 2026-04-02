"""Python script downloading a given google drive spreadsheet into a json file."""

import re
import random
import json
import gspread
import fire

SPLIT_PATTERN = r"\s*,\s*"
TITLES_SPLIT_PATTERN = r"(?<=\))\s*; \s*"
LANG_SPLIT_PATTERN = r"\s* \s*"
NUM_DIGITS_PROV_ID = {"BL": 7}

METADATA_RULES = {
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
        "rename_key_to": "media_start_year",
    },
    "date_of_last_publication": {
        "rename_key_to": "media_end_year",
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
    "media_title": {
        "rename_key_to": "title",
    },
    "source_type": {
        "rename_key_to": "src_type",
    },
    "source_medium": {
        "rename_key_to": "src_medium",
    },
    "periodicity": {
        "rename_key_to": "latest_periodicity",
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
    "other_titles_semicolon_separated_with_dates": {
        "split_values_by_re": TITLES_SPLIT_PATTERN,
    },
    "ocr_format_before_ingestion_in_impresso": {
        "rename_key_to": "ocr_format",
    },
    "uid": {
        "copy_value_from_field": "media_alias",
    },
    "provenance_id": {
        "z_fill_to_size_if_int": NUM_DIGITS_PROV_ID,
    },
    "free_text_description": {"rename_key_to": "description"},
    "dhs_link_without_the_date_section_of_the_url": {"rename_key_to": "dhs_link"},
    "wikipedia_page": {"rename_key_to": "wikipedia"},
    "additional_sources_comma_separated_links": {"rename_key_to": "additional_sources"},
}

ACCESS_RIGHTS_RULES = {
    "partner_id": {"rename_key_to": "rights_holder_id"},
    "alias": {"rename_key_to": "title_alias"},
    "title": {"rename_key_to": "full_title"},
    "included_time_period_start_date_1st_january_to_be_filled_only_if_it_applies": {
        "rename_key_to": "start_year"
    },
    "included_time_period_end_date_31st_december_to_be_filled_only_if_it_applies": {
        "rename_key_to": "end_year"
    },
    "media_type": {"copy_value_from_field": "media_type"},
    "medium": {"copy_value_from_field": "medium"},
    "do_you_provide_content_and_not_only_metadata": {"rename_key_to": "content_and_metadata"},
    "what_is_the_copyright_status_of_the_content_of_this_title_for_the_given_time_period_this_information_will_be_displayed_alongside_the_data_for_all_values_except_protected_domain_in_copyrigth_no_need_to_fill_the_columns_i_j_k_whose_values_are_then_no_restriction_please_contact_us_if_not_ok": {
        "rename_key_to": "copyright_status"
    },
    "which_user_status_or_archive_membership_is_sufficient_to_execute_the_explore_action_on_this_title_sufficient_condition": {
        "rename_key_to": "explore_req_status"
    },
    "which_user_status_or_archive_membership_is_sufficient_to_execute_the_get_action_on_transcripts_of_this_title_sufficient_condition": {
        "rename_key_to": "get_transcript_req_status"
    },
    "which_user_status_or_archive_membership_is_sufficient_to_execute_the_get_action_on_images_any_part_of_the_facsimile_of_this_title_sufficient_condition": {
        "rename_key_to": "get_facsimile_req_status"
    },
    "to_be_filled_only_if_the_choices_made_for_i_j_and_k_is_only_archive_members_which_uses_of_the_data_are_permitted_for_archive_members_permitted_uses_in_other_cases_result_from_the_user_status_and_are_defined_in_dsa_29": {
        "rename_key_to": "allowed_use_archive_only"
    },
}

MODELS_CHEATSHEET_RULES = {
    "release": {"copy_value_from_field": "release"},
    "model_run_mysql_id": {"copy_value_from_field": "model_run_mysql_id"},
    "model_internal_alias_shorten_version_of_run_id_used_in_solr_and_in_json_files": {
        "rename_key_to": "internal_alias"
    },
    "task_name_full_human_readable": {"rename_key_to": "full_task_name"},
    "lang_used_in_model_id": {"rename_key_to": "lang"},
    "processing_label_used_in_s3_path_and_file_names": {"rename_key_to": "process_label"},
    "processing_subtype_label_used_in_s3_path": {"rename_key_to": "process_subtype_label"},
    "model_alias_internal_process_use": {"rename_key_to": "model_alias"},
    "full_model_name_base_model": {"rename_key_to": "full_model_name"},
    "model_version_base_model": {"remove_key": ""},
    "model_specificity_we_could_leave_this_out_of_s3_path_and_keep_it_only_here": {
        "remove_key": ""
    },
    "model_id_task_subtask_model_specifity_model_version_lang_": {"rename_key_to": "model_id"},
    "huggingface_link": {"copy_value_from_field": "huggingface_link"},
    "run_id_processing_label_model_id_run_version_": {"rename_key_to": "run_id"},
    "run_version": {"copy_value_from_field": "run_version"},
    "s3_path_of_processed_data_path_s3_bucket_processing_label_processing_subtype_label_component_run_id_processing_step_provider_alias_media_alias_file_stem_jsonlbz2_": {
        "remove_key": ""
    },
    "s3_partition_of_output_data_manifest_location": {"rename_key_to": "processed_data_s3_path"},
    "computed_manifest": {"copy_value_from_field": "computed_manifest"},
    "comment": {"remove_key": ""},
}

RECORDS_HEAD = {"metadata": 1, "access_rights": 2, "cheatsheet": 2}
RULES = {
    "metadata": METADATA_RULES,
    "access_rights": ACCESS_RIGHTS_RULES,
    "cheatsheet": MODELS_CHEATSHEET_RULES,
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


def transform_value(d: dict, gsheet_type: str) -> dict:
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
    rules = RULES[gsheet_type]

    for key_with_rule, rule in rules.items():
        if "copy_value_from_field" in rule:
            val = transformed[rule["copy_value_from_field"]]
            if key_with_rule in transformed:
                del transformed[key_with_rule]
            transformed[key_with_rule] = val
        if "split_values_by_re" in rule:
            transformed[key_with_rule] = [
                x
                for x in re.split(rule["split_values_by_re"], transformed[key_with_rule])
                if x.strip()
            ]
        if "rename_key_to" in rule:
            transformed[rule["rename_key_to"]] = transformed[key_with_rule]
            del transformed[key_with_rule]
        if "z_fill_to_size_if_int" in rule:
            # sometimes provenance IDs have leading 0s
            if isinstance(transformed[key_with_rule], int):
                num_digits = rule["z_fill_to_size_if_int"][transformed["partner_uid"]]
                val = transformed[key_with_rule]
                transformed[key_with_rule] = str.zfill(str(val), num_digits)

    return transformed


def has_ar_values_defined(ar_entry):
    defined = (
        ar_entry["title_alias"] != ""
        and ar_entry["rights_holder_id"] != ""
        and ar_entry["copyright_status"] != ""
    )
    if not defined:
        print(f"Warning! Missing values for access right entry - will be ignored: {ar_entry}")

    return defined


def has_metadata_values_defined(metadata_entry):
    defined = (
        metadata_entry["ingestion_batch"] != ""
        and metadata_entry["media_alias"] != ""
        and metadata_entry["partner_uid"] != ""
    )
    if not defined:
        print(f"Warning! Missing values for metadata entry - will be ignored: {metadata_entry}")

    return defined


def download(
    spreadsheet_id: str,  # Use spreadsheet id instead of URL
    worksheet_name: str = "impresso1-collection",  # Default worksheet name
    credentials_path: str = "credentials.json",  # Default credentials path
    output_file: str = "data.json",  # Default output filename
    gsheet_type: str = "access_rights",  # Default type of data to fetch
) -> None:
    """
    Downloads data from a specified Google Sheet and saves it as a JSON file.

    Args:
      spreadsheet_id (str): spreadsheet_id of the Google Sheet
      worksheet_name (str): Name of the worksheet to download  (default: Sheet1).
      credentials_path (str): Path to the credentials JSON file  (default: credentials.json).
      output_file (str): Name of the output JSON file (default: data.json).
      gsheet_type (str): Type of Googe Sheet to fetch, one of "metadata", "access_rights",
      "cheatsheet" (default: access_rights).
    """
    print("Downloading data from Google Sheet... 📥")
    print(f"spreadsheet_id: {spreadsheet_id}")
    print(f"worksheet_name: {worksheet_name}")
    print(f"credentials_path: {credentials_path}")
    print(f"output_file: {output_file}")
    print(f"gsheet_type: {gsheet_type}")

    # ensure that the type of gsheet to fetch is supported/implemented
    if gsheet_type not in RECORDS_HEAD.keys():
        msg = (
            f"The gsheet_type '{gsheet_type}' is not one of ['metadata', 'access_rights', 'cheatsheet'] "
            "Please provide a supported type of Gsheet."
        )
        raise NotImplementedError(msg)

    # Initialize gspread client
    gc = gspread.service_account(filename=credentials_path)

    # Open spreadsheet using URL
    sheet = gc.open_by_key(spreadsheet_id)
    worksheet_list = sheet.worksheets()

    if worksheet_name not in [worksheet.title for worksheet in worksheet_list]:
        print(f"Worksheet {worksheet_name} not found in the spreadsheet. Available sheets:")
        print(worksheet_list)
        return
    # Open worksheet by name
    worksheet = sheet.worksheet(worksheet_name)

    # Get worksheet data
    values = worksheet.get_all_records(head=RECORDS_HEAD[gsheet_type])

    # convert is_metadata to an array for the map
    gsheet_types = [gsheet_type] * len(values)
    # use transform_records as a mapper function
    transformed_values = list(map(transform_value, values, gsheet_types))

    if gsheet_type == "access_rights":
        # only keep entries where all necessary values are defined
        transformed_values = [v for v in transformed_values if has_ar_values_defined(v)]
    if gsheet_type == "metadata":
        # only keep entries where all necessary values are defined
        transformed_values = [v for v in transformed_values if has_metadata_values_defined(v)]

    # get random index for the values list
    idx = random.randint(0, len(transformed_values) - 1)
    print(f"Random value: {json.dumps(transformed_values[idx],indent=2)}")

    # Write data to JSON file
    with open(output_file, "w", encoding="utf-8") as outfile:
        json.dump(transformed_values, outfile, indent=2)


if __name__ == "__main__":
    fire.Fire(download)
