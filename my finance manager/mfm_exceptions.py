import logging
import os
import shutil
import sys
from datetime import datetime

TODAY = datetime.strftime(datetime.today(), '%d.%m.%Y')


def create_logger():
    if not os.path.isdir('logs'):
        os.mkdir('logs')
    LOG = logging.getLogger('MFM.Logger')
    handler = logging.StreamHandler(sys.stdout)
    LOG.addHandler(handler)
    logging.basicConfig(filename='logs/MFM_Logger.log', filemode='w',
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%d/%m/%y %H:%M:%S',
                        level=logging.INFO)
    return LOG


def log_error_to_desktop(exception):
    """for creating copy of log file on desktop when schedule script failed to complete."""
    shutil.copy2('logs/MFM_Logger.log', f'logs/MFM_Logger_{TODAY}.log')
    try:
        shutil.move(f'logs/MFM_Logger_{TODAY}.log', f'C:/Users/{os.getlogin()}/Desktop')
    except shutil.Error:
        os.remove(f'MFM_Logger_{TODAY}.log')
    finally:
        raise exception
