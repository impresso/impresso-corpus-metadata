"""Script generating the Impresso Corpus and Enrichment Release Card.

This card is a JSON file which documents and describes the data within a given release all in one place.

Warning - When using the default arguments this script is to be run from the parent directory impresso-corpus-metadata/
"""

import os
import json
import fire
import git
from impresso_essentials.versioning.helpers import (
    DataStage,
    find_s3_data_manifest_path,
    read_manifest_from_s3_path,
)

# logger = logging.getLogger(__name__)

# TODO change with correct DataStatistics child class when it exists
ALL_SOURCE_TYPE_STATS = [
    "nps_stats",  # current name of Newspapers Stats
    "rb_stats",  # goal name for Newspaper stats (for next release)
    "rm_stats",
    "rs_stats",
    "mg_stats",
]
CORPUS_STAGES = [DataStage.SOLR_TEXT, DataStage.MYSQL_CIS, DataStage.EMB_IMAGES]
ENRICHMENT_STAGES = {
    DataStage.LINGPROC: [],
    DataStage.LANGIDENT: ["images", "lang_fd"],
    DataStage.TEXT_REUSE: ["text_reuse_clusters", "text_reuse_passages"],
    DataStage.ENTITIES: ["ne_entities", "ne_mentions"],
    DataStage.NEWS_AGENCIES: ["ne_entities", "ne_mentions"],
    DataStage.TOPICS: ["topics", "topics_fd"],
    DataStage.OCRQA: [],
    DataStage.EMB_IMAGES: ["images"],
    DataStage.EMB_DOCS: [],
}


def find_manifests(
    processings: list[dict], release_name: str, release_version: str
) -> dict[DataStage, dict]:
    processings_with_manifests = {}
    for proc in processings:
        if release_name in proc["release"] or release_version in proc["release"]:
            stage = DataStage._value2member_map_[proc["process_label"]]
            if proc["computed_manifest"] != "N/A":
                bucket_name = proc["processed_data_s3_path"].split("/")[2]
                partition = proc["processed_data_s3_path"].replace(
                    f"s3://{bucket_name}/", ""
                )
                m_path = find_s3_data_manifest_path(
                    bucket_name, proc["process_label"], partition
                )

                proc["manifest_s3_path"] = m_path
                if m_path is None:
                    msg = f"Warning, process {proc['process_label']}, with run_id {proc['run_id']} has no manifest on S3 in partition {proc['processed_data_s3_path']}."
                    print(msg)
                    # logger.warning(msg)
            else:
                proc["manifest_s3_path"] = "N/A"

            # create a mapping stage -> processes. We can have more than one process per stage
            if stage in processings_with_manifests:
                processings_with_manifests[stage].append(proc)
            else:
                processings_with_manifests[stage] = [proc]
        else:
            msg = f"Removing processing which is not in release: {proc}"
            print(msg)
            # logger.info(msg)

    return processings_with_manifests


def create_corpus_section(processes):
    source_types_stats = []
    corpus_dict = {}
    stage_to_overall_stats = {}

    # fetch the overall stats for all the stages we will list on the corpus stage
    for stg in CORPUS_STAGES:
        proc_for_stg = processes[stg]
        stage_to_overall_stats[stg] = {}
        for proc in proc_for_stg:
            # print(proc['task_name'], proc['manifest_s3_path'], proc['manifest_s3_path'] is None)
            if proc["manifest_s3_path"] is not None:
                manifest_stg = read_manifest_from_s3_path(proc["manifest_s3_path"])

                for sts in manifest_stg["overall_statistics"]:
                    if sts["stage"] == stg.value:
                        for source_type in ALL_SOURCE_TYPE_STATS:
                            if source_type in sts:
                                # add to the effective list of stats to include in the overall corpus overview
                                source_types_stats.append(source_type)
                                stage_to_overall_stats[stg][source_type] = sts[
                                    source_type
                                ]

    for source_type in source_types_stats:
        corpus_dict[source_type] = {
            "titles": stage_to_overall_stats[DataStage.SOLR_TEXT][source_type][
                "titles"
            ],
            "issues": stage_to_overall_stats[DataStage.SOLR_TEXT][source_type][
                "issues"
            ],
            "pages": stage_to_overall_stats[DataStage.MYSQL_CIS][source_type]["pages"],
            "content_items": stage_to_overall_stats[DataStage.SOLR_TEXT][source_type][
                "content_items_out"
            ],
            "images": stage_to_overall_stats[DataStage.EMB_IMAGES][source_type][
                "images"
            ],
            "tokens": stage_to_overall_stats[DataStage.SOLR_TEXT][source_type][
                "ft_tokens"
            ],
        }

    return corpus_dict, source_types_stats


