"""
Scrap account info from Meitav Dash website using selenium chrome web driver.
"""
import json
import logging
import os
import sys
from datetime import datetime

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
logging.basicConfig(filename='logs/Meitav_Dash_Scraper_Logger.log', filemode='w',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%d/%m/%y %H:%M:%S',
                    level=logging.INFO)


def get_trader_info(cash_days: bool = False):
    """
    Login to Meitav Dash account and scrapping user data.
    :param cash_days: True or False.
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

        days_left = int(driver.find_element_by_class_name(
            'highlighted-text.ng-binding.ng-scope').text)
        LOG.info(f'{days_left} days left for changing trader login password')

        element = driver.find_element_by_class_name('btn.btn-primary')
        driver.execute_script("arguments[0].click();", element)
        WebDriverWait(driver, 10).until(ec.presence_of_element_located((By.CLASS_NAME, 'online-holdings-summery')))

        account_number = driver.find_elements_by_class_name('ng-binding')[26].text

        balance, gain_and_loss, change_percentage, cash, income, \
        profit, profit_percentage, collateral = driver.find_elements_by_class_name('ng-binding.ng-scope')[:8]

        if cash_days:
            return [float(cash.text), days_left]

        info = {
            'Account Number': account_number,
            'Date': datetime.today().strftime('%d/%m/%y'),
            'Time': datetime.now().strftime('%H:%M:%S'),
            'Balance': balance.text,
            'Gain and Loss': gain_and_loss.text,
            'Change in Percentage': change_percentage.text,
            'Cash': cash.text,
            'Income': income.text,
            'Profit': profit.text,
            'Profit in Percentage': profit_percentage.text,
            'Collateral': collateral.text,
        }

        driver.quit()
        LOG.debug('Web driver closed')

        return info

    except:
        LOG.exception(f'Failed to get info from Meitav Dash website')
        return [None, None]


if __name__ == '__main__':
    # using json.dumps for pretty print.
    print(json.dumps(get_trader_info(), indent=4))
