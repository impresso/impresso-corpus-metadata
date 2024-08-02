# impresso-corpus-metadata

This repository contains python scripts to harvest metadata on the Impresso corpus by fetching it from:

- Spreadsheets on Google Drive, and writing it to JSON files.
- The APIs of the partner institution, and writing it to files of varied formats (Marc21, Intermarc, JSON).

TODO: general explaination of organization.

## Initial setup and use

### Environments

#### Pipenv users

Install pipenv with the python 3.12 version:

```bash
pyenv local 3.12.2
pipenv install
```

#### Conda users

```bash
conda create -n [env_name] python=3.12.2
pip install requirements.txt
```

### Running the various metadata harvesters


#### 0. Creating or obtaining the credentials

A service account's credentials include a generated email address that is unique and at least one public/private key pair.
We share the google spreadsheet with this service account in order to access private sheets.
https://developers.google.com/identity/protocols/OAuth2ServiceAccount#creatinganaccount

Create a [new credientials](https://console.developers.google.com/apis/credentials?project=impresso-199313) for a service account key, then you have to pick a good service account name. Finally, once the credential JSON file has been downloaded:

Fetching information present in Google Spreadsheets requires having the credentials to a service account.
**However**, such a service account **already exists**, so no need to create a new one.
Ask for the credentials to be shared with you.

#### 1. Fetching the contents of Gsheets into a JSON file

##### `fetch_from_gdrive.py` module

The base of the metadata for each title is collected in [this spreadsheet](https://docs.google.com/spreadsheets/d/1jkW6cuINgT7SpuvJE7jVW4lpWiCypVuFiQOhuDZ_o1E/edit?gid=1371128556#gid=1371128556).
Each institution is associated to a tab, and contains a first base of metadata for each media title.
For some institutions, this metadata is then also completed by metadata fetched from their API. As a result, good contenders for the information that should be filled in are anything not present in the API metadata and/or values that are common to the entire collection (eg. insitution links or OCR formats).

One can run the script by hand in the following way.
```bash
python harvesters/fetch_from_gdrive.py \
  --spreadsheet_id="1jkW6cuINgT7SpuvJE7jVW4lpWiCypVuFiQOhuDZ_o1E" \
  --worksheet_name="[name of tab to ingest]" \
  --output_file="data/gdrive_metadata/gsheet_metadata.[name of tab].json"
```

##### Fetching the Gsheet metadata for various collections

For Impresso II, the number of partner institutions has considerably increased. 
To ease the process of updating the metadata, targets have been added to a `Makefile` for all current tabs in the central metadata spreadsheet.
In order to update the fetched metadata, one only needs to call the corresponding target as shown below.
The resulting file will be in the `data/gdrive_metadata` directory, in files of the format `gsheet_metadata.[name of tab/corpus].json`.

```bash
# for all of the Impresso 1 corpus
make impresso1-metadata
# for the BNF corpus
make bnf-metadata
# for the BCUL corpus
make bcul-metadata
# for the SWA and FedGaz corpuses
make swa-fedgaz-metadata
# for all corpuses
make all-metadata
```

#### 2. Harvesting metadata from institutions' APIs to complete the one from the Gsheet

Some institutions expose their metadata on APIs from which we can fetch them, allowing us to complete the information we have on each media title. The format in which the data is exposed and the way to fetch is varies for each one.
For the first Impresso II release, additional metadata can be harvested for BNF and BCUL.

##### BNF

The BnF [exposes its metadata](https://api.bnf.fr/api-sru-catalogue-general) in mainly two formats: IntermarcXchange and DublinCore. 
We are harvesting it in [IntermarcXchange](https://www.bnf.fr/fr/intermarc-bibliographique-de-diffusion#bnf-zones-fixes) due to its proximity to the marc21 format used for SNL data, reducing the modifications necessary for the ingestion. 

Through this API, one only needs the ark ID corresponding to the media titles they are interested in to harvest the desired metadata.
This is done in the script `harvesters/metadata_api/bnf_metadata.py` which can be run in the following way:

```bash
python harvesters/metadata_api/bnf_metadata.py --config="harvesters/config/api_config.bnf.json" --data_dir="data/api_metadata"
```
Where the configuration file simply contains the ark ids of each title in the collection.
The resulting recourds are then written to disk in a XML file named `intermarc_metadata.bnf.xml`.

##### BCUL

The BCUL has an OAI-PMH API for which a `username` and `API key` are necessary to obtain a session key.
Unfortunately, the records can only be fetched by issue and not by entire newspaper title.
This process is done in the `harvesters/metadata_apis/bcul_metadata.ipynb` notebook, which will be converted to a script.
As a result, requests are made for each issue in the ingested collection, and then written to disk in the file `data/api_metadata/fetched_issue_metadata.bcul.json`.
This first file, while not processed is kept as to prevent having to repeat the process when generating the metadata.

The fetched metadata is then processed and aggregated by newspaper title to create the JSON file named `api_metadata.bcul.json`, prepared to keep the metatadata of interest, in a format that is easy to ingest.

#### 3. Copying the resulting files to the `impresso-master-db` repository

To copy the harvested metadata to the [impresso-master-db](https://github.com/impresso/impresso-master-db) GitHub repository, it needs to be cloned locally in the same parent directory as this one (impresso-corpus-metadata):
```
parent_dir
├── impresso-master-db
└── impresso-corpus-metadata
```

The contents harvested from both institution APIs and fetched from gsheets can be copied in a very similar approach.
One can simply run one of the following commands, which will copy the contents of the `impresso-corpus-metadata/data/api_metadata`  or `impresso-corpus-metadata/data/gdrive_metadata` directory into the corresponding subdirectoy of `impresso-master-db/impresso_db/data`.
Optionnally, a parameter can be added to specify exactly which file should be synched, otherwise all files will be.
```bash
# copy all files in /data/gdrive 
make sync-gdrive-metadata
# specify the file from /data/gdrive to copy
make sync-gdrive-metadata file_to_sync=gsheet_metadata.bcul.json
# copy all files in /data/apis 
make sync-apis-metadata
# specify the file from /data/apis to copy
make sync-apis-metadata file_to_sync=intermarc_metadata.bnf.xml
```

### Running the access rights harvesters

TODO