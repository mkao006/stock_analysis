import numpy as np
import pandas as pd
import pandas_datareader as pdr
import datetime
import logging

import seaborn as sns
import matplotlib.pyplot as plt

logger = logging.getLogger()
logging.basicConfig(level=logging.ERROR)

def annualised_return(p0, pT, t):
    return ((pT/p0))**(365/t) - 1


def series_ar(series):
    # check if the series has dates as index.
    if isinstance(series.index, pd.core.indexes.datetimes.DatetimeIndex):
        time = (datetime.date.today() - series.index.date[0]).days
    elif isinstance(series.index, pd.core.indexes.range.RangeIndex):
        time = len(series)
    else:
        raise ValueError
    return annualised_return(series[0], series[-1], time)


def get_sp500(dropna=True):

    start_date = datetime.date(2000, 1, 1)
    # end_date = datetime.date.today()
    sp500raw = pdr.fred.FredReader(['sp500'], start=start_date).read()
    sp500 = sp500raw['sp500']
    if dropna:
        return sp500.dropna()
    else:
        return sp500

class SP500ReturnSimulator():
    def __init__(self, series, number_of_purchase):
        self.series = series
        self.number_of_purchase = number_of_purchase
        self.split_series = np.array_split(self.series, self.number_of_purchase)
        self.bin_max_obs = [s.shape[0] - 1 for s in self.split_series]

    def _plot(self, purchase_series):
        fig, ax = plt.subplots()
        sns.lineplot(x=self.series.index.name,
                     y=self.series.name,
                     data=self.series.reset_index(), ax=ax)
        sns.scatterplot(x=purchase_series.index.name,
                        y=purchase_series.name,
                        data=purchase_series.reset_index(),
                        ax=ax, color='red', zorder=10)
        plt.show()

    def _calculate_return(self, purchasing_index):
        return np.mean([series_ar(self.series[ind:]) for ind in purchasing_index])

    def random_sampling_strategy(self, plot=False, sample=10):
        returns = [] * sample
        for iter in range(sample):
            purchasing_time = [s.sample(1).index[0] for s in self.split_series]
            purchasing_index = [self.series.index.get_loc(i) for i in purchasing_time]
            purchasing_points = self.series.iloc[purchasing_index]
            if plot:
                self._plot(purchasing_points)
        
        returns.append(self._calculate_return(purchasing_index))
        return np.mean(returns)

    def equal_space_strategy(self, plot=False, sample=10):
        returns = [] * sample
        for iter in range(sample):
            purchase_ind = np.random.choice(np.max(self.bin_max_obs), 1)[0]
            purchasing_time = [s[[purchase_ind]].index[0] if purchase_ind <= m else s[[m]].index[0]
                               for s, m in zip(self.split_series, self.bin_max_obs)]
            purchasing_index = [self.series.index.get_loc(i) for i in purchasing_time]
            purchasing_points = self.series.iloc[purchasing_index]
            if plot:
                self._plot(purchasing_points)
        returns.append(self._calculate_return(purchasing_index))
        return np.mean(returns)

    def optimal_return(self, plot=False):
        purchasing_time = [s.idxmin() for s in self.split_series]
        purchasing_index = [self.series.index.get_loc(i) for i in purchasing_time]
        purchasing_points = self.series.iloc[purchasing_index]
        if plot:
            self._plot(purchasing_points)

        return self._calculate_return(purchasing_index)

    def worst_return(self, plot=False):
        # split the data
        purchasing_time = [s.idxmax() for s in self.split_series]
        purchasing_index = [self.series.index.get_loc(i) for i in purchasing_time]
        purchasing_points = self.series.iloc[purchasing_index]        
        if plot:
            self._plot(purchasing_points)

        return self._calculate_return(purchasing_index)
