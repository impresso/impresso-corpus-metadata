# impresso-newspapers
Very simple node scripts to get the data out of a googlespreadsheet table. `npm run remap` remap the JSON file to a human-readable collection of newspaper titles metadata.







## initial setup

```
npm install
```

### get google service account credentials json.
A service account's credentials include a generated email address that is unique and at least one public/private key pair.
We share the google spreadsheet with this service account in order to access private sheets.
https://developers.google.com/identity/protocols/OAuth2ServiceAccount#creatinganaccount

Create a [new credientials](https://console.developers.google.com/apis/credentials?project=impresso-199313) for a service account key, then you have to pick a good service account name. Finally, once the credential JSON file has been downloaded, configure a .env file containing:

```
 SPREADSHEET_ID=<google spreadsheet ID>
 SPREADSHEET_GID=<the GID sheet OR the title of the sheet to be imported>
 CREDENTIALS=./credentials.json
```

Download to json:

```
npm run download
```

Remap to newspaper model:

```
npm run remap
```

Or one after the other:

```
npm start
```
