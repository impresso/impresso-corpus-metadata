"""Script to fetch the BNF metadata for all titles, and store it in a XML file.

Usage:
    bnf_metadata.py [--config=<c> --data-dir=<dd>]

Options:

--config=<c>  Path to the BNF config file with the ARK ids of each tite. 
              Defaults to "../config/api_config.bnf.json".
--data-dir=<dd>   Path to the output data directory, where the fetched metadata will be written. 
                  Defaults to "../../data/apis".
"""

import os
import logging
import json
from docopt import docopt
import requests
from bs4 import BeautifulSoup
import pymarc

logger = logging.getLogger(__name__)

# define constants & defaults
BNF_API_URI = "http://catalogue.bnf.fr/api/SRU?version=1.2&operation=searchRetrieve&query=(bib.ark%20any%20%22{query}%22)&recordSchema=intermarcXchange"
ARK_BASE = "ark:/12148"

# default values for the local paths
DATA_DIR = "../../data/apis"
CONFIG_FILE = "../config/api_config.bnf.json"


def main() -> None:
    """Query the BNF API for all titles in the config and write the result to disk."""
    arguments = docopt(__doc__)
    config_file = arguments["--config"] if arguments["--config"] else CONFIG_FILE
    data_dir = arguments["--data-dir"] if arguments["--data-dir"] else DATA_DIR

    bnf_marc_file = os.path.join(data_dir, "intermarc_metadata.bnf.xml")

    with open(config_file, mode="r", encoding="utf-8") as f_in:
        bnf_config = json.load(f_in)

    all_bnf_arks = {
        t: f"{ARK_BASE}/{ark_v}"
        for collection in bnf_config.values()
        for t, ark_v in collection.items()
    }

    # all the ark ids should be concatenated for the query
    arks_as_str = " ".join(all_bnf_arks.values())
    # format the query URI with all the arks
    full_bnf_query_uri = BNF_API_URI.format(query=arks_as_str)

    resp_all = requests.get(full_bnf_query_uri, timeout=60)
    # extract the response's contents as a beautifulsoup object
    all_contents = BeautifulSoup(resp_all.content, "xml")

    # JDPL is always missing from the contents of the response,
    # so query it independently
    if len(all_contents.records) != len(all_bnf_arks):
        print("Not all records were part of the response, querying missing JDPL.")
        bnf_jdpl_query_uri = BNF_API_URI.format(query=all_bnf_arks["jdpl"])

        resp_jdpl = requests.get(bnf_jdpl_query_uri, timeout=60)
        jdpl_contents = BeautifulSoup(resp_jdpl.content, "xml")

        # add the srw:record of JDPL to the other ones
        all_contents.records.append(jdpl_contents.find("srw:record"))
    else:
        print("All records were part of the response.")

    # Write the result to disk
    print(f"Writing the resulting records to disk: {bnf_marc_file}.")
    with open(bnf_marc_file, mode="w", encoding="utf-8") as file:
        file.write(str(all_contents))

    # small sanity-check
    bnf_recs = [r for r in pymarc.parse_xml_to_array(bnf_marc_file) if r is not None]
    if len(bnf_recs) == len(all_bnf_arks):
        print("Success! All records have been saved and are ready to be imported.")
    else:
        print("Failue! The number of records and titles in the config do not match!")


if __name__ == "__main__":
    main()
