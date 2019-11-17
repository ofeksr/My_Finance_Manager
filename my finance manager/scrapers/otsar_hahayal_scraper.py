"""
Scrap bank account info from Otsar Hahayal website using selenium chrome web driver.
"""

import json
import logging
import os
import sys

import keyring
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait


if not os.path.isdir('logs'):
    os.mkdir('logs')
LOG = logging.getLogger('Bank.Scraper.Logger')
handler = logging.StreamHandler(sys.stdout)
LOG.addHandler(handler)
logging.basicConfig(filename='logs/Bank_Scraper_Logger.log', filemode='w',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%d/%m/%y %H:%M:%S',
                    level=logging.INFO)


charge = 0


def get_bank_info(only_balance: bool = False) -> dict or None:
    """
    Login to Otzar Hahayal account and scrapping user data.
    :param only_balance: True or False.
    :return: dict
    """
    global charge
    LOG.info('Start web scrap for bank account info')

    url = 'https://www.bankotsar.co.il/wps/portal/FibiMenu/Marketing/Private?directPage=true'

    # Options for web driver silent run in background.
    c_options = Options()
    c_options.headless = True
    c_options.add_argument("--log-level=3")

    try:
        LOG.debug('Trying to web scrap bank website')
        # remove options=c_options for normal web driver run with opening screen.
        driver = webdriver.Chrome(options=c_options)
        driver.get(url)

        # Choose login frame, clear text if any, and insert username + password from windows environment variables.
        driver.switch_to.frame('loginFrame')

        username = driver.find_element_by_id('username')
        username.clear()
        username.send_keys(os.environ.get('otsar_user'))
        username.send_keys(Keys.RETURN)

        password = driver.find_element_by_id('password')

        password.clear()
        password.send_keys(keyring.get_password('otsar-pass', 'ofek'))
        password.send_keys(Keys.RETURN)

        driver.find_element_by_id('continueBtn').click()

        # Wait till the next page fully reloaded.
        WebDriverWait(driver, 10).until(ec.presence_of_element_located((By.ID, 'lotusMain')))
        LOG.info('Success in login to bank account')

        branch = driver.find_element_by_class_name('branch_num').text
        account_number = driver.find_element_by_class_name('acc_num').text
        date = driver.find_element_by_class_name('current_date').text
        time = driver.find_element_by_class_name('current_time').text

        greens = driver.find_elements_by_class_name('current_balance.txt_green')
        current = greens[0].text.replace(',', '').split()[1]
        currency = greens[1].text.replace(',', '').split()[1]
        total = greens[2].text.replace(',', '').split()[1]

        # check if there is a charge on account.
        try:
            charge = driver.find_elements_by_class_name('current_balance.txt_red')[-1].text
            charge = charge.replace(',', '').split()[1]
        except IndexError:
            charge = 0
        finally:
            balance = float(total) + float(charge)
            driver.quit()
            LOG.debug('Web driver closed')

        if only_balance:
            return float(balance)

        else:
            return {
                'Branch': branch,
                'Account Number': account_number,
                'Date': date,
                'Time': time,
                'Current Amount': f'{float(current):,}',
                'Foreign Currency': f'{float(currency):,}',
                'Total Current Account': f'{float(total):,}',
                'Charged Amount': f'{float(charge):,}',
                'Total Balance': f'{float(balance):,}',
            }

    except:
        LOG.exception(f'Failed to get info from Otsar Haayal website')
        return None


if __name__ == '__main__':
    # using json.dumps for pretty print.
    print(json.dumps(get_bank_info(), indent=4))
