""" Python script converting the DSA access rights entries into collection Access Rights Masterfiles.

Usage:
    harvesters/access_rights/access_rights_masterfile.py --partner=<p> --data-dir=<dd> [--log-file=<logfile> --verbose]

Arguments:
    p  Partner institution for which to create the access rights masterfile
    dd  Path the the data directory inside this repository, where to find the `gdrive_access_rights` dir.
    logfile  Log file.

Options:
    -h --help
    --verbose  verbose mode
"""

import os
import json
from typing import Any
from collections import Counter

from docopt import docopt

BITMAP_KEYS = [
    "public",
    "impresso",
    "educational",
    "researcher",
    "",
    "SNL",
    "BNL",
    "BNF",
    "KBR",
    "KB",
    "BL",
    "ONB",
    "SBB",
    "SUB",
    "LeTemps",
    "NZZ",
    "INA",
    "RTS",
    "BBC",
    "ORF",
    "Rundfunk",
    "DR",
    "BCUL",
    "BCUF",
    "Migros",
    "PSNE",
    "Gruyere",
    "LLE",
    "LCE",
    "LES",
    "MVS",
    "FRN",
    "RM",
    "Syna",
    "Unia",
    "SWA",
    "SA",
    "BVCF",
    "BVU",
    "ArcInfo",
    "Swissinfo",
    "CNA",
    "FedGaz",
]

ACTION_COLUMNS = {
    "explore": "explore_req_status",
    "get_tr": "get_transcript_req_status",
    "get_img": "get_facsimile_req_status",
}

GDRIVE_AR_FILE = "gdrive_access_rights/gsheet_access_rights.{partner}.json"
MASTER_AR_FILE = "access_rights_masterfiles/access_rights.{partner}.json"


def allowed_status_to_bitmap(
    allowed_status: str, bitmap: list[str], partner_index: int
) -> list[str]:
    """Based on the user statuses allowed, define bitmap indices to set to 1.

    The bitmap is separated into two zones:
    - User allowed statuses - first 4 bits: all user statuses which are allowed
        access by defualt without needing specific validation by the archive.
    - Archive memberships - all following bits: bits each one corresponding to an
        archive, allowing to represent when a user can request to access the content
        to the archive specifically, if its user status does not allow it by default.

    Some contents can be accessible by simple status OR by archive membership. Hence,
    the final bitmap can have up to 2 non-zero bits.
    A bitmap with only zero bits represents a forbidden action on the data.

    Args:
        allowed_status (str): User statuses which are allowed to access the data.
        bitmap (list[str]): Current bitmap, before setting new indices to 1.
        partner_index (int): Bitmap index corresponding to the partner in question.

    Returns:
        list[str]: Resulting content bitmap as list of strings.
    """
    # Based on the allowed statuses, identify which indices to set to 1
    match allowed_status:
        case "No restriction (all registered users allowed)":
            # start of bitmap: '0100'
            indices_to_set = [1]
        case "Educational users at least OR Archive members":
            # start of bitmap: '0010'
            indices_to_set = [2, partner_index]
        case "Educational users at least":
            # start of bitmap: '0010'
            indices_to_set = [2]
        case "Academic users at least OR Archive members":
            # start of bitmap: '0001'
            indices_to_set = [3, partner_index]
        case "Academic users at least":
            # start of bitmap: '0001'
            indices_to_set = [3]
        case "Only Archive members":
            # start of bitmap: '0000'
            indices_to_set = [partner_index]
        case "Forbidden":
            # start of bitmap: '0000'
            indices_to_set = []

    # set all selected indices to 1 (there can be 0, 1 or 2)
    for idx in indices_to_set:
        bitmap[idx] = "1"

    assert Counter(bitmap)["1"] in range(
        3
    ), "Content bitmaps should have at most two active bits!"

    return bitmap


def bitmap_bytes_to_str(bytes_bitmap: bytes) -> str:
    """Convert a bitmap in bytes format to string.

    Args:
        bytes_bitmap (bytes): Bitmap to convert.

    Returns:
        str: Resulting string bitmap.
    """
    as_str = [str(x) for x in bytes_bitmap]
    return "".join(as_str)


def bitmap_str_to_bytes(str_bitmap: str) -> bytes:
    """Convert a bitmap in string format to bytes.

    Args:
        str_bitmap (str): Bitmpa to convert.

    Returns:
        bytes: Resulting bytes bitmap
    """
    as_int = [int(x) for x in str_bitmap]
    return bytes(as_int)


