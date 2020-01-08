import concurrent.futures
import time

from exceptions import log_error_to_desktop, datetime, os
from mfm import MyFinanceManager
from scrapers.meitav_dash_scraper import get_trader_info
from scrapers.otsar_hahayal_scraper import get_bank_info
from tools.google_agents import GoogleKeepAgent
from config.config import email_address, keep_password, token, to_do_list_id


def run_script():
    try:

        p = MyFinanceManager()

        # check if its saturday and also if there was an update in friday - so don't need to update.
        weekday = datetime.datetime.today().weekday()
        stocks_last_update_date = p.db.last_modified.get_field(field_name='stocks')
        current_date = datetime.datetime.now()
        if weekday == 5 and (stocks_last_update_date == current_date + datetime.timedelta(days=-1)):
            p.LOG.info('Today is Saturday, no need to update portfolio.')
            exit()

        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.submit(p.update_stocks_price)
            f1 = executor.submit(get_bank_info, only_balance=True)
            f2 = executor.submit(get_trader_info, cash_days=True)

            bank_cf = f1.result()
            trader_cf, p.days_left = f2.result()

        # in case that script couldn't web scrap for bank and \ or trader data.
        if bank_cf is None and trader_cf is not None:
            p.update_bank_trader_cf(u_trader_cf=trader_cf)

        elif bank_cf is not None and trader_cf is None:
            p.update_bank_trader_cf(u_bank_cf=bank_cf)

        else:
            p.update_bank_trader_cf(u_bank_cf=bank_cf, u_trader_cf=trader_cf)

        p.update_history_data()

        # check if need to alert (add to google keep `to do list`) to change trader password.
        # if trader_cf is not None and p.days_left is not None:
        if (trader_cf and p.days_left) and (trader_cf < 50 or p.days_left < 8):
            keep = GoogleKeepAgent()
            keep.login(email_address=email_address, password=keep_password, token=token)
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

        # if its sunday, send email report.
        if datetime.datetime.today().weekday() == 6:
            receiver_email = p.db.user_info.get_user_email_address()
            p.send_fancy_email(receiver_email=receiver_email)

        p.db.close_connection()

        backup_path = f'C:/Users/{os.getlogin()}/PycharmProjects/Backup Databases/MFM/MongoDB/{p.TODAY}'
        if not os.path.isdir(backup_path):
            os.mkdir(backup_path)
        p.db.backup_database(path=backup_path)

        time.sleep(3.5)
        return True

    except Exception:
        MyFinanceManager.LOG.exception('Script not fully finished, error file created')
        log_error_to_desktop()


if __name__ == '__main__':
    run_script()
