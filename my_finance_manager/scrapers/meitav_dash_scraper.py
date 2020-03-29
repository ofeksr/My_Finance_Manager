"""
Scrap account info from Meitav Dash website using selenium chrome web driver.
"""
import logging
import os
import re
import sys
from datetime import datetime
from pprint import pprint

import keyring
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

LOG = logging.getLogger('Meitav.Dash.Scraper.Logger')
handler = logging.StreamHandler(sys.stdout)
LOG.addHandler(handler)
logging.basicConfig(filename='../logs/Meitav_Dash_Scraper_Logger.log', filemode='w',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%d/%m/%y %H:%M:%S',
                    level=logging.INFO)


def get_trader_info(mfm_output: bool = False):
    """
    Login to Meitav Dash account and scrapping user data.
    :param mfm_output: True or False.
    :return: tuple (cash_only=True), dict or None
    """
    LOG.info('start web scrap for trader info')

    url = 'https://sparkmeitav.ordernet.co.il/'

    c_options = Options()
    c_options.headless = True
    c_options.add_argument("--log-level=3")

    try:
        driver = webdriver.Chrome(options=c_options)
        driver.get(url)

        username = driver.find_element_by_name('username')
        username.clear()
        username.send_keys(os.environ.get('meitav_user'))
        username.send_keys(Keys.RETURN)

        password = driver.find_element_by_name('password')
        password.clear()
        password.send_keys(keyring.get_password('meitav-pass', 'ofek'))
        password.send_keys(Keys.RETURN)

        WebDriverWait(driver, 10).until(ec.presence_of_element_located((By.CLASS_NAME, 'btn-container')))
        LOG.info('Success in login to trader account')

        days_left = driver.find_element_by_class_name(
            'highlighted-text.ng-binding.ng-scope').text
        LOG.info(f'{days_left} days left for changing trader login password')

        WebDriverWait(driver, 10).until(ec.presence_of_element_located((By.CLASS_NAME, 'btn.btn-primary')))
        element = driver.find_element_by_class_name('btn.btn-primary')
        driver.execute_script("arguments[0].click();", element)
        WebDriverWait(driver, 10).until(ec.presence_of_element_located((By.CLASS_NAME, 'online-holdings-summery')))

        account_number = driver.find_elements_by_class_name('ng-binding')[26].text

        e = driver.find_elements_by_class_name('ng-binding.ng-scope')
        balance, gain_and_loss, change_percentage, cash, income, \
            profit, profit_percentage, collateral = [f.text for f in e[:8]]

        starts_with_path = '<div ng-switch-default="" class="ng-binding ng-scope"'
        stocks_amount = re.findall(f'{starts_with_path}.*>([0-9]+,+[0-9]+\.*[0-9]+)</div>',
                                   driver.page_source)
        usd_stock_amount = stocks_amount[0].replace(',', '')

        driver.quit()
        LOG.debug('Web driver closed')

        if mfm_output:
            return [float(cash), int(days_left), float(usd_stock_amount)]

        else:
            return {
                'Account Number': account_number,
                'Date': datetime.today().strftime('%d/%m/%y'),
                'Time': datetime.now().strftime('%H:%M:%S'),
                'Balance': balance,
                'Gain and Loss': gain_and_loss,
                'Change in Percentage': change_percentage,
                'Cash': cash,
                'Income': income,
                'Profit': profit,
                'Profit in Percentage': profit_percentage,
                'Collateral': collateral,
            }

    except:
        LOG.exception('Failed to get info from Meitav Dash website')
        return [None] * 3


if __name__ == '__main__':
    # keyring.set_password()  # TODO: for setting new password
    pprint(get_trader_info())
