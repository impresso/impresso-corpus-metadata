# Variables
db_data_dir = ../impresso-master-db/impresso_db/data
data_dir = data
file_prefix = gsheet_metadata
metadata_gsheet_id = 1jkW6cuINgT7SpuvJE7jVW4lpWiCypVuFiQOhuDZ_o1E
file_to_sync = 

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
	@echo "  help      - Display this help message"


all-metadata: impresso1-metadata bnf-metadata bcul-metadata swa-fedgaz-metadata

impresso1-metadata:
	python harvesters/fetch_from_gdrive.py \
	--spreadsheet_id=$(metadata_gsheet_id) \
	--worksheet_name="impresso1-collection" \
	--output_file="$(data_dir)/gdrive_metadata/$(file_prefix).impresso1.json"

bnf-metadata:
	python harvesters/fetch_from_gdrive.py \
	--spreadsheet_id=$(metadata_gsheet_id) \
	--worksheet_name="BNF" \
	--output_file="$(data_dir)/gdrive_metadata/$(file_prefix).bnf.json"

bcul-metadata:
	python harvesters/fetch_from_gdrive.py \
	--spreadsheet_id=$(metadata_gsheet_id) \
	--worksheet_name="BCUL" \
	--output_file="$(data_dir)/gdrive_metadata/$(file_prefix).bcul.json"

swa-fedgaz-metadata:
	python harvesters/fetch_from_gdrive.py \
	--spreadsheet_id=$(metadata_gsheet_id) \
	--worksheet_name="SWA-FedGaz" \
	--output_file="$(data_dir)/gdrive_metadata/$(file_prefix).swa_fedgaz.json"

sync-gdrive-metadata: 
	rsync -r -v "$(data_dir)/gdrive_metadata/$(file_to_sync)" "$(db_data_dir)/gdrive_metadata"

sync-api-metadata: 
	rsync -r -v "$(data_dir)/api_metadata/$(file_to_sync)" "$(db_data_dir)/api_metadata"