"""Script generating the Impresso Corpus and Enrichment Release Card.

This card is a JSON file which documents and describes the data within a given release all in one place.

Warning - When using the default arguments this script is to be run from the parent directory impresso-corpus-metadata/
"""

import os
import json
import logging
import fire
import git

from impresso_essentials.versioning.helpers import (
    find_s3_data_manifest_path,
    read_manifest_from_s3_path,
)
from impresso_essentials.utils import init_logger, DataStage

logger = logging.getLogger(__name__)

# TODO Either keep only media_stats or add medium-specific stats when in time
ALL_SOURCE_TYPE_STATS = [
    "nps_stats",  # current name of Newspapers Stats
    "media_stats",  # goal name for media stats (for next release)
    "rb_stats",
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
    """Finds and associates manifest S3 file paths with processing tasks for a given release.

    This function iterates through a list of processing tasks and checks if they belong
    to the specified release by matching `release_name` or `release_version`. If a process
    has a valid computed manifest, it searches for its manifest file in an S3 bucket and
    updates the process dictionary with the manifest path.

    Args:
        processings (list[dict]): A list of dictionaries where each dictionary represents
            a processing task with metadata, including release information and S3 paths.
        release_name (str): The name of the release to filter processing tasks.
        release_version (str): The version of the release to filter processing tasks.

    Returns:
        dict[DataStage, dict]: A dictionary mapping data stages to lists of processing
        tasks that include their associated manifest paths.

    Raises:
        KeyError: If a required key is missing from a processing dictionary.
    """
    processings_with_manifests = {}
    for proc in processings:
        if release_name in proc["release"] or release_version in proc["release"]:
            stage = DataStage._value2member_map_[proc["process_label"]]
            if proc["computed_manifest"] != "N/A":
                bucket_name = proc["processed_data_s3_path"].split("/")[2]
                partition = proc["processed_data_s3_path"].replace(f"s3://{bucket_name}/", "")
                m_path = find_s3_data_manifest_path(bucket_name, proc["process_label"], partition)

                proc["manifest_s3_path"] = m_path
                if m_path is None:
                    msg = f"⚠️  Warning ⚠️, process {proc['process_label']}, with run_id {proc['run_id']} has no manifest on S3 in partition {proc['processed_data_s3_path']}."
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
            msg = f"Removing processing which is not in release: {proc['full_task_name']}"
            print(msg)
            logger.info(msg)

    return processings_with_manifests


def create_corpus_section(
    processes: dict[DataStage, dict],
) -> tuple[dict[str, dict], list[str]]:
    """Generates a dictionary containing the main corpus-level statistics.

    This function extracts relevant corpus statistics from various data stages,
    such as the number of titles, issues, pages, content items, images, and tokens.
    The extracted statistics are used to construct an overview of the corpus.

    Args:
        processes (dict[DataStage, dict]): A dictionary where keys represent data stages
            and values are dictionaries containing processing task information.

    Returns:
        tuple[dict[str, dict], list[str]]: A tuple containing:
            - A dictionary where keys are source types and values are dictionaries
              containing corpus statistics for that source type.
            - A list of source types for which statistics were successfully extracted.

    Raises:
        KeyError: If a required data stage is missing in `processes`.
    """
    print("Creating the Impresso Corpus section")
    logger.info("Creating the Impresso Corpus section")

    source_types_stats = []
    corpus_dict = {}
    stage_to_overall_stats = {}

    # fetch the overall stats for all the stages we will list on the corpus stage
    for stg in CORPUS_STAGES:
        proc_for_stg = processes[stg]
        stage_to_overall_stats[stg] = {}
        for proc in proc_for_stg:
            if proc["manifest_s3_path"] is not None:
                manifest_stg = read_manifest_from_s3_path(proc["manifest_s3_path"])

                for sts in manifest_stg["overall_statistics"]:
                    if sts["stage"] == stg.value:
                        for source_type in ALL_SOURCE_TYPE_STATS:
                            if source_type in sts:
                                # specific case for nps_stats as it's deprecated
                                if source_type == "nps_stats":
                                    stage_to_overall_stats[stg]["media_stats"] = sts[source_type]
                                else:
                                    # add to the effective list of stats to include in the overall corpus overview
                                    source_types_stats.append(source_type)
                                    stage_to_overall_stats[stg][source_type] = sts[source_type]

    for source_type in source_types_stats:
        if stage_to_overall_stats[DataStage.SOLR_TEXT] != {}:
            titles = stage_to_overall_stats[DataStage.SOLR_TEXT][source_type]["titles"]
            issues = stage_to_overall_stats[DataStage.SOLR_TEXT][source_type]["issues"]
            cis = stage_to_overall_stats[DataStage.SOLR_TEXT][source_type]["content_items_out"]
            tokens = stage_to_overall_stats[DataStage.SOLR_TEXT][source_type]["ft_tokens"]
        else:
            titles, issues, cis, tokens = ("MISSING SOLR MANIFEST!",) * 4

        source_type = "media_stats" if source_type == "nps_stats" else source_type
        corpus_dict[source_type] = {
            "titles": titles,
            "issues": issues,
            "pages": stage_to_overall_stats[DataStage.MYSQL_CIS][source_type]["pages"],
            "content_items": cis,
            "images": stage_to_overall_stats[DataStage.EMB_IMAGES][source_type]["images"],
            "tokens": tokens,
        }

    return corpus_dict, source_types_stats


def get_model_link(process: dict[str, str | int]) -> dict[str, str]:
    """Handle the various cases possible relative to links to models.

    Not all processed have hugging face links, and some have

    Args:
        process (dict[str, str  |  int]): Dict with the information
            describing the process.

    Returns:
        dict[str, str]: Correct model link key-value pair.
    """
    if process["huggingface_link"].startswith("https://huggingface.co"):
        return {"huggingface_link": process["huggingface_link"]}
    elif process["huggingface_link"].startswith("https://github.com"):
        return {"github_link": process["huggingface_link"]}
    elif process["huggingface_link"] == "":
        # If the hugging face link is missing
        return {"huggingface_link": "MISSING HUGGING-FACE/GITHUB LINK"}

    # if the link had yet another format
    msg = f"process {process['process_label']} has an incorrect model link!"
    logger.warning(msg)
    print(msg)
    return {"huggingface_link": "INCORRECT HUGGING-FACE/GITHUB LINK"}


def create_enrichments_section(
    processes: dict[DataStage, list], actual_src_tp_stats: list[str]
) -> dict[str, list]:
    """Generates a structured dictionary for enrichment processes and their associated statistics.

    This function processes a given set of data enrichment tasks, linking them to model
    identifiers, Hugging Face repositories (if applicable), and available manifest statistics.

    Args:
        processes (dict[DataStage, list]): A dictionary where keys are data stages and
            values are lists of processing tasks associated with each stage.
        actual_src_tp_stats (list[str]): A list of source types for which enrichment
            statistics should be extracted.

    Returns:
        dict[str, list]: A dictionary where each key corresponds to a process label,
        and the value contains:
            - A list of models used in the process, including their task name, model ID,
              and Hugging Face link (if applicable).
            - Enrichment statistics if available.

    Raises:
        KeyError: If a data stage in `ENRICHMENT_STAGES` is not found in `processes`.
    """
    print("Creating the Impresso Enrichments section")
    logger.info("Creating the Impresso Enrichments section")

    enrich_dict = {}

    for stg, incl_enrich_stats in ENRICHMENT_STAGES.items():

        proc_for_stg = processes[stg]

        for proc in proc_for_stg:
            proc_label = proc["process_label"]
            model_id = proc["model_id"] if proc["model_id"] != "" else "MISSING MODEL ID"

            enrichment = {
                "task_name": proc["full_task_name"],
                "model_ID": model_id,
            }
            enrichment.update(get_model_link(proc))

            if proc["manifest_s3_path"] is None:
                msg = f"{proc['full_task_name']} --> Missing manifest!!"
                print(msg)
                logger.info(msg)
                enrichment_stats = "MISSING MANIFEST!"
            elif len(incl_enrich_stats) != 0 and proc["manifest_s3_path"] != "N/A":
                # not all enrichments have specific stats to fetch
                mft_stats = {}
                manifest_stg = read_manifest_from_s3_path(proc["manifest_s3_path"])
                for ov_sts in manifest_stg["overall_statistics"]:
                    if ov_sts["stage"] == stg.value:
                        for source_type in actual_src_tp_stats:
                            ## Temporary fix while we have multiple names for stats
                            if source_type == "nps_stats":
                                mft_stats["media_stats"] = {
                                    s: ov_sts[source_type][s] for s in incl_enrich_stats
                                }
                            elif source_type == "media_stats" and "media_stats" not in ov_sts:
                                mft_stats["media_stats"] = {
                                    s: ov_sts["nps_stats"][s] for s in incl_enrich_stats
                                }
                            else:
                                mft_stats[source_type] = {
                                    s: (ov_sts[source_type][s]) for s in incl_enrich_stats
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
                        logger.warning(msg)
                elif enrichment_stats is not None:
                    enrich_dict[proc_label]["enrichment_stats"] = enrichment_stats
            else:
                enrich_dict[proc_label] = {
                    "models": [enrichment],
                }
                if enrichment_stats is not None:
                    enrich_dict[proc_label]["enrichment_stats"] = enrichment_stats

    return enrich_dict


def get_links_of_mfts(
    repo: git.Repo,
    local_repo_path: str,
    release_dir: str,
    master_branch_link: str = "https://github.com/impresso/impresso-data-release/blob/master",
) -> dict[str, str]:
    """Retrieves GitHub links for manifest files in a given release directory.

    This function scans the latest commit in a Git repository, identifies manifest
    files (`.json`) within the specified release directory, and constructs GitHub links
    for each manifest.
    The keys are either the manifest parent dir and filename or only the filename based on
    whether the filename will be unique (manifests of the `data-processing` step are not).

    Args:
        repo (git.Repo): The Git repository object containing the release data.
        local_repo_path (str): The local file system path to the repository.
        release_dir (str): The release directory where manifests are stored. Is in format
            `data-release-YYYY-MM`.
        master_branch_link (str, optional): The base URL for the master branch of the
            impresso-data-release repository.
            Defaults to "https://github.com/impresso/impresso-data-release/blob/master".

    Returns:
        dict[str, str]: A dictionary mapping "manifest keys" (derived from file paths) to
        their corresponding GitHub links.
    """
    git_links = {}
    # pull from the repository
    repo.remotes.origin.pull()

    for obj in repo.head.commit.tree.traverse():
        if release_dir in obj.abspath and ".json" in obj.abspath:
            print(f"obj.abspath: {obj.abspath}")
            mft_key = "/".join(obj.abspath.split("/")[-2:])
            mft_key = mft_key if "data-processing" in mft_key else mft_key.split("/")[1]
            git_links[mft_key] = obj.abspath.replace(
                local_repo_path,
                master_branch_link,
            )

    return git_links


def create_processings_section(
    processes: dict[DataStage, list],
    repo: git.Repo,
    local_repo_path: str,
    release_month: str,
    release_prefix: str = "data-release",
) -> dict[str, list]:
    """Generates a dictionary linking processing tasks to their manifest GitHub links.

    This function organizes processing tasks by data stage and retrieves corresponding
    manifest GitHub links based on stored manifest paths.
    If a manifest is missing, it logs a message and marks it as "MISSING MANIFEST!".

    Args:
        processes (dict[DataStage, list]): A dictionary mapping data stages to lists of processing tasks.
        repo (git.Repo): The Git repository object containing the manifest files.
        local_repo_path (str): Local path to the repository where manifests are stored.
        release_month (str): The release month (e.g., "2025-03") used for constructing the release directory.
        release_prefix (str, optional): Prefix for the release directory name. Defaults to "data-release".

    Returns:
        dict[str, list]: A dictionary where keys are data stage names and values are dictionaries
        mapping processing task names to their corresponding GitHub manifest links. If a manifest
        is missing, the value is "MISSING MANIFEST!".
    """
    print("Creating the Impresso Processings section")
    logger.info("Creating the Impresso Processings section")
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
                    proc_gh_links[stg.value][proc["full_task_name"]] = manifest_gh_links[mft_key]
                elif mft_name in manifest_gh_links:
                    proc_gh_links[stg.value][proc["full_task_name"]] = manifest_gh_links[mft_name]
                else:
                    proc_gh_links[stg.value][proc["full_task_name"]] = "MISSING MANIFEST!"

    return proc_gh_links


def main(
    processing_cheatsheet_path: str = "data/corpus_release_card/gdrive_processings_cheatsheet.json",
    release_name: str = "polar night",
    release_version: str = "2025-04",
    local_data_release_repo_path: str = "/Users/piconti/impresso/release_prep/impresso-data-release",
    output_release_card_path: str = "data/corpus_release_card/corpus_release_card.json",
    log_file: str | None = None,
) -> None:
    msg = f"Starting the generation of the Impresso Corpus Release Card for {release_version} release."
    print(msg)
    logger.info(msg)

    if log_file is not None:
        # initialize the logfile if a path was provided
        init_logger(logger, logging.INFO, log_file)

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
    logger.info("✅ Finished generating the Corpus and Enrichments Release Card!")


if __name__ == "__main__":
    fire.Fire(main)
