import json
import requests
import pandas as pd
import logging

logger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG)

def read_quickfs_config(file):
    '''read configuration for the quick fs class. please see the
    quickfs_config.ini.template for structure.

    '''
    import configparser
    config = configparser.ConfigParser()
    config.read(file)
    return config

    
class QuickFS():
    ''' Get financial data from Quick FS.

    https://quickfs.net/
    '''
    def __init__(self, api_key):
        self.api_key = api_key

    def _url_builder(self, api_key, symbol, **kwargs):
        if 'metric' in kwargs:
            metric = kwargs['metric']
            return f'https://public-api.quickfs.net/v1/data/{symbol}/{metric}?api_key={api_key}'
        else:
            return f'https://public-api.quickfs.net/v1/data/all-data/{symbol}?api_key={api_key}'
    

    def _usage(self):
        usage = requests.get(f"https://public-api.quickfs.net/v1/usage?api_key={self.api_key}")
        content = json.loads(usage.content)['usage']['quota']
        logger.info(content)

    def get_metrics(self, qfs_symbol, metrics=None, period='quarterly'):
        if metrics:
            # The single metrics API doesn't return dates, which is an issue.
            results = {}
            for metric in metrics:
                metric_url = self._url_builder(self.api_key, qfs_symbol, metric=metric)
                response = requests.get(metric_url)
                parsed_content = json.loads(response.content)
                results.append({metric: parsed_content['data']})
            symbol = qfs_symbol.split(':')[0]
            metrics = pd.DataFrame(results).assign(symbol=symbol)
            return metrics
        else:
            all_data_url = self._url_builder(self.api_key, qfs_symbol)
            response = requests.get(all_data_url)
            parsed_content = json.loads(response.content)
            symbol = parsed_content['data']['metadata']['symbol']
            financials = pd.DataFrame(parsed_content['data']['financials'][period]).assign(symbol=symbol)
            self._usage()
            return financials            


    def get_metadata(self, symbol):
        '''Get metadata of a company

        WARNING: This function uses the same API as the all data and
        thus uses up 100 datapoint quota.

        '''
        url = self._url_builder(self.api_key, symbol)
        response = requests.get(url)
        parsed_content = json.loads(response.content)
        metadata = pd.DataFrame(parsed_content['data']['metadata'], index=[0])

        return metadata
