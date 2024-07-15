# Variables
db_data_dir = ../impresso-master-db/impresso_db/data
data_dir = data
metadata_file_prefix = gsheet_metadata
access_rights_file_prefix = gsheet_access_rights
metadata_gsheet_id = 1jkW6cuINgT7SpuvJE7jVW4lpWiCypVuFiQOhuDZ_o1E
ar_worksheet_name = DSA_access-rights
file_to_sync = 

# access rights gsheet ids
snl_ar_ghseet_id = 1ctskS_dAy1EMmZDY3T-um-IE53ZaNuMbhF3EAOmajko
bnl_ar_ghseet_id = 1nPHaTPDfwkpC91P9b6EnKcmJdzfOrysk1yu9i21geSI
bnf_ar_ghseet_id = 1dNNj2vpIm7xSrW6vMBFWWQV2FbxGP3PCa5RsqG8EKH4
bcul_ar_ghseet_id = 1EeMo01iwcLWIuAwWgYN7vwkmsOJM5dA1ipJuaikbBCo
swa_fedgaz_nzz_ar_ghseet_id = 1PC7B90IkXT8arczM8FlV6PN5YbZH1LjHV8ZUno5UW9c
kb_ar_ghseet_id = 1D-feGATwlBbxrTRLiDRVhEOGIxgGaa_CMEy_ZlQSbPE
onb_ar_ghseet_id = 1vvyQ-5ZEoqg7DpiwZC-LoDo59ObjNx3SkQyfv4L_Uh4
sub_ar_ghseet_id = 1zglWsq5EL3HbfB8QF_vyEKIewi8AWHD6

# Targets
help:
	@echo "Programmatically export the contents of the metadata google spreadsheet to json."
	@echo "Available targets:"
	@echo "  all-metadata   - Export the metadata for all ingestion batches"
	@echo "  impresso1-metadata      - Export the metadata for all Impresso 1 data"
	@echo "  bnf-metadata      - Export the metadata for all BNF media titles"
	@echo "  bcul-metadata       - Export the metadata for all BCUL media titles"
	@echo "  swa-fedgaz-metadata     - Export the metadata for all SWA and FedGaz media titles"
	@echo "  sync-gdrive-metadata     - Synchronize all or part of the gdrive data folder with the one of the impresso-master-db repository"
	@echo "  sync-api-metadata     - Synchronize all or part of the api data folder with the one of the impresso-master-db repository"
	@echo "  all-access-rights     - Export the access rights for all partners"
	@echo "  snl-access-rights     - Export the access rights for all SNL partners"
	@echo "  bnl-access-rights     - Export the access rights for BNL"
	@echo "  bnf-access-rights     - Export the access rights for BNF"
	@echo "  bcul-access-rights     - Export the access rights for BCUL"
	@echo "  swa-fedgaz-nzz-access-rights     - Export the access rights for SWA, FedGaz and NZZ"
	@echo "  kb-access-rights     - Export the access rights for KB"
	@echo "  onb-access-rights     - Export the access rights for ONB"
	@echo "  sub-access-rights     - Export the access rights for SUBKB"
	@echo "  help      - Display this help message"


### Fetching metadata ###
all-metadata: impresso1-metadata bnf-metadata bcul-metadata swa-fedgaz-metadata

impresso1-metadata:
	python harvesters/fetch_from_gdrive.py \
	--spreadsheet_id=$(metadata_gsheet_id) \
	--worksheet_name="impresso1-collection" \
	--output_file="$(data_dir)/gdrive_metadata/$(metadata_file_prefix).impresso1.json" \
	--is_metadata

bnf-metadata:
	python harvesters/fetch_from_gdrive.py \
	--spreadsheet_id=$(metadata_gsheet_id) \
	--worksheet_name="BNF" \
	--output_file="$(data_dir)/gdrive_metadata/$(metadata_file_prefix).bnf.json" \
	--is_metadata

bcul-metadata:
	python harvesters/fetch_from_gdrive.py \
	--spreadsheet_id=$(metadata_gsheet_id) \
	--worksheet_name="BCUL" \
	--output_file="$(data_dir)/gdrive_metadata/$(metadata_file_prefix).bcul.json" \
	--is_metadata

swa-fedgaz-metadata:
	python harvesters/fetch_from_gdrive.py \
	--spreadsheet_id=$(metadata_gsheet_id) \
	--worksheet_name="SWA-FedGaz" \
	--output_file="$(data_dir)/gdrive_metadata/$(metadata_file_prefix).swa_fedgaz.json" \
	--is_metadata

