import smtplib
import ssl
from os import environ

import keyring
import yagmail

from charts_graphs import ChartsGraphs


class EmailFuncs(ChartsGraphs):
    def send_plain_text_email(self):
        smtp_server = "smtp.gmail.com"
        port, context = 465, ssl.create_default_context()
        sender_email = environ.get('MFM_email')
        sender_password = keyring.get_password('mfm', 'mfm')
        receiver_email = self.user_email
        message = f'\n\n\nMyFinanceManager app report:\n' \
            f'{self.print_assets(True)}\n' \
            f'Total profit is {self.total_profit()[0]} % / {self.total_profit()[1]} ILS.\n\n' \
            f'{self.show_stocks()}\n\n\n\n' \
            f'End of report.\n' \
            f'Sent by MyFinanceManager.'

        try:
            self.LOG.debug('Trying to send plain text email message')
            with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, receiver_email, message)
                self.LOG.info(f'Email sent successfully to {receiver_email}')
                return True

        except Exception as e:
            self.LOG.exception('Error in sending plain text email message')
            raise e

    def send_fancy_email(self):
        sender_email = environ.get('MFM_email')
        sender_password = keyring.get_password('mfm', 'mfm')
        receiver_email = self.user_email
        subject = 'MFM App Report'

        body1 = f'<br><br><center>' \
            f'<h2><b>MyFinanceManager Weekly Report</b></h2>' \
            f'<h3><br>{self.df_assets(True)}</h3>' \
            f'</center>'

        img = self.graph(profit_numbers=True, save_only=True)

        body2 = f'<br><center>' \
            f'<h3><u>Portfolio History Stats</u></h3>' \
            f'{self.df_history(tabulate_mode=True, to_email=True)}</center>'

        body3 = f'<br><center>' \
            f'<h3><u>Current Holdings</u></h3>' \
            f'{self.df_stocks(to_email=True)}</center>' \
            f'<br><br><br><br><big>End of report.</big>' \
            f'<br><small>Sent by MyFinanceManager.</small>'

        contents = [body1, yagmail.inline(img), body2, body3]

        if self.days_left < 5 and self.days_left != 0:
            body_0 = f'<br><center><h4><u>Warning:</u><br>' \
                     f'{self.days_left} to update login password in trader site.</h4></center><br>'
            contents.insert(0, body_0)

        if self.trader_cf < 50:
            body_1 = f'<br><center><h4><u>Warning:</u><br>' \
                     f' Balance in trader is: {self.trader_cf},<br>' \
                     f' consider adding cash to trader balance.</h4></center><br>'
            contents.insert(0, body_1)

        try:
            self.LOG.debug('Trying to send fancy text email message')
            yag = yagmail.SMTP(sender_email, sender_password)
            yag.send(receiver_email, subject, contents)
            self.LOG.info(f'Email sent successfully to {receiver_email}')
            return True

        except Exception as e:
            self.LOG.exception('Error in sending plain text email message')
            raise e
