import os

import keyring

email_address = os.environ.get('my_email')
keep_password = keyring.get_password('keep-agent', os.getlogin())
keep_username = email_address.split('@')[0]
token = keyring.get_password('google-keep-token', keep_username)

sender_email = os.environ.get('MFM_email')
sender_password = keyring.get_password('mfm', 'mfm')

to_do_list_id = keyring.get_password('keep-agent', 'todo-list-id')
