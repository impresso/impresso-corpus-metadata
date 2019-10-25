const fromcsv = (v) => { return v.split(/\s*,\s*/).filter(d => d.length > 0) };

// code adapted from https://github.com/bassarisse/google-spreadsheet-to-json/issues/24#issuecomment-411903887
const parseDate = (v) => {
  if (v == '') {
    return v;
  }
  return new Date(Date.UTC(0) + (v - 2) * 24 * 60 * 60 * 1000 ).toLocaleDateString('fr-FR', {
    timeZone: 'UTC'
  })};

const translations = {
ingestion_batch: { // new
    field: 'Ingestion batch',
  },
uid: {
    field: 'Newspaper acronym',
  },
acronym: { // to remove ?
    field: 'Newspaper acronym',
  },
partner_uid: {
    field: 'Partner ID',
  },
partner_country: {
    field: 'Partner country',
  },
availability_eta: {
    field: 'Availability ETA',
  },
title: { // changed: name = title
    field: 'Newspaper title',
  },
subtitles: { // changed: subtitle => subtitles
    field: 'Subtitles',
  },
resource_holder_names: { // change: holders => resource_holder_names
    field: 'Resource holder names',
    transform: (v) => {
      return fromcsv(v)
    }
  },
resource_holder_links: {
    field: 'Resource holder links',
    transform: (v) => {
      return fromcsv(v)
    }
  },
institution_logos: {
    field: 'Institution logos',
    transform: (v) => {
      return fromcsv(v)
    }
  },
provenance_id: {
    field: 'Provenance ID',
  },
source_permalink: {
    field: 'Source permalink',
  },
institution_portal: {
    field: 'Institution portal',
  },
languages : { // to remove?
    transform: (v) => { return v.split(/[\s\-]+/).filter(d => d.length > 0)},
    field: 'Lang',
  },
start_year: {
    field: 'Date of first issue',
    transform: parseInt
  },
end_year: {
    field: 'Date of last issue',
    transform: parseInt
  },
date of last issue in the interface: {
    field: 'Date of last issue in the interface',
  },
ocr : { // changed: expected_ocr = ocr
    field: 'OCR',
    transform: v => {
      return v === 'y'
    }
  },
olr : { // expected_olr => olr
    field: 'OLR',
    transform: v => {
      return v === 'y'
    }
  },
olr_quality: {
    field: 'OLR quality',
  },
ocr_format: {
    field: 'OCR format (before ingestion in impresso)',
  },
right_statement: {
    field: 'Right statement',
  },
political_orientation: {
    field: 'Political orientation',
  },
topics: {
    field: 'Topics',
  },
geographic_outreach: {
    field: 'Largest geographic outreach',
  },
geographical_area: {
    field: 'Local geographical area',
  },
latest_periodicity: {
    field: 'Periodicity',
  },
change_periodicity: {
    field: 'Change in periodicity',
  },
publisher: {
    field: 'Publisher',
  },
editor: {
    field: 'Editor',
  },
printer: {
    field: 'Printer',
  },
founder: {
    field: 'Founder',
  },
bib_record_link: {
    field: 'Bibliographic record (link)',
  },
bib_record_text: {
    field: 'Bibliographic record (text)',
  },
dhs_link: {
    field: 'DHS (link)',
  },
digitized_period: {
    field: 'digitized period',
  },
letter_fonts: {
    field: 'letter fonts',
  },
format: {
    field: 'Format',
  },
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
