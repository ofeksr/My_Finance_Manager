import os
from datetime import datetime
from glob import glob
import shutil

import keyring

from database import MyFinanceManager
from google_agents import GoogleKeepAgent
from meitav_dash_scraper import get_trader_info
from mfm_exceptions import log_error_to_desktop
from otsar_hahayal_scraper import get_bank_info

p = None


def run_script():
    global p
    try:

        if datetime.today().weekday() == 5:
            print('Today is Saturday, no need to update portfolio.')
            exit()

        list_of_files = glob(MyFinanceManager.DEFAULT_SAVE_PATH + '/*.json')

        if len(list_of_files) != 0:
            latest_file = sorted(
                list_of_files,
                key=lambda date: datetime.strptime(''.join(date.split('\\')[1]).split('-')[0],
                                                   '%d.%m.%Y'))[-1]

            p = MyFinanceManager.import_database(filename=latest_file, gui_mode=True)

            p.update_stocks_price()

            bank_cf = get_bank_info(only_balance=True)

            trader_cf, p.days_left = get_trader_info(cash_days=True)

            if bank_cf is None and trader_cf is not None:
                p.update_bank_trader_cf(u_trader_cf=trader_cf)

            elif bank_cf is not None and trader_cf is None:
                p.update_bank_trader_cf(u_bank_cf=bank_cf)

            else:
                p.update_bank_trader_cf(u_bank_cf=bank_cf, u_trader_cf=trader_cf)

            if trader_cf is not None and p.days_left is not None:
                if trader_cf < 50 or p.days_left < 8:
                    email_address = os.environ.get('my_email')
                    keep_password = keyring.get_password('keep-agent', os.getlogin())
                    keep_username = email_address.split('@')[0]
                    token = keyring.get_password('google-keep-token', keep_username)

                    keep = GoogleKeepAgent()
                    keep.keep_login(email_address=email_address, password=keep_password, token=token)
                    to_do_list_id = keyring.get_password('keep-agent', 'todo-list-id')
                    events_to_add = []

                    if trader_cf < 50:
                        events_to_add.append(f'Balance in trader is: {trader_cf},'
                                             f' consider adding cash to trader balance.')

                    if p.days_left < 8:
                        events_to_add.append(f'Days left for changing Meitav Dash password: {p.days_left}.')

                    keep.add_events_to_list(list_id=to_do_list_id, events=events_to_add, top=True)

            p.graph(market_value=True, save_only=True)
            p.graph(profit_numbers=True, save_only=True)
            p.graph(profit_percentage=True, save_only=True)

            p.save_database()

            backup_path = f'C:/Users/{os.getlogin()}/PycharmProjects/Backup Databases/MFM'
            if not os.path.isdir(backup_path):
                os.mkdir(backup_path)

            shutil.copy(f'database/{p.TODAY}-Portfolio-Data.json',
                        backup_path)

            if datetime.today().weekday() == 6:
                p.send_fancy_email()

            return True

    except Exception as e:
        MyFinanceManager.LOG.exception('Script not fully finished, error file created')
        log_error_to_desktop(e)


if __name__ == '__main__':
    run_script()
