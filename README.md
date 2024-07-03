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

##### `main_metadata.py` module
TODO context
```bash
pipenv run python metadata_harvest/gdrive/main_metadata.py \
  --spreadsheet_id="1jkW6cuINgT7SpuvJE7jVW4lpWiCypVuFiQOhuDZ_o1E" \ # todo update
  --worksheet_name="impresso-mediasources-master" \
  --output_file="data.json"
```

##### Fetching the Gsheet metadata for various collections

TODO context
```bash
# for all of the Impresso 1 corpus
make impresso1
# for the BNF corpus
make bnf
# for the BCUL corpus
make bcul
# for the SWA and FedGaz corpuses
make swa-fedgaz
# for all corpuses
make all
```

#### 2. Harvesting metadata from institutions' APIs to complete the one from the Gsheet

##### BNF

TODO 

##### BCUL

TODO

#### 3. Copying the resulting files to the `impresso-master-db` repository

To copy the harvested metadata to the [impresso-master-db](https://github.com/impresso/impresso-master-db) GitHub repository, it needs to be cloned locally in the same parent directory as this one (impresso-corpus-metadata):
```
parent_dir
├── impresso-master-db
└── impresso-corpus-metadata
```

The contents harvested from both institution APIs and fetched from gsheets can be copied in a very similar approach.
One can simply run one of the following commands, which will copy the contents of the `impresso-corpus-metadata/data/api`  or `impresso-corpus-metadata/data/gdrive` directory into `impresso-master-db/impresso_db/data`.
Optionnally, a parameter can be added to specify exactly which file should be synched, otherwise all files will be.
```bash
# copy all files in /data/gdrive 
make sync-gdrive
# specify the file from /data/gdrive to copy
make sync-gdrive file_to_sync=gsheet_metadata.bcul.json
# copy all files in /data/apis 
make sync-apis
# specify the file from /data/apis to copy
make sync-apis file_to_sync=intermarc_metadata.bnf.xml
```

### Running the access rights harvesters

TODO