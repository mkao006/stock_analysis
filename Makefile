.PHONY: data

########################################################################
## Get data
########################################################################

get_superinvestor_portfolio:
	python3 src/data/make_dataset.py dataroma_superinvestor_portfolio -o data/raw/dataroma_superinvestor.csv

get_sp500_financial_metrics:
	python3 src/data/make_dataset.py sp500_financials -c quickfs_config.ini -d data/raw/sp500_financial
