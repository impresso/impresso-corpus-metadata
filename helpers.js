const fromcsv = (v) => { return v.split(/\s*,\s*/).filter(d => d.length > 0) };

// code adapted from https://github.com/bassarisse/google-spreadsheet-to-json/issues/24#issuecomment-411903887
const parseDate = (v) => { return new Date(Date.UTC(0) + (v - 2) * 24 * 60 * 60 * 1000 ).toLocaleDateString('fr-FR', { timeZone: 'UTC' })};

const translations = {
  partner_uid: {
    field: 'partnerid', // archive
  },
  holder     : {
    field: 'Resource Holder*',
    // CSV of links + REGEX
    // KB Graubünden https://www.gr.ch/DE/institutionen/verwaltung/ekud/afk/kbg/ueberuns/Seiten/Willkommen.aspx,  RERO https://www.rero.ch (hosting), BN http://www.nb.admin.ch
    transform: (v) => { return fromcsv(v).map(d => {
      let re = /([^\s]+)\s*(https?:.*)$/g
      let match = re.exec(d)

      return match? {
        name: match[1],
        url: match[2]
      }: {
        name: d
      }
    })},

  },
  uid    : {
    field: 'newspaperAcronym*',
  },
  availability_eta    : {
    field: 'availability ETA',
    transform: parseDate
  },
  acronym    : { // internal
    field: 'newspaper acronym*',
  },
  start_year : {
    field: 'Date of first issue* (YYYY)',
    transform: parseInt
  },
  end_year   : {
    field: 'Date of last issue* (YYYY)',
    transform: parseInt
  },
  languages       : {
    transform: (v) => { return v.split(/[\s\-]+/).filter(d => d.length > 0)},
    field: 'Lang*',
  },
  name      : {
    field: 'newspaperTitle(s)*',
  },
  subtitle   : {
    field: 'Subtitle*',
  },

  url        : {
    field: 'Online Portal/Link/ Reference*',
  },
  status     : {
    field: 'Digitization Status* ',
  },
  provenance_id     : {
    field: 'provenanceID',
  },
  predecessor: {
    field: 'Predecessor'
    // free texxte
  },
  predecessor_uid: {
    field: 'previousPredecessorid', // only ONE
    transform: fromcsv
  },
  expected_aliases: {
    field: 'Title changes over time*',
  },
  expected_raw_issues : {
    field: 'Total number of issues',
    transform: parseInt
  },
  expected_issues     : {
    field: 'Total number of digitized issues',
    transform: parseInt
  },
  expected_raw_pages  : {
    field: 'Total number of  pages',
    transform: parseInt
  },
  expected_pages      : {
    field: 'Total number of digitized pages',
    transform: parseInt
  },
  expected_ocr      : {
    field: 'OCR* (y/n)',
    transform: v => {
      return v === 'y'
    }
  },
  expected_olr     : {
    field: 'OLR* (y/n)',
    transform: v => {
      return v === 'y'
    }
  },

  geographical_outreach : {
    field: 'Largest geographic outreach*',
    // choices: international, regional, national, local
  },
  geographical_area: {
    field:'Local Geographical Area*',
    // GEO entities
    // CH-FR
    // internal
  },
  periodicity  : {
    field: 'periodicity*',
    // 3 times a week
  },

  political_orientation: {
    field: 'Political orientation* (radical, liberal,....)',
    transform: fromcsv
  },
  editor       : {
    field: 'Editor*',
    transform: fromcsv
  },
  printer       : { // as edge: is_printer_of, source: add mention of PartnerId
    field: 'Printer*',
    transform: fromcsv
  },
  publisher     : { // as edge: is_publisher_of
    field: 'Publisher*',
    transform: fromcsv
  },
  founder      : { // as edge: is_founder_of
    field: 'Founder*',
    transform: fromcsv ,
  },
  topics: {
    field: 'Topics (general, cultural, business)*',
    transform: fromcsv
  }

};

const mapper = (d) => {
  let n = {};
  // lowercase d keys
  for(k in d){
    d[k.toLowerCase()] = d[k]
  }
  for(t in translations) {
    let k = translations[t].field.replace(/\s/g, '').toLowerCase();
    let value = '' + (d[k] || '')
    value = value.trim();
    if(translations[t].transform)
      value = translations[t].transform(value);
    n[t.toLowerCase()] = value;
  }
  n._valid  = n.uid.match(/^[A-Z]+$/) && !isNaN(n.start_year) && !isNaN(n.end_year) && n.languages.length > 0;
  return n;
}

module.exports = {
  mapper,
  translations
}
