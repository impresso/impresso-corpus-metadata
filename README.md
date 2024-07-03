# impresso-corpus-metadata

This repository contains python scripts to harvest metadata on the Impresso corpus by fetching it from:

- Spreadsheets on Google Drive, and writing it to JSON files.
- The APIs of the partner institution, and writing it to files of varied formats (Marc21, Intermarc, JSON).

TODO: general explaination of organization.

## initial setup

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

### get google service account credentials json.

A service account's credentials include a generated email address that is unique and at least one public/private key pair.
We share the google spreadsheet with this service account in order to access private sheets.
https://developers.google.com/identity/protocols/OAuth2ServiceAccount#creatinganaccount

Create a [new credientials](https://console.developers.google.com/apis/credentials?project=impresso-199313) for a service account key, then you have to pick a good service account name. Finally, once the credential JSON file has been downloaded:

```bash
pipenv run python main.py \
  --spreadsheet_id="1jkW6cuINgT7SpuvJE7jVW4lpWiCypVuFiQOhuDZ_o1E" \
  --worksheet_name="impresso-mediasources-master" \
  --output_file="data.json"
```
