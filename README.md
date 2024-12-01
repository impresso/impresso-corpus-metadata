# Impresso Corpus Metadata

This repository contains scripts and resources related to the **Impresso Corpus**, including:  

- **Metadata Harvesters**  
   Tools to fetch metadata from:  
   - **Manually Edited Spreadsheets**: Located in the project's GDrive and serialized as JSON in `data/gdrive_metadata`.  
   - **Institutional APIs**: Fetching metadata from partnering institutions in formats such as Marc21, Intermarc, or JSON, and stored in `data/api_metadata`.  

- **Access Rights Harvesters**  
   Tools to gather access rights and copyright information from the project's GDrive, used to generate:  
   - **Access Rights Master Files**: Created for each institution.  
   - **Corpus Access Catalogue**: Aggregating access rights information across the corpus.

Also refer to the [metadata-collection-organisation](https://docs.google.com/drawings/d/1v_8mgdCgWaxduIpHEE_6UsPuTtsvgPRPzU7AGZYHQdw/edit?pli=1) schema for an overview of the process.

## Initial setup and use

### Environment

```bash
# For pipenv users 
pyenv local 3.12.2
pipenv install

# For conda users
conda create -n [env_name] python=3.12.2
pip install requirements.txt
```

### Google service account

We use a service account to programmatically access documents on the project's Gdrive and fetch information from them.

The process requires:
- The creation of a service account requires an email address and at least one public/private key pair. See more information on [google identity service account](https://developers.google.com/identity/protocols/OAuth2ServiceAccount#creatinganaccount).
- The generation of service account [credentials](https://console.developers.google.com/apis/credentials?project=impresso-199313) in the Google APi Console. Pick a good service account name and download the JSON credential file.
- The sharing of the (private) documents to be accessed with the service account email address.

A service account for the project already exists, **ask us for the credentials**.

## Metadata harvesters

### About metadata

The [00_Impresso-MediaSources](https://docs.google.com/spreadsheets/d/1jkW6cuINgT7SpuvJE7jVW4lpWiCypVuFiQOhuDZ_o1E/edit?gid=1371128556#gid=1371128556) preadsheet serves as the central repository for all Impresso media titles, along with their manually collected metadata, organized into one tab per institution.

In addition, we collect further metadata from the institutions' APIs. 

While these two sources of metadata may overlap, both are essential. Not all institutions provide the same level of metadata, and our goal is to establish a baseline common to all titles. The central spreadsheet should ideally capture information not available in the API metadata and/or values that apply uniformly across the entire collection (e.g., institution links or OCR formats).

### 1. Fetching metadata from Gsheets 

This is done with the `fetch_from_gdrive.py` module.

**For a single institution or tab**

```bash
python harvesters/fetch_from_gdrive.py \
  --spreadsheet_id="1jkW6cuINgT7SpuvJE7jVW4lpWiCypVuFiQOhuDZ_o1E" \
  --worksheet_name="[name of tab to ingest]" \
  --output_file="data/gdrive_metadata/gsheet_metadata.[name of tab].json"
```

**For several institutions at once**

In Impresso II, the number of partner institutions has significantly increased. To streamline the process of updating metadata (e.g., JSON files and others in the `/data` folder), a `Makefile` now includes targets for all current tabs in the central metadata spreadsheet. 

To update the fetched metadata, simply call the corresponding target as demonstrated below. The updated files will be saved in the `data/gdrive_metadata` directory, using the format `gsheet_metadata.[tab_name/corpus].json`.

```bash
# Fetch metadata for specific corpora or all at once:
make impresso1-metadata  # Impresso 1 corpus  
make bnf-metadata        # BNF corpus  
make bcul-metadata       # BCUL corpus  
make swa-fedgaz-metadata # SWA and FedGaz corpora  
make all-metadata        # All corpora  
```

### 2. Harvesting metadata from institutions' APIs 

Some institutions provide metadata through APIs, enabling us to supplement the information we have for each media title. The data formats and retrieval methods vary across institutions. 

For the initial Impresso II release, additional metadata can be harvested from the APIs of BnF and BCUL.

#### BNF

The BnF [provides metadata](https://api.bnf.fr/api-sru-catalogue-general) primarily in two formats: IntermarcXchange and Dublin Core. We harvest metadata in [IntermarcXchange](https://www.bnf.fr/fr/intermarc-bibliographique-de-diffusion#bnf-zones-fixes) format because of its similarity to the MARC21 format used for SNL data, minimizing the modifications needed for ingestion.

Using this API, metadata can be retrieved for any media title by providing its corresponding ARK ID. 

The script for this process is located at `harvesters/metadata_api/bnf_metadata.py` and can be executed as follows:

```bash
python harvesters/metadata_api/bnf_metadata.py --config="harvesters/config/api_config.bnf.json" --data_dir="data/api_metadata"
```
The configuration file simply lists the ARK IDs of the media titles in the collection. 

The harvested records are then saved to disk in an XML file named `intermarc_metadata.bnf.xml`.

#### BCUL

The BCUL provides an OAI-PMH API that requires a `username` and `API key` to generate a session key. 

Unlike other systems, metadata records can only be fetched issue by issue rather than for an entire newspaper title. This process is currently handled in the `harvesters/metadata_apis/bcul_metadata.ipynb` notebook, which is planned for conversion into a standalone script.

During harvesting, requests are made for each issue in the ingested collection, and the resulting data is saved to `data/api_metadata/fetched_issue_metadata.bcul.json`. This unprocessed file is retained to avoid re-fetching metadata unnecessarily during subsequent steps.

The fetched metadata is then processed and aggregated by newspaper title into a structured JSON file, `api_metadata.bcul.json`. This file contains the relevant metadata in a format optimized for easy ingestion.

### 3. Copying metadata files to the impresso-master-db repository 

Collected metadata is ingested into **MySQL** and needs to be copied to the `impresso-master-db` repository

To facilitate this process, metadata files from the **impresso-corpus-metadata** repository need to be copied to the [**impresso-master-db**](https://github.com/impresso/impresso-master-db) repository. These copies are handled locally using predefined `Makefile` commands. The commands assume that all repositories are stored under the same parent directory, as illustrated below:

```
parent_directory
├── impresso-master-db
├── impresso-corpus-metadata
```

Ensure this directory structure is in place before running the `Makefile` commands. Below are examples of the commands you can use:

```bash
# Copy metadata files to impresso-master-db:
make sync-gdrive-metadata                # All files from gdrive_metadata  
make sync-gdrive-metadata file_to_sync=<filename>  # Specific file from gdrive_metadata  
make sync-apis-metadata                  # All files from api_metadata  
make sync-apis-metadata file_to_sync=<filename>    # Specific file from api_metadata  
```

## Access rights harvesters

### 1. Fetching access rights gsheets per institution

The process for harvesting **access rights** is similar to that of metadata harvesting. Each institution's access rights are stored in individual Google Sheets in a standardized format, always located in the worksheet named **`DSA_access-rights`**.

Two processes are required:

1. **Fetching the Gsheet Content**  
     The script `harvesters/fetch_from_gdrive.py` retrieves the contents of the Gsheet.

2. **Converting to Masterfile JSON**  
   The script `harvesters/access_rights_masterfile.py` processes the resulting JSON, converting it into the corresponding **access-rights masterfile JSON** for the institution. This includes adding **content bitmaps** and **access rights statements**. The final JSON files is in the directory `data/access_rights_master_files`. The output files follow the naming convention: `access_rights.[institution].json`

Predefined `Makefile` targets for each institution allow to run both scripts sequentially:

```bash
# Fetch and create access rights:
make all-access-rights                    # For all institutions  
make <institution>-access-rights          # For a specific corpus, e.g., snl, bnl, bnf, kbr, kb, bl, onb, sbb, sub, ina, bcul, swa-fedgaz-nzz  
```

### 2. Copying access right files to downstream repositories

Information from access right JSON files is ingested into both **MySQL** and **Solr**. As for the metadata files, they are copied between local repositories.

```bash
# Copy access rights to impresso-master-db:
make sync-access-rights                           # All files  
make sync-access-rights file_to_sync=<filename>  # Specific file, e.g., access_rights.bcul.json  

# Copy access rights to Solr:
make sync-solr-access-rights
```

## Access rights aggregator

(description to come)


## About Impresso

### Impresso project

[Impresso - Media Monitoring of the Past](https://impresso-project.ch) is an interdisciplinary research project that aims to develop and consolidate tools for processing and exploring large collections of media archives across modalities, time, languages and national borders. The first project (2017-2021) was funded by the Swiss National Science Foundation under grant No. [CRSII5_173719](http://p3.snf.ch/project-173719) and the second project (2023-2027) by the SNSF under grant No. [CRSII5_213585](https://data.snf.ch/grants/grant/213585) and the Luxembourg National Research Fund under grant No. 17498891.

### Copyright

Copyright (C) 2024 The Impresso team.

### License

This program is provided as open source under the [GNU Affero General Public License](https://github.com/impresso/impresso-pyindexation/blob/master/LICENSE) v3 or later.

---

<p align="center">
  <img src="https://github.com/impresso/impresso.github.io/blob/master/assets/images/3x1--Yellow-Impresso-Black-on-White--transparent.png?raw=true" width="350" alt="Impresso Project Logo"/>
</p>