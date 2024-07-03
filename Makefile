# Variables
db_data_dir = ../impresso-master-db/impresso_db/data
data_dir = data
file_prefix = gsheet_metadata
gsheet_id = 1jkW6cuINgT7SpuvJE7jVW4lpWiCypVuFiQOhuDZ_o1E
file_to_sync = 

# Targets
help:
	@echo "Programmatically export the contents of the metadata google spreadsheet to json."
	@echo "Available targets:"
	@echo "  all   - Export the metadata for all ingestion batches"
	@echo "  impresso1      - Export the metadata for all Impresso 1 data"
	@echo "  bnf      - Export the metadata for all BNF media titles"
	@echo "  bcul       - Export the metadata for all BCUL media titles"
	@echo "  swa-fedgaz     - Export the metadata for all SWA and FedGaz media titles"
	@echo "  sync-gdrive     - Synchronize all or part of the gdrive data folder with the one of the impresso-master-db repository"
	@echo "  sync-apis     - Synchronize all or part of the api data folder with the one of the impresso-master-db repository"
	@echo "  help      - Display this help message"


all: impresso1 bnf bcul swa-fedgaz

impresso1:
	python metadata_harvest/gdrive/main_metadata.py \
	--spreadsheet_id=$(gsheet_id) \
	--worksheet_name="impresso1-collection" \
	--output_file="$(data_dir)/gdrive/$(file_prefix).impresso1.json"

bnf:
	python metadata_harvest/gdrive/main_metadata.py \
	--spreadsheet_id=$(gsheet_id) \
	--worksheet_name="BNF" \
	--output_file="$(data_dir)/gdrive/$(file_prefix).bnf.json"

bcul:
	python metadata_harvest/gdrive/main_metadata.py \
	--spreadsheet_id=$(gsheet_id) \
	--worksheet_name="BCUL" \
	--output_file="$(data_dir)/gdrive/$(file_prefix).bcul.json"

swa-fedgaz:
	python metadata_harvest/gdrive/main_metadata.py \
	--spreadsheet_id=$(gsheet_id) \
	--worksheet_name="SWA-FedGaz" \
	--output_file="$(data_dir)/gdrive/$(file_prefix).swa_fedgaz.json"

sync-gdrive: 
	rsync -r -v "$(data_dir)/gdrive/$(file_to_sync)" "$(db_data_dir)"

sync-apis: 
	rsync -r -v "$(data_dir)/apis/$(file_to_sync)" "$(db_data_dir)"