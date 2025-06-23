"""Script to combine all the institution-specific access-rights masterfiles into one Corpus Access Catalogue."""

import os
import json
import copy
import fire
from harvesters.utils import transform_value, BITMAP_KEYS

MASTER_AR_DIR = "data/access_rights_masterfiles"
AR_FILES_TO_EXCLUDE = ["debug", "catalogue", "institutions", "bitmap"]

CATALOGUE_RULES = {
    "rights_holder_id": {"rename_key_to": "data_partner_institution"},
    "title_alias": {"rename_key_to": "media_alias"},
    "full_title": {"rename_key_to": "media_title"},
    "start_year": {"rename_key_to": "time_period"},
    "end_year": {"copy_value_from_field": "end_year"},
    "media_type": {"rename_key_to": "source_type"},
    "medium": {"rename_key_to": "source_medium"},
    "content_and_metadata": {"remove_key": ""},
    "copyright_status": {"rename_key_to": "copyright_or_copyright_status"},
    "explore_req_status": {"remove_key": ""},
    "get_transcript_req_status": {"remove_key": ""},
    "get_facsimile_req_status": {"remove_key": ""},
    "allowed_use_archive_only": {"rename_key_to": "permitted_use"},
    "content_bitmaps": {"remove_key": ""},
    "rights_statement_explore": {"remove_key": ""},
    "rights_statement_get_tr": {"remove_key": ""},
    "rights_statement_get_img": {"remove_key": ""},
}

MIN_PLAN_CAT_KEYS = {
    "explore": "minimum_user_plan_required_to_explore_in_the_webapp",
    "get_tr": "minimum_user_plan_required_to_export_transcripts",
    "get_img": "minimum_user_plan_required_to_export_illustration",
}

REQ_STATUS_AR_KEYS = {
    "explore": "explore_req_status",
    "get_tr": "get_transcript_req_status",
    "get_img": "get_facsimile_req_status",
}

RIGHTS_AR_KEYS = {
    "explore": "rights_statement_explore",
    "get_tr": "rights_statement_get_tr",
    "get_img": "rights_statement_get_img",
}


def list_ar_masterfiles(
    ar_dir: str, to_exclude: list[str] = AR_FILES_TO_EXCLUDE
) -> dict[str, str]:
    ar_master_files = {}
    for ar_master_file in os.listdir(ar_dir):
        if all(word not in ar_master_file for word in to_exclude):
            partner = ar_master_file.split(".")[1]
            ar_master_files[partner] = os.path.join(ar_dir, ar_master_file)

    print(f"Found access rights masterfiles: {ar_master_files}")
    return ar_master_files


def min_plan_from_rest(
    action_key: str, ar_dict: dict[str, str], req_status_ar_key: str, rights_ar_key: str
) -> str:
    # define the minimum user plan for a given action
    # based on the required status and rights statement
    print(
        f"Defining the minimum user plan for an action based on required status and rights:"
        f"  action_key: {action_key}, \n"
        f"  req_status_ar_key: {req_status_ar_key},\n"
        f"  ar_dict[req_status_ar_key]: {ar_dict[req_status_ar_key]}"
    )
    match ar_dict[req_status_ar_key]:
        case "No restriction (all registered users allowed)":
            if "Public Domain" in ar_dict[rights_ar_key] and action_key == "explore":
                # public domain and no restriction means gests can access it, but only explore
                return "Guest User Plan"
            # to access via the API or if the content is copyrighted, the user must be registered
            return "Basic User Plan"
        case "":
            # This is the same case as above
            if "Public Domain" in ar_dict[rights_ar_key] and action_key == "explore":
                return "Guest User Plan"
            return "Basic User Plan"
        case "Educational users at least":
            return "Student User Plan"
        case "Academic users at least":
            return "Academic User Plan"
        case "Educational users at least OR Archive members":
            # whenever archive members are allowed, we need to consider their allowed status too.
            if "Personal" in ar_dict["allowed_use_archive_only"]:
                # if personal use is allowed for archive members:
                # - basic plan can suffice if user is member of the special archive
                # - if user is not user of special archive, they need the Student Plan at least.
                return "Basic User Plan"
            # otherwise, any user with Student or academic plan are allowed.
            return "Student User Plan"
        case "Academic users at least OR Archive members":
            # same logic as above with one additional restriction level
            if "Personal" in ar_dict["allowed_use_archive_only"]:
                return "Basic User Plan"
            if "Educational" in ar_dict["allowed_use_archive_only"]:
                return "Student User Plan"
            return "Academic User Plan"
        case "Only Archive members":
            # if only archive members are allowed, minimum user plan is defined by the allowed uses.
            if "Personal" in ar_dict["allowed_use_archive_only"]:
                return "Basic User Plan"
            if "Educational" in ar_dict["allowed_use_archive_only"]:
                return "Student User Plan"
            return "Academic User Plan"
        case "Forbidden":
            return "Not Possible"


