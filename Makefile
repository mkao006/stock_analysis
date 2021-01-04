.PHONY: data

########################################################################
## Get data
########################################################################

get_superinvestor_portfolio:
	python3 src/data/make_dataset.py dataroma_superinvestor_portfolio -o data/raw/dataroma_superinvestor.csv
