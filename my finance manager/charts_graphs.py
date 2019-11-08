import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import cm as cm
from tabulate import tabulate

from print_funcs import PrintFuncs


class ChartsGraphs(PrintFuncs):

    def df_stocks(self, to_email: bool = False):
        symbols, lots, data, columns = [], [], [], ['Symbol', 'Lot']
        for symbol, lot in self.stocks.items():
            for lot_i, details in lot.items():
                symbols.append(symbol)
                lots.append(lot_i)
                data.append(details)

                for detail, val in details.items():
                    columns.append(detail)

        columns = sorted(set(columns), key=columns.index)
        df = pd.DataFrame(data=data, columns=columns)
        df.Lot, df.Symbol = lots, symbols
        df = df.fillna(0).sort_values('Market Value ILS', ascending=False).reset_index(drop=True)
        df.index = df.index + 1

        if 'num' in df.columns:
            df = df.drop(columns='num')

        if to_email:
            df = df.drop(columns=['Profit ILS', 'Profit USD'])
            tabulate.PRESERVE_WHITESPACE = True
            return tabulate(df, headers='keys', floatfmt=",.1f", tablefmt='html', numalign='center',
                            stralign='center')

        else:
            return df

    def total_profit(self, numbers_only: bool = False) -> tuple:
        try:
            df = self.df_stocks()
            df_g_s = df.groupby(by='Symbol').sum()
            total_profit_nums = df_g_s['Profit ILS'].sum()

            portfolio_assets = sum([val for (symbol, lot) in self.stocks.items() for (lot_i, details) in lot.items()
                                    for key, val in details.items() if key == 'Market Value ILS'])
            total_profit_percentage = (((
                                                portfolio_assets
                                                + total_profit_nums
                                        )
                                        / portfolio_assets
                                        )
                                       * 100
                                       ) - 100

            if numbers_only:
                return total_profit_percentage, total_profit_nums
            else:
                return f'{total_profit_percentage:,.4f}', f'{total_profit_nums:,.2f}'

        except Exception as e:
            self.LOG.exception('Error in calculating total profit', e)
            if numbers_only:
                return 0, 0
            else:
                return '0.0', '0.0'

    def df_history(self, tabulate_mode: bool = False, to_email: bool = False):
        dates, data, dict_temp = [], {}, {}
        columns = ['Portfolio ILS', 'Portfolio USD', 'Total ILS', 'Total USD', 'Profit %', 'Profit ILS',
                   'Bank CF', 'Trader CF']

        for date, history_dict in self.history_data.items():
            dates.append(date)

            for history_type, val in history_dict.items():

                if history_type == 'market_value':
                    tup1, tup2 = val.values()
                    values = [num for tup in [tup1, tup2] for num in tup]
                    data[date] = {col: val for col, val in zip(columns, values)}

                elif history_type == 'profit':
                    dict_temp[date] = {'Profit %': val[0], 'Profit ILS': val[1]}

                elif history_type == 'bank_cf':
                    dict_temp[date].update({'Bank CF': val})

                elif history_type == 'trader_cf':
                    dict_temp[date].update({'Trader CF': val})

        for date, dict_i in dict_temp.items():
            for key, val in dict_i.items():
                data[date].update({key: val})

        df = pd.DataFrame(index=dates, columns=columns, data=[val for val in data.values()])
        df = df.reindex(columns=['Portfolio ILS', 'Portfolio USD', 'Bank CF', 'Trader CF', 'Total ILS',
                                 'Total USD', 'Profit %', 'Profit ILS'])
        df.insert(0, 'Date', df.index)
        df = df[::-1]

        if tabulate_mode:
            if to_email:  # last week stats only.
                def day_name(s):
                    date_s = s.split('.')
                    date_i = [int(d) for d in date_s]
                    return date_i

                df = df.iloc[:7]
                df = df.drop(columns=['Portfolio USD', 'Total USD'])
                df.Date = df.Date.apply(lambda s: datetime.date(day=day_name(s)[0],
                                                                month=day_name(s)[1],
                                                                year=day_name(s)[2])
                                        .strftime('%A'))
                df = df.rename(columns={'Date': 'Day'})

            return tabulate(df, headers='keys', tablefmt='html', stralign='center',
                            numalign='center', floatfmt=",.2f", showindex=False)

        else:
            return df

    def df_assets(self, to_email: bool = False, normal_mode: bool = False):
        nis_cash = sum([val for (symbol, lot) in self.stocks.items() for (lot_i, details) in lot.items()
                        for key, val in details.items() if key == 'Market Value ILS'])

        data = [
            f'{nis_cash:,.2f}₪',
            self.total_profit()[1] + '₪',
            self.total_profit()[0] + '%',
            f'{self.bank_cf:,.2f}₪',
            f'{self.trader_cf:,.2f}₪',
            f'{nis_cash + self.bank_cf + self.trader_cf:,.2f}₪',
        ]

        labels = [
            'Portfolio Assets',
            'Profit ILS',
            'Profit %',
            'Bank CF',
            'Trader CF',
            'Total Assets',
        ]

        df = pd.DataFrame(data=data, index=labels, columns=[''])
        df = df.transpose()
        if to_email:
            tabulate.PRESERVE_WHITESPACE = True
            if normal_mode:
                return tabulate(df, headers='keys', tablefmt='plain', stralign='center',
                                numalign='center', showindex=False)
            else:
                return tabulate(df, headers='keys', tablefmt='html', stralign='center',
                                numalign='center', showindex=False)
        else:
            return df

    def graph(self, market_value: bool = False, profit_percentage: bool = False, profit_numbers: bool = False,
              save_only: bool = False, date: str = None):

        if date is None:  # for editing graphs date
            date = self.TODAY

        c_map = cm.get_cmap('viridis')

        def random_color():
            return c_map(np.random.choice(np.arange(0, 1, 0.01)))

        colors = [random_color() for _ in range(len(self.stocks.keys()) + 1)]

        if market_value:
            if len(self.df_stocks()) > 0:
                df = self.df_stocks()
                df_g = df.groupby(by=['Symbol']).sum()
                df_g_s = df_g.sort_values('Market Value ILS')
                plt.style.use('ggplot')
                df_g_s.plot.barh(y='Market Value ILS', legend=False, color=colors, figsize=(10, 5))
                plt.xlim(0, df['Market Value ILS'].max() + 2500)
                plt.yticks(fontsize=9, rotation=45), plt.ylabel('')
                plt.title('Market Value ILS', fontsize=15)

                for i, v in enumerate(df_g_s['Market Value ILS']):
                    plt.text(v, i, str(f'{v:,.2f}'))

                if save_only:
                    plt.savefig(self.graphs_save_path + f'\\{date}-Market-Value.png')
                    plt.close('all')
                    self.LOG.info('graph market value saved')
                    return self.graphs_save_path + f'\\{date}-Market-Value.png'

                else:
                    plt.close('all')
                    return plt.show()

            else:
                self.LOG.info('No stocks to show in graph market val bars')
                return None

        if profit_percentage:
            if len(self.df_stocks()) > 0:
                df = self.df_stocks()
                df_g = df.groupby(by=['Symbol']).mean()
                df_g_s = df_g.sort_values('Profit %')
                plt.style.use('ggplot')
                df_g_s.plot.barh(y='Profit %', legend=False, color=colors, figsize=(10, 5))
                plt.xlim(df_g['Profit %'].min() - 5, df_g['Profit %'].max() + 5)
                plt.yticks(fontsize=9, rotation=45), plt.ylabel('')
                plt.title('Profit %', fontsize=15, x=0.5, y=1.08)
                plt.suptitle(f'Total of {self.total_profit()[0]}%', x=0.5, y=0.93)

                for i, v in enumerate(df_g_s['Profit %']):
                    plt.text(v, i, str(round(v, 3)))

                if save_only:
                    plt.savefig(self.graphs_save_path + f'\\{date}-Profit-Prec.png')
                    plt.close('all')
                    self.LOG.info('graph profit percentage saved')
                    return self.graphs_save_path + f'\\{date}-Profit-Prec.png'

                else:
                    plt.close('all')
                    return plt.show()

            else:
                self.LOG.info('No stocks to show in graph profit percentage')
                return None

        if profit_numbers:
            if len(self.df_stocks()) > 0:
                df = self.df_stocks()
                df_g = df.groupby(by='Symbol').sum()
                df_g_m = df_g.sort_values('Profit ILS')
                plt.style.use('ggplot')
                df_g_m.plot.barh(y='Profit ILS', legend=False, color=colors, figsize=(10, 5))
                plt.xlim(df_g['Profit ILS'].min() - 500, df_g['Profit ILS'].max() + 500)
                plt.yticks(fontsize=9, rotation=45), plt.ylabel('')
                plt.title('Profit ILS', fontsize=15, x=0.5, y=1.08)
                plt.suptitle(f'Total of {self.total_profit()[1]} ILS', x=0.5, y=0.93)

                for i, v in enumerate(df_g_m['Profit ILS']):
                    plt.text(v, i, str(f'{v:,.2f}'))

                if save_only:
                    plt.savefig(self.graphs_save_path + f'\\{date}-Profit-Nums.png')
                    plt.close('all')
                    self.LOG.info('graph profit numbers saved')
                    return self.graphs_save_path + f'\\{date}-Profit-Nums.png'

                else:
                    plt.close('all')
                    return plt.show()

            else:
                self.LOG.info('No stocks to show in graph profit nums')
                return None
