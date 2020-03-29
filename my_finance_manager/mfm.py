"""
My Finance Manager created to manage all data at one place, data from bank account and investment house portfolio.
Update stocks prices from yahoo finance or from Tel Aviv stock Exchange (TASE).
Get statistics about portfolio history changes, including profit.
View graphs and receive email report with weekly summery of your portfolio.
"""

__version__ = '1.1'
# 1.0 first release
# 1.1 MongoDB version + ThreadPoolExecutor for schedule script


import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import yagmail
import yfinance as yf
from forex_python.converter import CurrencyRates, CurrencyCodes
from matplotlib import cm as cm
from requests_html import HTMLSession
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from tabulate import tabulate

import mongo_db
from config.config import sender_password, sender_email
from exceptions import create_logger, os, datetime


class MyFinanceManager:
    LOG = create_logger()
    TODAY = mongo_db.TODAY
    CR = CurrencyRates()
    CC = CurrencyCodes()

    graphs_save_path = 'media/graphs/'
    days_left = 0  # for changing Meitav Dash website password

    def __init__(self):
        self.LOG.debug('Initializing MFM object')

        self.db = mongo_db.MyMongoDB()

        if not os.path.exists(self.graphs_save_path):  # creating Graphs folder in root dir for future graphs generate.
            self.LOG.debug('Trying to create Graphs folder')
            try:
                os.makedirs(self.graphs_save_path)
                self.LOG.info('Graphs folder created')

            except IOError:
                self.LOG.exception('Error in creating Graphs folder in root dir')
                raise

        self.LOG.info('MFM object created successfully')

    @staticmethod
    def _convert_to_datetime_obj(date_string: str):
        date_string = date_string.strip().replace('.', '/').replace('\\', '/')
        return datetime.datetime.strptime(date_string, '%d/%m/%Y')

    @classmethod
    def currency_converter(cls, i_have: str = None, i_want: str = None, amount=.0,
                           symbol: str = None) -> float or str:
        """

        :param i_have: str, currency i have to convert, like 'USD'.
        :param i_want: str, currency i want to convert to, like 'NIS'.
        :param amount: int or float.
        :param symbol: str, to get symbol sign of currency, like for 'USD' output is '$'.
        :return: float for currency convert, str for symbol.
        """
        if symbol:
            symbol = symbol.upper()
            return cls.CC.get_symbol(symbol)

        else:
            if not i_want or not i_have:
                return 0

            else:
                i_have, i_want = i_have.upper(), i_want.upper()

        if amount == 0:
            return MyFinanceManager.CR.get_rate(i_have, i_want)

        else:
            return MyFinanceManager.CR.convert(i_have, i_want, amount)

    def add_stock(self, symbol: str, date: str, amount: int, buy_price: float, currency: str,
                  tase_index: int or str = 0) -> bool:
        """
        Add stock to portfolio.
        :param symbol: str, like 'VTI'.
        :param date: str, today or full date '28.08.18'.
        :param amount: int.
        :param buy_price: float.
        :param currency: str, like 'USD'.
        :param tase_index: int, if israeli stock (Tel-Aviv Stock Exchange).
        :return: True
        """

        if (currency is 'USD' and tase_index != 0) or (currency is 'ILS' and tase_index == 0):
            raise ValueError

        # convert date to datetime object
        if date.strip().lower() == 'today':
            date = datetime.datetime.today()
        else:
            date = self._convert_to_datetime_obj(date)

        symbol = symbol.upper().strip()
        currency = currency.upper().strip()

        symbol_current_lots_count = self.db.stocks.get_stock_lots_count(symbol)
        if symbol_current_lots_count > 1:
            lot_num = symbol_current_lots_count + 1
        else:
            lot_num = 1

        d = {'symbol': symbol}
        if currency == 'USD':
            start_market_val = buy_price * amount
            current_market_val = self.get_stock_price(symbol) * amount
            converted_c_market_val = np.round(self.CR.convert('USD', 'ILS', current_market_val), 3)

            profit_usd = np.round(current_market_val - start_market_val, 3)
            profit_ils = np.round(self.CR.convert('USD', 'ILS', profit_usd), 3)
            profit_percentage = np.round((((current_market_val / start_market_val) * 100) - 100), 3)

            d.update({
                'Lot_Num': lot_num,
                'Date': date,
                'Amount': amount,
                'Buy_Price': buy_price,
                'Currency': currency,
                'Market_Value USD': current_market_val,
                'Market_Value ILS': converted_c_market_val,
                'Profit_USD': profit_usd,
                'Profit_ILS': profit_ils,
                'Profit_%': profit_percentage,
            })

        elif currency == 'ILS':
            start_market_val = (buy_price * amount) / 100
            current_market_val = (self.get_redemption_price(tase_index) * amount) / 100
            converted_c_market_val = np.round(self.CR.convert('ILS', 'USD', current_market_val), 3)

            profit_ils = np.round(current_market_val - start_market_val, 3)
            profit_usd = np.round(self.CR.convert('ILS', 'USD', profit_ils), 3)
            profit_percentage = np.round((((current_market_val / start_market_val) * 100) - 100), 3)

            d.update({
                'Lot_Num': lot_num,
                'Date': date,
                'Amount': amount,
                'Buy_Price': buy_price,
                'Currency': currency,
                'Market_Value_USD': converted_c_market_val,
                'Market_Value_ILS': current_market_val,
                'Profit_USD': profit_usd,
                'Profit_ILS': profit_ils,
                'TASE_INDEX': tase_index,
                'Profit_%': profit_percentage,
            })

        self.db.stocks.insert_stock(d)
        self.LOG.info(f'{symbol} added to portfolio')
        return True

    def _loop_update_stock(self, symbol, lot_count):
        for lot_num in range(1, lot_count + 1):
            if self.db.stocks.get_field_from_stock(symbol, lot_num, 'Currency') == 'ILS':
                amount = self.db.stocks.get_field_from_stock(symbol, lot_num, 'Amount')
                buy_price = self.db.stocks.get_field_from_stock(symbol, lot_num, 'Buy_Price')
                start_market_val = (buy_price * amount) / 100

                tase_index = self.db.stocks.get_field_from_stock(symbol, lot_num, 'TASE_INDEX')
                updated_buy_price = self.get_redemption_price(tase_index)

                current_market_val = (updated_buy_price * amount) / 100
                converted_c_market_val = np.round(self.CR.convert('ILS', 'USD', current_market_val), 3)

                profit_ils = np.round(current_market_val - start_market_val, 3)
                profit_usd = np.round(self.CR.convert('ILS', 'USD', profit_ils), 3)
                profit_percentage = np.round((((current_market_val / start_market_val) * 100) - 100), 3)

                self.db.stocks.update_stock_lot(symbol, lot_num, current_market_val, converted_c_market_val,
                                                profit_usd, profit_ils, profit_percentage)

            else:
                amount = self.db.stocks.get_field_from_stock(symbol, lot_num, 'Amount')
                buy_price = self.db.stocks.get_field_from_stock(symbol, lot_num, 'Buy_Price')
                start_market_val = buy_price * amount

                updated_buy_price = self.get_stock_price(symbol)

                current_market_val = updated_buy_price * amount
                converted_c_market_val = np.round(self.CR.convert('USD', 'ILS', current_market_val), 3)

                profit_usd = np.round(current_market_val - start_market_val, 3)
                profit_ils = np.round(self.CR.convert('USD', 'ILS', profit_usd), 3)
                profit_percentage = np.round((((current_market_val / start_market_val) * 100) - 100), 3)

                self.db.stocks.update_stock_lot(symbol, lot_num, converted_c_market_val, current_market_val,
                                                profit_usd, profit_ils, profit_percentage)

    def update_stocks_price(self, symbol: str = None) -> bool:
        if symbol:
            self._loop_update_stock(symbol, self.db.stocks.get_stock_lots_count(symbol))
            self.LOG.info(f'{symbol} price updated')
        else:
            for d in self.db.stocks.get_stock_lots_count(per_stock=True):
                self._loop_update_stock(d['symbol'], d['count'])
            self.LOG.info('All stocks prices updated')

        self.db.last_modified.update_field(field_name='stocks')
        return True

    def update_bank_trader_foreign_currency(self, symbol: str,
                                            u_bank_usd_val: float = None, u_trader_usd_val: float = None):
        if u_trader_usd_val:
            converted_trader_usd_val = self.currency_converter(symbol, 'ILS', u_trader_usd_val)
            self.db.foreign_currencies.update_foreign_currency(symbol, 'Trader', converted_trader_usd_val,
                                                               u_trader_usd_val)
            self.LOG.info('Trader Foreign Currency updated')

        elif u_bank_usd_val:
            converted_bank_usd_val = self.currency_converter('ILS', symbol, u_bank_usd_val)
            self.db.foreign_currencies.update_foreign_currency(symbol, 'Bank', u_bank_usd_val, converted_bank_usd_val)
            self.LOG.info('Bank Foreign Currency updated')

    def update_bank_trader_cf(self, u_bank_cf: float = None, u_trader_cf: float = None) -> bool:
        if u_bank_cf:
            self.db.history_data.update_bank(u_bank_cf)
            self.db.last_modified.update_field(field_name='bank')
            self.LOG.info('Bank cash flow updated')

        if u_trader_cf:
            self.db.history_data.update_trader(u_trader_cf)
            self.db.last_modified.update_field(field_name='trader')
            self.LOG.info('Trader cash flow updated')

        return True

    def update_history_data(self):
        total_profit = self.total_profit(numbers_only=True)
        total_assets_ils = self.total_assets()
        total_assets_usd = self.total_assets(in_usd=True)

        self.db.history_data.update_all(
            total_profit=total_profit, total_assets_ils=total_assets_ils,
            total_assets_usd=total_assets_usd
        )
        return True

    def remove_stock(self, symbol: str, sell_amount: int):
        """
        Removes stock's shares by FIFO; first lot to came it - first to come out.
        ** works recursively.
        """
        lot_count = self.db.stocks.get_stock_lots_count(symbol)

        for lot_num in range(1, lot_count + 1):
            current_amount = self.db.stocks.get_field_from_stock(symbol, lot_num, 'Amount')

            if current_amount > sell_amount:
                self.db.stocks.update_stock_amount(symbol, lot_num, sell_amount)
                self.LOG.info(f'{sell_amount} shares of {symbol} removed from lot {lot_num}')
                return self.update_stocks_price(symbol)

            elif current_amount < sell_amount:
                new_amount = sell_amount - current_amount
                self.db.stocks.remove_stock(symbol, lot_num)
                self.LOG.info(f'{sell_amount} shares of {symbol} removed from lot {lot_num}')
                return self.remove_stock(symbol, new_amount)

            elif current_amount == sell_amount:
                if self.db.stocks.get_stock_lots_count(symbol) > 1:  # if more than 1 lot remove only first lot
                    self.db.stocks.remove_stock(symbol, lot_num)
                    self.LOG.info(f'{sell_amount} shares of {symbol} removed from lot {lot_num}')
                else:  # if only 1 lot remove the symbol from stocks db
                    self.db.stocks.remove_stock(symbol)
                    self.LOG.info(f'{symbol} removed from portfolio')
                return self.update_stocks_price(symbol)

    def get_redemption_price(self, fund_id: int) -> float:

        if isinstance(fund_id, str):
            return np.round(self.currency_converter(fund_id, 'ILS') * 100, 3)

        try:
            self.LOG.debug(f'Getting redemption price for {fund_id} with BizPortal API')

            url = f'http://externalapi.bizportal.co.il/mobile/m/GetQuote?id={fund_id}'
            with requests.get(url) as r:
                red_price = r.json()['Quote']['RedPrice']
            return float(red_price)

        except:
            self.LOG.exception(f'Error while trying to get redemption price from BizPortal API')

            try:
                self.LOG.debug(f'Getting redemption price for {fund_id} with HTMLSession')
                session = HTMLSession()
                url = 'https://maya.tase.co.il/fund/5109889'
                r = session.get(url)
                r.html.render()
                red_price = r.html.find('div.redemptionPriceValue.ng-binding')[0].text.split(' ')[0]
                return float(red_price)

            except Exception:
                self.LOG.exception(f'Error while trying to get redemption price with HTMLSession')
                raise

    def scrap_redemption_price(self, fund_num_exchange: int) -> float:

        self.LOG.info(f'start web scrap for {fund_num_exchange} with web driver')

        if isinstance(fund_num_exchange, str):
            return np.round(self.currency_converter(fund_num_exchange, 'ILS') * 100, 3)

        try:
            url = f'https://maya.tase.co.il/fund/{fund_num_exchange}'

            c_options = Options()
            c_options.headless = True
            c_options.add_argument("--log-level=3")

            driver = webdriver.Chrome(options=c_options)
            driver.get(url)

            price = driver.find_element_by_class_name('redemptionPriceValue.ng-binding').text.split()[0]

            driver.quit()
            return float(price)

        except Exception as e:
            self.LOG.exception(f'Error while trying to web scrap redemption price with web driver')
            raise e

    @staticmethod
    def get_stock_price(symbol: str) -> float:
        stock = yf.Ticker(symbol)
        stock_price = stock.history(period='1d').iloc[0, 3]
        return float(stock_price)

    def df_stocks(self, to_email: bool = False):
        data = self.db.stocks.fetch_data_for_df()
        data.extend(self.db.foreign_currencies.fetch_data_for_df())
        df = pd.DataFrame(data=[d for d in data])
        df = df.reindex(columns=['Symbol', 'Lot', 'Date', 'Amount', 'Buy_Price', 'Currency',
                                 'Market_Value_ILS', 'Profit_ILS', 'Profit_%'])
        df.sort_values(by=['Market_Value_ILS'], ascending=False, inplace=True)

        df.Date = df.Date.dt.strftime('%d-%m-%Y')

        df = df.replace({'NaT': '-'})

        df.Amount = df.Amount.fillna(0).astype(int)
        df.Amount = df.Amount.replace({0: '-'})

        if to_email:
            df.fillna('-', inplace=True)
            df = df.drop(columns=['Profit_ILS', 'Buy_Price'])
            tabulate.PRESERVE_WHITESPACE = True
            return tabulate(df, headers='keys', floatfmt=",.1f", tablefmt='html', numalign='center',
                            stralign='center', showindex=False)
        else:
            return df

    def total_profit(self, numbers_only: bool = False) -> tuple:
        try:
            total_profit_percentage = (((
                                                self.db.stocks.sum_portfolio_field('Market_Value_ILS')
                                                + self.db.stocks.sum_portfolio_field('Profit_ILS')
                                        )
                                        / self.db.stocks.sum_portfolio_field('Market_Value_ILS')
                                        )
                                       * 100
                                       ) - 100

            if numbers_only:
                return total_profit_percentage, self.db.stocks.sum_portfolio_field('Profit_ILS')
            else:
                return f'{total_profit_percentage:,.4f}', f'{self.db.stocks.sum_portfolio_field("Profit_ILS"):,.2f}'

        except Exception:
            if numbers_only:
                return 0, 0
            else:
                return '0.0', '0.0'

    def df_history(self, tabulate_output: bool = False, to_email: bool = False):
        data = self.db.history_data.fetch_data_for_df()
        df = pd.DataFrame(data=[d for d in data])
        df = df.reindex(columns=['Date', 'Portfolio_ILS', 'Profit_ILS', 'Profit_%', 'Foreign_Currencies',
                                 'Bank_CF', 'Trader_CF', 'Total_ILS', 'Total_USD'])
        df.Date = df.Date.dt.strftime('%d-%m-%Y')
        df.Foreign_Currencies = df.Foreign_Currencies.round(2)

        if tabulate_output:
            df.fillna('-', inplace=True)
            if to_email:  # last week stats only.
                def day_name(s):
                    date_s = s.split('-')
                    date_i = [int(d) for d in date_s]
                    return date_i

                df = df.iloc[:7]
                df = df.drop(columns=['Total_USD'])
                df.Date = df.Date.apply(lambda s: datetime.date(day=day_name(s)[0],
                                                                month=day_name(s)[1],
                                                                year=day_name(s)[2])
                                        .strftime('%A'))
                df = df.rename(columns={'Date': 'Day'})

            return tabulate(df, headers='keys', tablefmt='html', stralign='center',
                            numalign='center', floatfmt=",.2f", showindex=False)

        else:
            df.index = df.Date
            df.drop('Date', inplace=True)
            return df

    def total_assets(self, in_usd: bool = False) -> float:
        total_assets = self.db.stocks.sum_portfolio_field('Market_Value_ILS') \
                       + self.db.history_data.get_latest_bank_cf() \
                       + self.db.history_data.get_latest_trader_cf() \
                       + self.db.foreign_currencies.sum_foreign_currency_field('Market_Value_ILS') \

        if in_usd:
            return self.currency_converter('ILS', 'USD', total_assets)
        else:
            return total_assets

    def df_assets(self, to_email: bool = False, plain_text: bool = False):

        profits = self.total_profit(numbers_only=True)
        total_assets = self.total_assets()
        foreign_currencies = self.db.foreign_currencies.sum_foreign_currency_field('Market_Value_ILS')
        data = [
            f'{self.db.stocks.sum_portfolio_field("Market_Value_ILS"):,.2f}₪',
            f'{profits[1]:,.2f} ₪',
            f'{profits[0]:,.2f} %',
            f'{foreign_currencies:,.2f} ₪',
            f'{self.db.history_data.get_latest_bank_cf():,.2f}₪',
            f'{self.db.history_data.get_latest_trader_cf():,.2f}₪',
            f'{total_assets:,.2f}₪',
        ]

        labels = [
            'Portfolio Assets',
            'Profit ILS',
            'Profit %',
            'Foreign Currencies',
            'Bank CF',
            'Trader CF',
            'Total Assets',
        ]

        df = pd.DataFrame(data=data, index=labels, columns=[''])
        df = df.transpose()
        if to_email:
            tabulate.PRESERVE_WHITESPACE = True
            if plain_text:
                return tabulate(df, headers='keys', tablefmt='plain', stralign='center',
                                numalign='center', showindex=False)
            else:
                return tabulate(df, headers='keys', tablefmt='html', stralign='center',
                                numalign='center', showindex=False)
        else:
            return df

    def graph(self, market_value: bool = False, profit_percentage: bool = False, profit_numbers: bool = False,
              save_only: bool = False):
        df = self.df_stocks()
        profits = self.total_profit()
        c_map = cm.get_cmap('viridis')

        def random_color():
            return c_map(np.random.choice(np.arange(0, 1, 0.01)))

        stocks_count = len(self.db.stocks.get_stocks_names())
        colors = [random_color() for _ in range(stocks_count + 1)]

        if market_value:
            if len(df) > 0:
                df_g = df.groupby(by=['Symbol']).sum()
                df_g_s = df_g.sort_values('Market_Value_ILS')
                plt.style.use('ggplot')
                df_g_s.plot.barh(y='Market_Value_ILS', legend=False, color=colors, figsize=(10, 5))
                plt.xlim(0, df['Market_Value_ILS'].max() + 2500)
                plt.yticks(fontsize=9, rotation=45), plt.ylabel('')
                plt.title('Market Value ILS', fontsize=15)

                for i, v in enumerate(df_g_s['Market_Value_ILS']):
                    plt.text(v, i, str(f'{v:,.2f}'))

                if save_only:
                    plt.savefig(self.graphs_save_path + f'{self.TODAY}-Market-Value.png')
                    plt.close('all')
                    self.LOG.info('Graph market value saved')
                    return self.graphs_save_path + f'{self.TODAY}-Market-Value.png'

                else:
                    plt.close('all')
                    return plt.show()

            else:
                self.LOG.info('No stocks to show in graph market val bars')
                return None

        if profit_percentage:
            if len(df) > 0:
                df_g = df.dropna().groupby(by=['Symbol']).mean()
                df_g_s = df_g.sort_values('Profit_%')
                plt.style.use('ggplot')
                df_g_s.plot.barh(y='Profit_%', legend=False, color=colors, figsize=(10, 5))
                plt.xlim(df_g['Profit_%'].min() - 5, df_g['Profit_%'].max() + 5)
                plt.yticks(fontsize=9, rotation=45), plt.ylabel('')
                plt.title('Profit_%', fontsize=15, x=0.5, y=1.08)
                plt.suptitle(f'Total of {profits[0]}%', x=0.5, y=0.93)

                for i, v in enumerate(df_g_s['Profit_%']):
                    plt.text(v, i, str(round(v, 3)))

                if save_only:
                    plt.savefig(self.graphs_save_path + f'{self.TODAY}-Profit-Prec.png')
                    plt.close('all')
                    self.LOG.info('Graph profit percentage saved')
                    return self.graphs_save_path + f'{self.TODAY}-Profit-Prec.png'

                else:
                    plt.close('all')
                    return plt.show()

            else:
                self.LOG.info('No stocks to show in graph profit percentage')
                return None

        if profit_numbers:
            if len(df) > 0:
                df_g = df.dropna().groupby(by=['Symbol']).sum()
                df_g_m = df_g.sort_values('Profit_ILS')
                plt.style.use('ggplot')
                df_g_m.plot.barh(y='Profit_ILS', legend=False, color=colors, figsize=(10, 5))
                plt.xlim(df_g['Profit_ILS'].min() - 500, df_g['Profit_ILS'].max() + 500)
                plt.yticks(fontsize=9, rotation=45), plt.ylabel('')
                plt.title('Profit_ILS', fontsize=15, x=0.5, y=1.08)
                plt.suptitle(f'Total of {profits[1]} ILS', x=0.5, y=0.93)

                for i, v in enumerate(df_g_m['Profit_ILS']):
                    plt.text(v, i, str(f'{v:,.2f}'))

                if save_only:
                    plt.savefig(self.graphs_save_path + f'{self.TODAY}-Profit-Nums.png')
                    plt.close('all')
                    self.LOG.info('Graph profit numbers saved')
                    return self.graphs_save_path + f'{self.TODAY}-Profit-Nums.png'

                else:
                    plt.close('all')
                    return plt.show()

            else:
                self.LOG.info('No stocks to show in graph profit nums')
                return None

    def send_fancy_email(self, receiver_email: str):

        subject = 'MFM App Report'

        body1 = f'<br><br><center>' \
                f'<h2><b>MyFinanceManager Weekly Report</b></h2>' \
                f'<h3><br>{self.df_assets(to_email=True)}</h3>' \
                f'</center>'

        img = self.graph(profit_percentage=True, save_only=True)

        body2 = f'<br><center>' \
                f'<h3><u>Portfolio History Stats</u></h3>' \
                f'{self.df_history(to_email=True, tabulate_output=True)}</center>'

        body3 = f'<br><center>' \
                f'<h3><u>Current Holdings</u></h3>' \
                f'{self.df_stocks(to_email=True)}</center>' \
                f'<br><br><br><br><big>End of report.</big>' \
                f'<br><small>Sent by MyFinanceManager.</small>'

        contents = [body1, yagmail.inline(img), body2, body3]

        if self.days_left and (self.days_left < 7 and self.days_left != 0):
            body_0 = f'<br><center><h4><u>Warning:</u><br>' \
                     f'{self.days_left} to update login password in trader site.</h4></center><br>'
            contents.insert(0, body_0)

        if self.db.history_data.get_latest_trader_cf() and (self.db.history_data.get_latest_trader_cf() < 50):
            body_1 = f'<br><center><h4><u>Warning:</u><br>' \
                     f'Balance in trader is: {self.db.history_data.get_latest_trader_cf()},<br>' \
                     f'consider adding cash to trader balance.</h4></center><br>'
            contents.insert(0, body_1)

        try:
            self.LOG.debug('Trying to send fancy text email message')
            yag = yagmail.SMTP(sender_email, sender_password)
            yag.send(receiver_email, subject, contents)
            self.LOG.info(f'Email sent successfully to {receiver_email}')
            return True

        except Exception:
            self.LOG.exception('Error in sending plain text email message')
            raise
