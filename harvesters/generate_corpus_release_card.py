"""Script generating the Impresso Corpus and Enrichment Release Card.

This card is a JSON file which documents and describes the data within a given release all in one place.
"""

import os
import json
import copy
import fire
import logging
from harvesters.utils import transform_value, BITMAP_KEYS
from impresso_essentials.versioning.helpers import (
    DataStage,
    find_s3_data_manifest_path,
    read_manifest_from_s3_path,
)

logger = logging.getLogger(__name__)

CORPUS_STAGES = [DataStage.SOLR_TEXT, DataStage.MYSQL_CIS, DataStage.EMB_IMAGES]
ENRICHMENT_STAGES = [
    DataStage.LINGPROC,
    DataStage.LANGIDENT,
    DataStage.TEXT_REUSE,
    DataStage.ENTITIES,
    DataStage.NEWS_AGENCIES,
    DataStage.TOPICS,
    DataStage.OCRQA,
    DataStage.EMB_IMAGES,
    DataStage.EMB_ENTITIES,
    DataStage.EMB_DOCS,
]


def find_manifests(processings: list[dict]) -> dict[DataStage, dict]:
    processings_with_manifests = {}
    for proc in processings:
        stage = DataStage._value2member_map_[proc["processing_label"]]
        if proc["processed_data_s3_path"] != "N/A":
            bucket_name = proc["processed_data_s3_path"].split("/")[2]
            partition = proc["processed_data_s3_path"].replace(
                f"s3://{bucket_name}/", ""
            )
            m_path = find_s3_data_manifest_path(
                bucket_name, proc["processing_label"], partition
            )

            proc["manifest_s3_path"] = m_path
            if m_path is None:
                msg = f"Warning, process {proc['processing_label']}, with run_id {proc['run_id']} has no manifest on S3 in partition {proc['processed_data_s3_path']}."
                print(msg)
                logger.warning(msg)

        # create a mapping stage -> processes. We can have more than one process per stage
        if stage in processings_with_manifests:
            processings_with_manifests[stage].append(proc)
        else:
            processings_with_manifests[stage] = [proc]

    return processings_with_manifests


def main(
    processing_cheatsheet_path: str = "../data/corpus_release_card/gdrive_processings_cheatsheet.json",
    release: str = "polar night",
) -> None:
    print(f"access rights masterfiles dir path: {processing_cheatsheet_path}")

    with open(processing_cheatsheet_path, "r", encoding="utf-8") as file:
        processings = json.load(file)


if __name__ == "__main__":
    fire.Fire(main)