def create_enrichments_section(
    processes: dict[DataStage, list], actual_src_tp_stats: list[str]
) -> dict[str, list]:
    enrich_dict = {}

    for stg, incl_enrich_stats in ENRICHMENT_STAGES.items():

        proc_for_stg = processes[stg]
        # if len(enrich_stats) != 0:
        # stats_for_enrich = {source_type: {} for source_type in actual_src_tp_stats}
        for proc in proc_for_stg:
            proc_label = proc["process_label"]
            model_id = (
                proc["model_id"] if proc["model_id"] != "" else "MISSING MODEL ID"
            )
            if stg == DataStage.TEXT_REUSE:
                # text reuse is not on Hugging-Face
                hf_link = "N/A"
            else:
                hf_link = (
                    proc["huggingface_link"]
                    if proc["huggingface_link"] != ""
                    else "MISSING HUGGING-FACE LINK"
                )

            enrichment = {
                "task name": proc["full_task_name"],
                "model ID": model_id,
                "Hugging-face link": hf_link,
            }

            if proc["manifest_s3_path"] is None:
                msg = f"{proc['full_task_name']} --> Missing manifest!!"
                print(msg)
                # logger.info(msg)
                enrichment_stats = "MISSING MANIFEST!"
            elif len(incl_enrich_stats) != 0 and proc["manifest_s3_path"] != "N/A":
                # not all enrichments have specific stats to fetch
                mft_stats = {}
                manifest_stg = read_manifest_from_s3_path(proc["manifest_s3_path"])
                for ov_sts in manifest_stg["overall_statistics"]:
                    if ov_sts["stage"] == stg.value:
                        for source_type in actual_src_tp_stats:
                            mft_stats[source_type] = {
                                s: ov_sts[source_type][s] for s in incl_enrich_stats
                            }

                enrichment_stats = mft_stats
            else:
                enrichment_stats = None

            # save the processing in the final dict
            if proc_label in enrich_dict:
                enrich_dict[proc_label]["models"].append(enrichment)
                if "enrichment_stats" in enrich_dict[proc_label]:
                    if (
                        enrich_dict[proc_label]["enrichment_stats"] != enrichment_stats
                        and enrichment_stats is not None
                    ):
                        msg = (
                            f"WARNING - {proc_label} --> Statistics already exist and are different! "
                            f" Currently -> {enrich_dict[proc_label]["enrichment_stats"]}"
                            f" New stats -> {enrichment_stats}"
                        )
                        print(msg)
                        # logger.warning(msg)
                elif enrichment_stats is not None:
                    enrich_dict[proc_label]["enrichment_stats"] = enrichment_stats
            else:
                enrich_dict[proc_label] = {
                    "models": [enrichment],
                }
                if enrichment_stats is not None:
                    enrich_dict[proc_label]["enrichment_stats"] = enrichment_stats

    return enrich_dict


def get_links_of_mfts(repo, local_repo_path, release_dir):
    # release_prefix should be changed to the final release dir
    git_links = {}
    for obj in repo.head.commit.tree.traverse():
        if release_dir in obj.abspath and ".json" in obj.abspath:
            mft_key = "/".join(obj.abspath.split("/")[-2:])
            mft_key = mft_key if "data-processing" in mft_key else mft_key.split("/")[1]
            git_links[mft_key] = obj.abspath.replace(
                local_repo_path,
                "https://github.com/impresso/impresso-data-release/blob/master",
            )

    return git_links


def create_processings_section(
    processes: dict[DataStage, list],
    repo: git.Repo,
    local_repo_path: str,
    release_month: str,
    release_prefix: str = "data-release",
) -> dict[str, list]:

    release_dir = "-".join([release_prefix, release_month])
    manifest_gh_links = get_links_of_mfts(repo, local_repo_path, release_dir)
    proc_gh_links = {}
    for stg, processes_for_stg in processes.items():

        proc_gh_links[stg.value] = {}

        for proc in processes_for_stg:

            if proc["manifest_s3_path"] is None:
                msg = f"{proc['full_task_name']} --> Missing manifest!!"
                print(msg)
                # logger.info(msg)
                proc_gh_links[stg.value][proc["full_task_name"]] = "MISSING MANIFEST!"
            elif proc["manifest_s3_path"] != "N/A":
                # not all enrichments have specific stats to fetch
                mft_name = os.path.split(proc["manifest_s3_path"])[1]
                mft_key = "/".join(proc["manifest_s3_path"].split("/")[-2:])
                if mft_key in manifest_gh_links:
                    proc_gh_links[stg.value][proc["full_task_name"]] = (
                        manifest_gh_links[mft_key]
                    )
                elif mft_name in manifest_gh_links:
                    proc_gh_links[stg.value][proc["full_task_name"]] = (
                        manifest_gh_links[mft_name]
                    )
                else:
                    proc_gh_links[stg.value][
                        proc["full_task_name"]
                    ] = "MISSING MANIFEST!"

    return proc_gh_links


def main(
    processing_cheatsheet_path: str = "data/corpus_release_card/gdrive_processings_cheatsheet.json",
    release_name: str = "polar night",
    release_version: str = "2025-04",
    local_data_release_repo_path: str = "/Users/piconti/impresso/release_prep/impresso-data-release",
    output_release_card_path: str = "data/corpus_release_card/corpus_release_card.json",
) -> None:
    print(f"access rights masterfiles dir path: {processing_cheatsheet_path}")

    with open(processing_cheatsheet_path, "r", encoding="utf-8") as file:
        processings = json.load(file)

    # add the manifest paths for each processing listed
    proc_w_mft = find_manifests(processings, release_name, release_version)

    # Create the corpus overview dict and get the list of source types stats actually in corpus.
    corpus_dict, actual_src_tp_stats = create_corpus_section(proc_w_mft)

    enrichments_dict = create_enrichments_section(proc_w_mft, actual_src_tp_stats)

    repo = git.Repo(local_data_release_repo_path)
    if repo.active_branch.name == "staging":
        repo.git.checkout("master")
        repo.remotes.origin.pull()
    proc_gh_links = create_processings_section(
        proc_w_mft, repo, local_data_release_repo_path, release_version
    )

    corpus_release_card = {
        "Release Name": release_name,
        "Release Version": release_version,
        "Impresso Corpus Overview": corpus_dict,
        "Impresso Enrichments": enrichments_dict,
        "Impresso Processings": proc_gh_links,
    }

    with open(output_release_card_path, "w", encoding="utf-8") as outfile:
        json.dump(corpus_release_card, outfile, indent=2)

    print("✅ Finished generating the Corpus and Enrichments Release Card!")


if __name__ == "__main__":
    fire.Fire(main)
