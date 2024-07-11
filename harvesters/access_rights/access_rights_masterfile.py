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
    "KBR",
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
    "SFA",
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
        case "Only Achive members":
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
    as_str = [str(x) for x in bytes_bitmap]
    return "".join(as_str)


def bitmap_str_to_bytes(str_bitmap: str) -> bytes:
    as_int = [int(x) for x in str_bitmap]
    return bytes(as_int)


def entry_to_bitmaps(
    ar_entry: dict[str, Any],
    bitmap_keys: list[str],
    action_columns: dict[str, str],
    as_str: bool = True,
) -> dict[str, bytes] | dict[str, str]:
    bitmaps = {"explore": ["0"] * 64, "get_tr": ["0"] * 64, "get_img": ["0"] * 64}
    # if the title is public domain, only the first bit should be set to 1
    if "Public Domain" in ar_entry["copyright_status"]:
        for bm in bitmaps.values():
            bm[0] = "1"
    # if it's not public, each bitmap changes based on the various columns
    else:
        # for each type of bitmap, check the value of the column and modify the bitmap accordingly
        for bm_key, ar_key in action_columns.items():
            bitmaps[bm_key] = allowed_status_to_bitmap(
                ar_entry[ar_key],
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
    assert len(a) == len(b), "The two bitmaps must be of the same size!"
    # first case: bytes
    if isinstance(a, bytes) and isinstance(b, bytes):
        return bytes([a[x] & b[x] for x in range(len(a))])
    # second case: strings
    elif isinstance(a, str) and isinstance(b, str):
        return [str(int(a[x] == "1" and b[x] == "1")) for x in range(len(a))]
    else:
        m = "The AND operation is not supported for this type of data, only str or bytes!"
        print(m)
        raise AttributeError(m)


def statement_from_status(allowed_status):
    match allowed_status:
        case "No restriction (all registered users allowed)":
            return "Personal, Research and Educational"
        case "Educational users at least OR Archive members":
            return "Research and Educational"
        case "Educational users at least":
            return "Research and Educational"
        case "Academic users at least OR Archive members":
            return "Research"
        case "Academic users at least":
            return "Research"
        case "Only Achive members":
            return "Research"
        case "Forbidden":
            return "No allowed"


def entry_to_statement(entry: dict[str, Any], period: str) -> str:
    if entry["copyright_status"] == "Public Domain":
        return f"Public Domain ({period})"
    if entry["copyright_status"] == "Protected Domain: In copyright":
        # the human readable rights are only for the interface: explore
        return f"Protected ({period}) - {statement_from_status(entry['explore_req_status'])} use"
    if entry["copyright_status"] == "":
        m = f"The copyright status was not provided for {entry['title_alias']}"
        print(m)
        raise AttributeError(m)
    else:
        # all other protected domain cases
        # TODO maybe change based on type of uses?
        return f"Protected ({period}) - Personal, Research and Educational use"


def main():

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
            title = entry["title_alias"]
            period = f"{entry['start_year']}-{entry['end_year']}"
            str_bitmaps = entry_to_bitmaps(entry, BITMAP_KEYS, ACTION_COLUMNS)

            # prepare the entry for the final masterfile
            del entry[""]
            entry["content_bitmaps"] = str_bitmaps
            entry["rights_statement"] = entry_to_statement(entry, period)

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
