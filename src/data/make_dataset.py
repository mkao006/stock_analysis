'''
Usage:
    make_dataset.py dataroma_superinvestor_portfolio -o OUTPUT_FILE

Options:
    -o OUTPUT_FILE          Output location of the file.
'''


from docopt import docopt
import requests
import pandas as pd
from pandas.core.common import SettingWithCopyWarning
from bs4 import BeautifulSoup
import warnings

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

if __name__ == '__main__':
    opts = docopt(__doc__)
    print(opts)

    if opts['dataroma_superinvestor_portfolio']:
        superinvestor_portfolio = extract_dataroma_superinvestor_portfolio()
        superinvestor_portfolio.to_csv(opts['-o'], index=False)
    else:
        raise NotImplementedError