def remap_keys_and_values(
    ar_dict: dict[str, str],
    min_plan_cat_keys: dict[str, str] = MIN_PLAN_CAT_KEYS,
    req_status_ar_keys: dict[str, str] = REQ_STATUS_AR_KEYS,
    rights_ar_keys: dict[str, str] = RIGHTS_AR_KEYS,
) -> dict[str, str]:

    catalogue_entry = transform_value(copy.deepcopy(ar_dict), CATALOGUE_RULES)
    catalogue_entry["time_period"] = (
        f"{catalogue_entry['time_period']}-{catalogue_entry['end_year']}"
    )
    del catalogue_entry["end_year"]

    for key, min_plan_catalogue in min_plan_cat_keys.items():
        catalogue_entry[min_plan_catalogue] = min_plan_from_rest(
            key, ar_dict, req_status_ar_keys[key], rights_ar_keys[key]
        )

    if catalogue_entry["permitted_use"] == "":
        if catalogue_entry["minimum_user_plan_required_to_explore_in_the_webapp"] in [
            "Guest User Plan",
            "Basic User Plan",
        ]:
            catalogue_entry["permitted_use"] = "Personal, Research and Educational"
        elif (
            "Student" in catalogue_entry["minimum_user_plan_required_to_explore_in_the_webapp"]
        ):
            catalogue_entry["permitted_use"] = "Research and Educational"
        else:
            catalogue_entry["permitted_use"] = "Research"

    catalogue_entry["partner_bitmap_index"] = BITMAP_KEYS.index(
        catalogue_entry["data_partner_institution"]
    )

    return catalogue_entry


def to_catalogue_entry(access_rights: dict[str, dict]) -> tuple[list, dict]:
    catalogue = {}
    catalogue_list = []
    for title, period_dict in access_rights.items():
        print(f"\n{title}:")
        catalogue[title] = {}
        for period, ar_dict in period_dict.items():
            print(f"- {period}:")
            catalogue[title][period] = remap_keys_and_values(ar_dict)
            catalogue_list.append(catalogue[title][period])
            print(f"ar_dict: {ar_dict} \ncatalogue: {catalogue[title][period]}")

    return catalogue_list, catalogue


def main(ar_dir_path: str = MASTER_AR_DIR):
    """Based on the access right information fetched from the Gsheets, create the
    access rights masterfile for a given institution; where each period associated
    with a specific copyright domain has its own content bitmaps and human-readable
    statement to be displayed on the interface.
    """
    print(f"access rights masterfiles dir path: {ar_dir_path}")

    ar_master_files = list_ar_masterfiles(ar_dir_path)

    access_rights_contents = {}
    full_catalogue = []
    for partner, file_path in ar_master_files.items():
        print(f"\n\n___________{partner.upper()}_________:")
        with open(file_path, "r", encoding="utf-8") as file:
            fetched_ar = json.load(file)

        tranformed_ar_list, tranformed_ar = to_catalogue_entry(fetched_ar)

        access_rights_contents[partner.upper()] = tranformed_ar
        full_catalogue.extend(tranformed_ar_list)

    catalogue_path = os.path.join(ar_dir_path, "corpus_access_catalogue.json")

    msg = f"Writing the generated corpus access catalogue to disk: {catalogue_path}"
    print(msg)

    with open(catalogue_path, "w", encoding="utf-8") as fout:
        json.dump(full_catalogue, fout, indent=4)


if __name__ == "__main__":
    fire.Fire(main)
