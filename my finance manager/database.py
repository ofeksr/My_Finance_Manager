import json
import os

from email_funcs import EmailFuncs


class MyFinanceManager(EmailFuncs):

    @classmethod
    def import_database(cls, filename: str, gui_mode: bool = False):
        cls.LOG.debug('Trying to import database')
        if filename[-5:] != '.json' and not gui_mode:
            filename = filename + '.json'

        if gui_mode:
            complete_path = filename

        else:
            default_save_path = 'database/'

            # complete_path = os.path.join(default_save_path, filename + '.json')
            complete_path = os.path.join(default_save_path, filename)

        try:
            with open(complete_path) as file:
                data = json.load(file)
                file_name_fixed = filename.replace('\\', '/')
                cls.LOG.info(f'Import database file "{file_name_fixed}"')
                return cls(data=data)

        except IOError:
            cls.LOG.exception('Error in importing database')
            raise

    def save_database(self, user_path: str = None) -> bool:
        self.LOG.debug('Trying to save database')
        self.history_data[f'{self.TODAY}'] = {
            'market_value':
                {
                    'portfolio': self.total_assets(portfolio_only=True, numbers_only=True),
                    'total_assets': self.total_assets(portfolio_only=False, numbers_only=True)
                },
            'profit': self.total_profit(numbers_only=True),
            'bank_cf': self.bank_cf,
            'trader_cf': self.trader_cf
        }

        data = {
            'stocks': self.stocks,
            'symbol buy count': self.symbol_buy_count,
            'bank_cf': self.bank_cf,
            'trader_cf': self.trader_cf,
            'user_email': self.user_email,
            'update_dates': self.update_dates,
            'history_data': self.history_data
        }

        if user_path:
            try:
                with open(user_path, 'w') as file:
                    user_path_fixed = user_path.replace('\\', '/')
                    dir_path = '/'.join(user_path_fixed.split('/')[:-1])
                    if not os.path.isdir(dir_path):
                        os.mkdir(dir_path)

                    json.dump(data, file,  indent=4, separators=(',', ': '))
                    self.LOG.info(f'Save database file "{user_path_fixed}" finished')
                    return True

            except IOError:
                self.LOG.exception('Error in saving database')
                raise

        else:
            if not os.path.isdir(self.save_path):
                os.mkdir(self.save_path)
            filename = f'{self.TODAY}-Portfolio-Data'
            complete_path = os.path.join(self.save_path, filename + '.json').replace('\\', '/')

            try:
                with open(complete_path, 'w') as file:
                    json.dump(data, file,  indent=4, separators=(',', ': '))
                    self.LOG.info(f'Save database file "{complete_path}" finished')
                    return True

            except IOError:
                self.LOG.exception('Error in saving database file')
                raise
