'''
Usage:
    make_dataset.py dataroma_superinvestor_portfolio -o OUTPUT_FILE
    make_dataset.py sp500_financials -c CONFIG_FILE -d OUTPUT_DIRECTORY

Options:
    -o OUTPUT_FILE          Output location of the file.
    -c CONFIG_FILE          The configure file for QuickFS.
    -d OUTPUT_DIRECTORY     The output directory of the extracted data.
'''

import os
from docopt import docopt
import requests
import pandas as pd
from pandas.core.common import SettingWithCopyWarning
from bs4 import BeautifulSoup
import warnings
from quickfs import read_quickfs_config
from quickfs import QuickFS

warnings.simplefilter(action="ignore", category=SettingWithCopyWarning)
HOME_PAGE_URL = 'https://www.dataroma.com/m/home.php'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:55.0) Gecko/20100101 Firefox/55.0',
}


def get_superinvestor_link():
    '''Function to get the list of all super investors and their
    corresponding portfolio url from the dataroma.com home page.

    '''
    home_page = requests.get(HOME_PAGE_URL, headers=HEADERS)
    home_page_parsed = BeautifulSoup(home_page.content, 'html.parser')
    superinvestor_table = home_page_parsed.find(id='port_body')

    investor_link = dict()
    for li in superinvestor_table.find_all('li'):
        investor_name = li.text.split('Update')[0]
        investor_partial_link = 'https://dataroma.com' + li.find('a')['href']
        investor_link[investor_name] = investor_partial_link

    return investor_link


def extract_portfolio(portfolio_url):
    ''' Parse the value, percent and the name of the stock of a portfolio.
    '''
    page = requests.get(portfolio_url, headers=HEADERS)
    portfolio = pd.read_html(page.text)[0]

    sub_columns = ['Stock', '% of portfolio', 'Shares', 'Value']
    sub_table = portfolio[sub_columns]
    sub_table.columns = ['stock', 'portfolio_pct', 'shares', 'value']
    sub_table['value'] = sub_table['value'].str.replace('\$|,', '').astype('int')
    return sub_table


def concatenate_portfolios(investor_links):
    ''' wrapper function to loop through all the investor and concatenate the portfolios.
    '''
    investor_portfolios = []
    for investor_name, investor_link in investor_links.items():
        investor_portfolio = extract_portfolio(investor_link).assign(investor=investor_name)
        investor_portfolios.append(investor_portfolio)

    return pd.concat(investor_portfolios)


def extract_dataroma_superinvestor_portfolio():
    ''' Extracts the portfolio of superinvestors on dataroma.com.
    '''

    superinvestor_links = get_superinvestor_link()
    superinvestor_portfolios = concatenate_portfolios(superinvestor_links)
    return superinvestor_portfolios

def get_sp500_company_info():
    '''The function extracts the tables from the list of SP500 wiki
    page. The page has 2 tables:

    1. companies that are currently listed
    2. companies added/removed in the past.

    '''
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    response = requests.get(url)
    tables = pd.read_html(response.text)
    return tables

def get_sp500_financial_metrics(opts):
    symbols = get_sp500_company_info()[0]['Symbol'].tolist()

    config = read_quickfs_config(opts['-c'])
    api = QuickFS(api_key=config['default']['api_key'])

    # since we are limited to only 25000 datapoints per day, and each
    # 'all-data' api call uses 100 datapoints, we would need to query
    # the data over 3 days.

    loaded_symbols = [i.replace('.csv', '') for i in os.listdir(opts['-d'])]
    print(loaded_symbols)
    remaining_symbols = [symbol for symbol in symbols if symbol not in loaded_symbols]
    print(f'remaining symbols: {len(remaining_symbols)}')

    for symb in remaining_symbols:
        output_path = f"{opts['-d']}/{symb}.csv"
        all_data = api.get_metrics(qfs_symbol=f'{symb}:US', period='quarterly')
        all_data.to_csv(output_path, index=False)

    api._usage()

if __name__ == '__main__':
    opts = docopt(__doc__)
    print(opts)

    if opts['dataroma_superinvestor_portfolio']:
        superinvestor_portfolio = extract_dataroma_superinvestor_portfolio()
        superinvestor_portfolio.to_csv(opts['-o'], index=False)
    elif opts['sp500_financials']:
        get_sp500_financial_metrics(opts)
    else:
        raise NotImplementedError