sync-gdrive-metadata: 
	rsync -r -v "$(data_dir)/gdrive_metadata/$(file_to_sync)" "$(db_data_dir)/gdrive_metadata"

sync-api-metadata: 
	rsync -r -v "$(data_dir)/api_metadata/$(file_to_sync)" "$(db_data_dir)/api_metadata"

sync-access-rights: 
	rsync -r -v "$(data_dir)/access_rights_masterfiles/$(file_to_sync)" "$(db_data_dir)/access_rights"

### Fetching access-rights ###
debug-access-rights: # the gsheet id is going to change with each provider
	python harvesters/fetch_from_gdrive.py \
	--spreadsheet_id="1cLgvhFTPaqjnxTByDejMrwxBM0-o0j1U2Oz-o4oTabs" \
	--worksheet_name="v5" \
	--output_file="$(data_dir)/gdrive_access_rights/$(access_rights_file_prefix).debug.json" 


all-access-rights: snl-access-rights bnl-access-rights bnf-access-rights bcul-access-rights swa-fedgaz-nzz-access-rights
# todo add the rest once their access rights are filled in

snl-access-rights:
	python harvesters/fetch_from_gdrive.py \
	--spreadsheet_id=$(snl_ar_ghseet_id) \
	--worksheet_name=$(ar_worksheet_name) \
	--output_file="$(data_dir)/gdrive_access_rights/$(access_rights_file_prefix).snl.json" 

	python harvesters/access_rights/access_rights_masterfile.py --partner="snl" --data-dir=$(data_dir)

bnl-access-rights:
	python harvesters/fetch_from_gdrive.py \
	--spreadsheet_id=$(bnl_ar_ghseet_id) \
	--worksheet_name=$(ar_worksheet_name) \
	--output_file="$(data_dir)/gdrive_access_rights/$(access_rights_file_prefix).bnl.json" 

	python harvesters/access_rights/access_rights_masterfile.py --partner="bnl" --data-dir=$(data_dir)

bnf-access-rights:
	python harvesters/fetch_from_gdrive.py \
	--spreadsheet_id=$(bnf_ar_ghseet_id) \
	--worksheet_name=$(ar_worksheet_name) \
	--output_file="$(data_dir)/gdrive_access_rights/$(access_rights_file_prefix).bnf.json" 

	python harvesters/access_rights/access_rights_masterfile.py --partner="bnf" --data-dir=$(data_dir)

bcul-access-rights:
	python harvesters/fetch_from_gdrive.py \
	--spreadsheet_id=$(bcul_ar_ghseet_id) \
	--worksheet_name=$(ar_worksheet_name) \
	--output_file="$(data_dir)/gdrive_access_rights/$(access_rights_file_prefix).bcul.json" 

	python harvesters/access_rights/access_rights_masterfile.py --partner="bcul" --data-dir=$(data_dir)

swa-fedgaz-nzz-access-rights:
	python harvesters/fetch_from_gdrive.py \
	--spreadsheet_id=$(swa_fedgaz_nzz_ar_ghseet_id) \
	--worksheet_name=$(ar_worksheet_name) \
	--output_file="$(data_dir)/gdrive_access_rights/$(access_rights_file_prefix).swa_fedgaz_nzz.json" 

	python harvesters/access_rights/access_rights_masterfile.py --partner="swa_fedgaz_nzz" --data-dir=$(data_dir)

kb-access-rights:
	python harvesters/fetch_from_gdrive.py \
	--spreadsheet_id=$(kb_ar_ghseet_id) \
	--worksheet_name=$(ar_worksheet_name) \
	--output_file="$(data_dir)/gdrive_access_rights/$(access_rights_file_prefix).kb.json" 

	python harvesters/access_rights/access_rights_masterfile.py --partner="kb" --data-dir=$(data_dir)

onb-access-rights:
	python harvesters/fetch_from_gdrive.py \
	--spreadsheet_id=$(onb_ar_ghseet_id) \
	--worksheet_name=$(ar_worksheet_name) \
	--output_file="$(data_dir)/gdrive_access_rights/$(access_rights_file_prefix).onb.json" 

	python harvesters/access_rights/access_rights_masterfile.py --partner="onb" --data-dir=$(data_dir)

sub-access-rights:
	python harvesters/fetch_from_gdrive.py \
	--spreadsheet_id=$(sub_ar_ghseet_id) \
	--worksheet_name=$(ar_worksheet_name) \
	--output_file="$(data_dir)/gdrive_access_rights/$(access_rights_file_prefix).sub.json" 

	python harvesters/access_rights/access_rights_masterfile.py --partner="sub" --data-dir=$(data_dir)