def entry_to_bitmaps(
    ar_entry: dict[str, Any],
    bitmap_keys: list[str],
    action_columns: dict[str, str],
    as_str: bool = True,
) -> dict[str, bytes] | dict[str, str]:
    """Construct the content bitmaps for an access right entry from the gsheet.

    Each media title and period will be assigned 3 bitmpas corresponding to the
    three possible actions on the content: explore, get-transcript, get-facsimile.

    Based on the content's copyright status and the institution's allowed accesses/uses,
    the bitmaps are created.
    In the cases where the `copyright_status` is "Public Domain", "Protected Domain:
    Copyright undetermined", "Protected Domain: In copyright - Unknown rightsholder",
    "Protected Domain: In copyright - EU Orphean" or "Protected Domain: No Known
    Copyright", all actions are allowed for personal, educational and research uses,
    and registered users. When the copyright status is "Protected Domain: In copyright",
    the insitutions is free to restrict which users or uses are permitted on the data.

    Args:
        ar_entry (dict[str, Any]): Access right entry from the google sheets.
        bitmap_keys (list[str]): Mapping of each bitmap index to the value it encodes.
        action_columns (dict[str, str]): Mapping from actions to the gsheet column.
        as_str (bool, optional): Whether the created bitmaps should be returned as
            string (True) or bytes (False). Defaults to True.

    Returns:
        dict[str, bytes] | dict[str, str]: _description_
    """
    no_restr_ar = "No restriction (all registered users allowed)"
    bitmaps = {"explore": ["0"] * 64, "get_tr": ["0"] * 64, "get_img": ["0"] * 64}
    # if the title is public domain, only the first bit should be set to 1
    if "Public Domain" in ar_entry["copyright_status"]:
        for bm in bitmaps.values():
            bm[0] = "1"
    # if it's not public, each bitmap changes based on the various columns
    else:
        # undetermined, unknown or orphan copyright don't have restrictions
        if ar_entry["copyright_status"] not in "Protected Domain: In copyright":
            allowed_status = no_restr_ar
        else:
            allowed_status = None
        # for each type of bitmap, check the value of the column and modify the bitmap accordingly
        for bm_key, ar_key in action_columns.items():
            if allowed_status is not None and ar_entry[ar_key] not in [no_restr_ar, ""]:
                print(
                    f"Warning! For {ar_entry['title_alias']}: "
                    f"copyright_status is '{ar_entry["copyright_status"]}' "
                    f"but the allowed user status for the {ar_key} operation is '{ar_entry[ar_key]}'! "
                    f"This value will be overwritten to '{no_restr_ar}'."
                )

            bitmaps[bm_key] = allowed_status_to_bitmap(
                ar_entry[ar_key] if allowed_status is None else allowed_status,
                bitmaps[bm_key],
                bitmap_keys.index(ar_entry["rights_holder_id"]),
            )

    str_bitmaps = {k: "".join(val) for k, val in bitmaps.items()}

    # return bitmaps as strings
    if as_str:
        return str_bitmaps
    # retrun bitmaps as bytes
    return {k: bitmap_str_to_bytes(val) for k, val in bitmaps.items()}


def bitwise_and(a: str | bytes, b: str | bytes) -> str | bytes:
    """Perform a bitwise AND between two btimaps of the same format.

    Args:
        a (str | bytes): Bitmap to compare, as string or bytes.
        b (str | bytes): Bitmap to compare, as string or bytes.

    Raises:
        AttributeError: The two bitmaps were not of the same type or not str or bytes.

    Returns:
        str | bytes: The resulting bitmap in the same type as the inputs.
    """
    assert len(a) == len(b), "The two bitmaps must be of the same size!"
    # first case: bytes
    if isinstance(a, bytes) and isinstance(b, bytes):
        return bytes([a[x] & b[x] for x in range(len(a))])
    # second case: strings
    elif isinstance(a, str) and isinstance(b, str):
        return "".join([str(int(a[x] == "1" and b[x] == "1")) for x in range(len(a))])
    else:
        m = "The AND operation is not supported for this type of data, only str or bytes!"
        print(m)
        raise AttributeError(m)


