import numpy as np

from __init__ import BasicFunctions


class PrintFuncs(BasicFunctions):
    def show_stocks(self, symbol: str = None) -> str:
        if symbol is None:
            output = []
            for symbol, lot in self.stocks.items():
                for lot_i, details in lot.items():
                    output.append(f'\n\nHolding Symbol: {symbol}\n')

                    for key, val in details.items():
                        if key in ['Market Value USD', 'Market Value ILS', 'Profit ILS', 'Profit USD', 'Profit %']:
                            output.append(f'{key}: {val:,}, ')

                        else:
                            output.append(f'{key}: {val}, ')

            return ''.join(output)

        else:
            symbol = symbol.upper()
            output = [f'Holding Symbol: {symbol}\n']
            for lot_i, details in self.stocks[symbol].items():
                for key, val in details.items():
                    if key in ['Market Value USD', 'Market Value ILS', 'Profit ILS', 'Profit USD', 'Profit %']:
                        output.append(f'{key}: {val:,}, ')

                    else:
                        output.append(f'{key}: {val}, ')

            return ''.join(output)

    def total_assets(self, portfolio_only: bool = False, numbers_only: bool = False) -> str or float:
        usd_cash = sum([val for (symbol, lot) in self.stocks.items() for (lot_i, details) in lot.items()
                        for key, val in details.items() if key == 'Market Value USD'])
        nis_cash = sum([val for (symbol, lot) in self.stocks.items() for (lot_i, details) in lot.items()
                        for key, val in details.items() if key == 'Market Value ILS'])

        if portfolio_only and numbers_only:
            return np.round(nis_cash, 3), np.round(usd_cash, 3)

        if not portfolio_only and not numbers_only:
            return f'\nPortfolio Assets: {usd_cash:,.2f} $ | {nis_cash:,.2f} ILS'

        else:
            usd_cash_bt = usd_cash + self.CR.convert('ILS', 'USD', self.bank_cf + self.trader_cf)

            if numbers_only:
                return np.round(nis_cash+self.bank_cf+self.trader_cf, 3), np.round(usd_cash_bt, 3)

            else:
                return f'\nPortfolio Assets: {usd_cash:,.2f} $ | {nis_cash:,.2f} ILS\n' \
                       f'Bank Cash Flow: {self.bank_cf:,.2f} ILS\nTrader Cash Flow: {self.trader_cf:,.2f} ILS\n\n' \
                       f'Total Assets: {usd_cash_bt:,.2f} $ |' \
                       f' {nis_cash + self.bank_cf + self.trader_cf:,.2f} ILS'

    def print_assets(self, for_plot_mail: bool = False) -> str:
        if for_plot_mail:
            if self.bank_cf + self.trader_cf > 0:
                return self.total_assets(portfolio_only=True)
            else:
                return self.total_assets()

        if self.bank_cf + self.trader_cf > 0:
            print(self.total_assets(portfolio_only=True))

        else:
            print(self.total_assets())

    def print_stocks(self, symbol: str = None):
        if symbol:
            symbol = symbol.upper()
            print(self.show_stocks(symbol))

        else:
            print(self.show_stocks())
