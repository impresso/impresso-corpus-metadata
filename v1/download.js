const fs      = require('fs')
const gsjson  = require('google-spreadsheet-to-json')
const config  = require('dotenv').config()

console.log('\n  --- ')
console.log(`  loading spreadsheet: ${process.env.SPREADSHEET_ID}`);
console.log(`  workseet id or title: ${process.env.SPREADSHEET_GID}`);
console.log(`  using credential file: ${process.env.CREDENTIALS}`);

gsjson({
    spreadsheetId: process.env.SPREADSHEET_ID,
    // other options...
    credentials: process.env.CREDENTIALS,
    worksheet: process.env.SPREADSHEET_GID
}) .then(result => {
    const filepath = process.env.SPREADSHEET_OUTPUT_LOCATION || `./data/${process.env.SPREADSHEET_ID}.json`;
    fs.writeFileSync(filepath, JSON.stringify(result, null, 2), 'utf8');
    console.log(`  ${result.length} values found, written to ${filepath} \n`)
}) .catch(err => {
    console.log(err.message);
    console.log(err.stack);
});