def statement_from_status(allowed_status: str, allowed_used_archive_only: str) -> str:
    """Return the allowed use(s) for a content based on the user statuses.

    Args:
        allowed_status (str): User statuses which are allowd to access a given content.
        allowed_used_archive_only (str): Allowed uses for the data, when only archive
            members are allowed access: `allowed_status`='Only Archive members'.

    Raises:
        AttributeError: The allowed user status is not part of the valid values.

    Returns:
        str: The allowed uses to be then displayed on the interface.
    """
    match allowed_status:
        case "No restriction (all registered users allowed)":
            return "Personal, Research and Educational use"
        case "Educational users at least OR Archive members":
            return "Research and Educational use"
        case "Educational users at least":
            return "Research and Educational use"
        case "Academic users at least OR Archive members":
            return "Research"
        case "Academic users at least":
            return "Research use"
        case "Only Archive members":
            if allowed_used_archive_only != "":
                return f"{allowed_used_archive_only} use"

            # if only archive members are allowed, the alloed uses need to be specified.
            m = f"When allowing only archive members, the allowed uses should be provided ({allowed_used_archive_only})!"
            print(m)
            raise AttributeError(m)
        case "Forbidden":
            return "Operation not permitted"


def entry_to_statement(entry: dict[str, Any], period: str, action_status: str) -> str:
    """Create the human-readable copyright statement from a given title and period.

    The returned statement is of the form:
        "[Copyright Domain] ([start year]-[end year]) - [allowed uses] use"

    Args:
        entry (dict[str, Any]): Access right entry directly fetched from the Gsheet.
        period (str): Period for which the statement applies.

    Raises:
        AttributeError: The provided copyright status is an empty string.

    Returns:
        str: Human-readable copyright statement for the interface.
    """
    if entry["copyright_status"] == "Public Domain":
        return f"Public Domain ({period})"
    if entry["copyright_status"] == "Protected Domain: In copyright":
        # the human readable rights are only for the interface: explore
        stmt = statement_from_status(
            entry[action_status], entry["allowed_use_archive_only"]
        )
        return f"Protected ({period}) - {stmt}"
    if entry["copyright_status"] == "":
        m = f"The copyright status was not provided for {entry['title_alias']}"
        print(m)
        raise AttributeError(m)
    # all other protected domain cases
    # TODO maybe change based on type of uses?
    return f"Protected ({period}) - Personal, Research and Educational use"


def main():
    """Based on the access right information fetched from the Gsheets, create the
    access rights masterfile for a given institution; where each period associated
    with a specific copyright domain has its own content bitmaps and human-readable
    statement to be displayed on the interface.
    """
    arguments = docopt(__doc__)
    partner = arguments["--partner"]
    data_dir_path = arguments["--data-dir"]
    print(f"partner: {partner}, data_dir_path: {data_dir_path}")

    masterfile = {}
    out_json_path = os.path.join(data_dir_path, MASTER_AR_FILE.format(partner=partner))
    gdrive_json_path = os.path.join(
        data_dir_path, GDRIVE_AR_FILE.format(partner=partner)
    )

    with open(gdrive_json_path, "r", encoding="utf-8") as file:
        fetched_ar = json.load(file)

    for entry in fetched_ar:
        if entry["rights_holder_id"] != "" and entry["title_alias"] != "":
            title = entry["title_alias"].strip()
            period = f"{entry['start_year']}-{entry['end_year']}"
            str_bitmaps = entry_to_bitmaps(entry, BITMAP_KEYS, ACTION_COLUMNS)

            # prepare the entry for the final masterfile
            del entry[""]
            entry["content_bitmaps"] = str_bitmaps
            entry["rights_statement_explore"] = entry_to_statement(
                entry, period, "explore_req_status"
            )
            entry["rights_statement_get_tr"] = entry_to_statement(
                entry, period, "get_transcript_req_status"
            )
            entry["rights_statement_get_img"] = entry_to_statement(
                entry, period, "get_facsimile_req_status"
            )

            if title in masterfile:
                if period in masterfile[title]:
                    print(
                        f"{title} ({period}): This period had already been defined for this title!"
                    )
                else:
                    masterfile[title][period] = entry
            else:
                masterfile[title] = {period: entry}
        else:
            print("Missing some key information, skipping ", entry)

    with open(out_json_path, "w", encoding="utf-8") as file:
        file.write(json.dumps(masterfile, indent=4))


if __name__ == "__main__":
    main()
