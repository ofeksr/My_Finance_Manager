"""
My Finance Manager created to manage all data at one place, data from bank account and investment house portfolio.
Update stocks prices from yahoo finance or from Tel Aviv stock Exchange (TASE).
Get statistics about portfolio history changes, including profit.
View graphs and receive email report with weekly summery of your portfolio.
"""

import os
from datetime import datetime

import numpy as np
import requests
from forex_python.converter import CurrencyRates, CurrencyCodes
from requests_html import HTMLSession
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from yahoo_fin import stock_info

import mfm_exceptions

LOG = mfm_exceptions.create_logger()


class BasicFunctions:

    LOG = LOG
    DEFAULT_SAVE_PATH = 'database/'
    TODAY = datetime.strftime(datetime.today(), '%d.%m.%Y')
    NOW = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    CR = CurrencyRates()
    CC = CurrencyCodes()
    days_left = 0  # for changing Meitav Dash website password

    def __init__(self, data=None, bank_cf: float = 0., trader_cf: float = 0., user_email: str = None):
        self.LOG.debug('Initialising MFM object')

        self.save_path = 'database/'
        self.graphs_save_path = 'media/graphs/'

        if data:
            self.stocks = data['stocks']
            self.symbol_buy_count = data['symbol buy count']
            self.bank_cf = data['bank_cf']
            self.trader_cf = data['trader_cf']
            self.user_email = data['user_email']
            self.update_dates = data['update_dates']
            try:
                self.history_data = data['history_data']
            except:
                self.history_data = {}

        else:
            self.stocks, self.symbol_buy_count, self.history_data = {}, {}, {}
            self.bank_cf = bank_cf
            self.trader_cf = trader_cf
            self.user_email = user_email

            self.update_dates = {
                'stocks': self.NOW,
                'bank_trader': self.NOW,
            }

        if not os.path.exists(self.graphs_save_path):  # creating Graphs folder in root dir for future graphs generate.
            self.LOG.debug('Trying to create Graphs folder')
            try:
                os.makedirs(self.graphs_save_path)
                self.LOG.info('Graphs folder created')

            except IOError:
                self.LOG.exception('Error in creating Graphs folder in root dir')
                raise

        self.LOG.info('MFM object created successfully')

    @classmethod
    def currency_converter(cls, i_have: str = None, i_want: str = None, amount: int or float = 0,
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
            return BasicFunctions.CR.get_rate(i_have, i_want)

        else:
            return BasicFunctions.CR.convert(i_have, i_want, amount)

    def add_stock(self, symbol: str, date: str, amount: int, buy_price: float, currency: str,
                  fund_num_exchange: int or str = 0) -> bool:
        """
        Add stock to portfolio.
        :param symbol: str, like 'VTI'.
        :param date: str, today or full date '28.08.18'.
        :param amount: int.
        :param buy_price: float.
        :param currency: str, like 'USD'.
        :param fund_num_exchange: int, if israeli stock (TASE).
        :return: True
        """

        if (currency is 'USD' and fund_num_exchange != 0) or (currency is 'ILS' and fund_num_exchange == 0):
            raise ValueError

        date = date.replace('/', '.').replace('\\', '.')
        symbol = symbol.upper()
        currency = currency.upper()

        if date.lower() == 'today':
            date = self.TODAY

        if symbol in self.symbol_buy_count:
            self.symbol_buy_count[symbol] += 1
            i = str(self.symbol_buy_count[symbol])

            if currency == 'USD':
                start_market_val = buy_price * amount
                current_market_val = stock_info.get_live_price(symbol) * amount
                converted_c_market_val = np.round(self.CR.convert('USD', 'ILS', current_market_val), 3)
                profit_usd = np.round(current_market_val - start_market_val, 3)
                profit_ils = np.round(self.CR.convert('USD', 'ILS', profit_usd), 3)
                profit = np.round((((current_market_val / start_market_val) * 100) - 100), 3)
                self.stocks[symbol].update(
                    {
                        'Lot ' + i: {
                            'Date': date,
                            'Amount': amount,
                            'Buy Price': buy_price,
                            'Currency': currency,
                            'Market Value USD': current_market_val,
                            'Market Value ILS': converted_c_market_val,
                            'Profit USD': profit_usd,
                            'Profit ILS': profit_ils,
                            'Profit %': profit
                        }
                    }
                )

            elif currency == 'ILS':
                start_market_val = (buy_price * amount) / 100
                current_market_val = (self.get_redemption_price(fund_num_exchange) * amount) / 100
                converted_c_market_val = np.round(self.CR.convert('ILS', 'USD', current_market_val), 3)
                profit_ils = np.round(current_market_val - start_market_val, 3)
                profit_usd = np.round(self.CR.convert('ILS', 'USD', profit_ils), 3)
                profit = np.round((((current_market_val / start_market_val) * 100) - 100), 3)
                self.stocks[symbol].update(
                    {
                        'Lot ' + i: {
                                'Date': date,
                                'Amount': amount,
                                'Buy Price': buy_price,
                                'Currency': currency,
                                'Market Value USD': converted_c_market_val,
                                'Market Value ILS': current_market_val,
                                'Profit USD': profit_usd,
                                'Profit ILS': profit_ils,
                                'num': fund_num_exchange,
                                'Profit %': profit
                        }
                    }
                )

        elif currency == 'USD':
            self.symbol_buy_count[symbol] = 1
            start_market_val = buy_price * amount
            current_market_val = stock_info.get_live_price(symbol) * amount
            converted_c_market_val = np.round(self.CR.convert('USD', 'ILS', current_market_val), 3)
            profit_usd = np.round(current_market_val - start_market_val, 3)
            profit_ils = np.round(self.CR.convert('USD', 'ILS', profit_usd), 3)
            profit = np.round((((current_market_val / start_market_val) * 100) - 100), 3)
            self.stocks[symbol] = {
                'Lot 1': {
                    'Date': date,
                    'Amount': amount,
                    'Buy Price': buy_price,
                    'Currency': currency,
                    'Market Value USD': current_market_val,
                    'Market Value ILS': converted_c_market_val,
                    'Profit USD': profit_usd,
                    'Profit ILS': profit_ils,
                    'Profit %': profit
                }
            }

        elif currency == 'ILS':
            self.symbol_buy_count[symbol] = 1
            start_market_val = (buy_price * amount) / 100
            current_market_val = (self.get_redemption_price(fund_num_exchange) * amount) / 100
            converted_c_market_val = np.round(self.CR.convert('ILS', 'USD', current_market_val), 3)
            profit_ils = np.round(current_market_val - start_market_val, 3)
            profit_usd = np.round(self.CR.convert('ILS', 'USD', profit_ils), 3)
            profit = np.round((((current_market_val / start_market_val) * 100) - 100), 3)
            self.stocks[symbol] = {
                'Lot 1': {
                        'Date': date,
                        'Amount': amount,
                        'Buy Price': buy_price,
                        'Currency': currency,
                        'Market Value USD': converted_c_market_val,
                        'Market Value ILS': current_market_val,
                        'Profit USD': profit_usd,
                        'Profit ILS': profit_ils,
                        'num': fund_num_exchange,
                        'Profit %': profit
                }
            }

        self.LOG.info(f'{symbol} added to portfolio')
        return True

    def update_stocks_price(self, symbol: str = None) -> bool:

        flag = False  # flag for updating specific stock.

        if symbol is None:
            flag = True  # means update all stocks.

        for stock, lot in self.stocks.items():

            if flag is False and stock != symbol:
                continue

            self.LOG.info(f'Updating {stock} price')

            for lot_i in lot:
                if self.stocks[stock][lot_i]['Currency'] == 'ILS':
                    amount = self.stocks[stock][lot_i]['Amount']
                    buy_price = self.stocks[stock][lot_i]['Buy Price']
                    start_market_val = (buy_price * amount) / 100
                    fund_num_exchange = self.stocks[stock][lot_i]['num']
                    updated_buy_price = self.get_redemption_price(fund_num_exchange)
                    current_market_val = (updated_buy_price * amount) / 100
                    converted_c_market_val = np.round(self.CR.convert('ILS', 'USD', current_market_val), 3)
                    profit_ils = np.round(current_market_val - start_market_val, 3)
                    profit_usd = np.round(self.CR.convert('ILS', 'USD', profit_ils), 3)
                    profit = np.round((((current_market_val / start_market_val) * 100) - 100), 3)

                    self.stocks[stock][lot_i]['Market Value ILS'] = current_market_val
                    self.stocks[stock][lot_i]['Market Value USD'] = converted_c_market_val
                    self.stocks[stock][lot_i]['Profit %'] = profit
                    self.stocks[stock][lot_i]['Profit USD'] = profit_usd
                    self.stocks[stock][lot_i]['Profit ILS'] = profit_ils

                    self.LOG.info(f'Finished update for {stock}')

                else:
                    amount = self.stocks[stock][lot_i]['Amount']
                    buy_price = self.stocks[stock][lot_i]['Buy Price']
                    start_market_val = buy_price * amount
                    updated_buy_price = stock_info.get_live_price(stock)
                    current_market_val = updated_buy_price * amount
                    converted_c_market_val = np.round(self.CR.convert('USD', 'ILS', current_market_val), 3)
                    profit_usd = np.round(current_market_val - start_market_val, 3)
                    profit_ils = np.round(self.CR.convert('USD', 'ILS', profit_usd), 3)
                    profit = np.round((((current_market_val / start_market_val) * 100) - 100), 3)

                    self.stocks[stock][lot_i]['Market Value ILS'] = converted_c_market_val
                    self.stocks[stock][lot_i]['Market Value USD'] = current_market_val
                    self.stocks[stock][lot_i]['Profit %'] = profit
                    self.stocks[stock][lot_i]['Profit USD'] = profit_usd
                    self.stocks[stock][lot_i]['Profit ILS'] = profit_ils

                    self.LOG.debug(f'Finished updating {stock} price')

        self.update_dates.update({'stocks': self.NOW})

        self.LOG.info('All stocks prices updated')
        return True

    def modify_stock_price(self, symbol: str, current_price: float or int) -> bool:  # for manual update of stock price
        symbol = symbol.upper()
        for stock, lot in self.stocks.items():
            if stock == symbol:

                for lot_i in lot:
                    if self.stocks[symbol][lot_i]['Currency'] == 'ILS':
                        start_market_val = (self.stocks[symbol][lot_i]['Buy Price'] *
                                            self.stocks[symbol][lot_i]['Amount']) / 100
                        current_market_val = (current_price * self.stocks[symbol][lot_i]['Amount']) / 100
                        converted_c_market_val = np.round(self.CR.convert('ILS', 'USD', current_market_val), 3)
                        profit_ils = np.round(current_market_val - start_market_val, 3)
                        profit_usd = np.round(self.CR.convert('ILS', 'USD', profit_ils), 3)
                        profit = np.round((((current_market_val / start_market_val) * 100) - 100), 3)

                        self.stocks[symbol].update(
                            {
                                lot_i: {
                                    'Date': self.stocks[symbol][lot_i]['Date'],
                                    'Amount': self.stocks[symbol][lot_i]['Amount'],
                                    'Buy Price': current_price,
                                    'Currency': self.stocks[symbol][lot_i]['Currency'],
                                    'Market Value USD': converted_c_market_val,
                                    'Market Value ILS': current_market_val,
                                    'Profit %': profit,
                                    'Profit USD': profit_usd,
                                    'Profit ILS': profit_ils
                                }
                            }
                        )

                    else:
                        start_market_val = self.stocks[symbol][lot_i]['Buy Price'] * \
                                           self.stocks[symbol][lot_i]['Amount']
                        current_market_val = current_price * self.stocks[symbol][lot_i]['Amount']
                        converted_c_market_val = np.round(self.CR.convert('USD', 'ILS', current_market_val), 3)
                        profit_usd = np.round(current_market_val - start_market_val, 3)
                        profit_ils = np.round(self.CR.convert('USD', 'ILS', profit_usd), 3)
                        profit = np.round((((current_market_val / start_market_val) * 100) - 100), 3)

                        self.stocks[symbol].update(
                            {
                                lot_i: {
                                    'Date': self.stocks[symbol][lot_i]['Date'],
                                    'Amount': self.stocks[symbol][lot_i]['Amount'],
                                    'Buy Price': current_price,
                                    'Currency': self.stocks[symbol][lot_i]['Currency'],
                                    'Market Value USD': current_market_val,
                                    'Market Value ILS': converted_c_market_val,
                                    'Profit %': profit,
                                    'Profit USD': profit_usd,
                                    'Profit ILS': profit_ils
                                }
                            }
                        )

        self.LOG.info(f'{symbol} current price modified')
        return True

    def update_bank_trader_cf(self, u_bank_cf: int or float = None, u_trader_cf: int or float = None) -> bool:
        if u_bank_cf:
            self.bank_cf = u_bank_cf
            self.LOG.info('Bank cash flow updated')

        if u_trader_cf:
            self.trader_cf = u_trader_cf
            self.LOG.info('Trader cash flow updated')

        self.update_dates.update(
            {
                'bank_trader': self.NOW
            }
        )
        return True

    def remove_stock(self, symbol: str, amount: int or float):
        try:
            self.LOG.info(f'Removing {symbol} from portfolio')
            for stock, lot in self.stocks.items():
                if stock == symbol:

                    for lot_i in list(lot):
                        if self.stocks[symbol][lot_i]['Amount'] > amount:
                            self.stocks[symbol][lot_i]['Amount'] -= amount
                            return self.update_stocks_price(symbol)

                        elif self.stocks[symbol][lot_i]['Amount'] < amount:
                            new_amount = amount - self.stocks[symbol][lot_i]['Amount']
                            self.stocks[symbol].pop(lot_i, None)
                            return self.remove_stock(symbol, new_amount)

                        elif self.stocks[symbol][lot_i]['Amount'] == amount:
                            if len(self.stocks[symbol].keys()) > 1:
                                self.stocks[symbol].pop(lot_i, None)

                            else:
                                self.stocks.pop(symbol, None)
                            return self.update_stocks_price(symbol)

        except Exception as e:
            self.LOG.exception(f'Error in removing {symbol} from portfolio')
            raise e

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
