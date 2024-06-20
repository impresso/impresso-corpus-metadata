# impresso-corpus-metadata

Python script to get the data out of a googlespreadsheet table.

```bash
pipenv run python main.py \
  --spreadsheet_id="1jkW6cuINgT7SpuvJE7jVW4lpWiCypVuFiQOhuDZ_o1E" \
  --worksheet_name="impresso-mediasources-master" \
  --output_file="data.json"
```

## initial setup

Install pipenv with the python 3.12 version:

```bash
pyenv local 3.12.2
pipenv install
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
