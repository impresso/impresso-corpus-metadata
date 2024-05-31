const fs      = require('fs')
const helpers = require('./helpers')
const config  = require('dotenv').config()
const data    = require(process.env.SPREADSHEET_OUTPUT_LOCATION || `./data/${process.env.SPREADSHEET_ID}.json`)

//console.log(config)

let filepath = process.env.OUTPUT_LOCATION || `./data/${process.env.SPREADSHEET_ID}.remap.json`;

fs.writeFileSync(filepath, JSON.stringify(data.map(helpers.mapper), null, 2), 'utf8');

console.log(`\n  --- \n  ${data.length} values written to ${filepath}\n`);
