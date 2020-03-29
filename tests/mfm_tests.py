import os
import unittest

from mfm import MyFinanceManager, mongo_db


class MyTestCase(unittest.TestCase):

    def setUp(self) -> None:
        for path in ['logs', 'media']:
            if not os.path.isdir(path):
                os.mkdir(path)

        self.mfm = MyFinanceManager()
        self.mfm.db._setup_test_collections()

    def tearDown(self) -> None:
        mongo_db.MyMongoDB._drop_db(db_name='mfm_test')
        self.mfm = None

    def test_add_stock(self):
        for i in range(2):
            with self.subTest(i=i):
                if i == 1:
                    self.assertTrue(self.mfm.add_stock('BNDX', '18.12.2011', 150, 66.5, 'USD'),
                                    msg='Failed to add USD stock')
                else:
                    self.assertTrue(self.mfm.add_stock('PSAGOT-TA-125', '18.12.2011', 300, 1950.58, 'ILS', 5110788),
                                    msg='Failed to add ILS stock')

    def test_remove_stock(self):
        for i in range(2):
            with self.subTest(i=i):
                if i == 1:
                    self.assertTrue(self.mfm.remove_stock('VTI', 10),
                                    msg='Failed to remove shares from stock with 1 lot')
                else:
                    self.assertTrue(self.mfm.remove_stock('IJR', 10),
                                    msg='Failed to remove shares from stock with 2 lots')

    def test_update_stocks(self):
        for i in range(2):
            with self.subTest(i=i):
                if i == 1:
                    self.assertTrue(self.mfm.update_stocks_price(),
                                    msg='Failed to update all stocks prices')
                else:
                    self.assertTrue(self.mfm.update_stocks_price(symbol='VTI'),
                                    msg='Failed to update specific stock price')

    def test_update_bank_trader(self):
        self.assertTrue(self.mfm.update_bank_trader_cf(60, 50),
                        msg='Failed to update bank and trader cash flows')

    def test_update_history_data(self):
        self.assertTrue(self.mfm.update_history_data(),
                        msg='Failed to update all history data')

    def test_graph(self):
        for i in range(3):
            with self.subTest(i=i):
                if i == 1:
                    self.assertIsInstance(self.mfm.graph(market_value=True, save_only=True),
                                          str,
                                          msg='Failed to create market value graph')
                elif i == 2:
                    self.assertIsInstance(self.mfm.graph(profit_percentage=True, save_only=True),
                                          str,
                                          msg='Failed to create profit percentage graph')
                else:
                    self.assertIsInstance(self.mfm.graph(profit_numbers=True, save_only=True),
                                          str,
                                          msg='Failed to create profit numbers graph')

    def test_send_email(self):
        receiver_email = self.mfm.db.user_info.get_user_email_address()
        self.assertTrue(self.mfm.send_fancy_email(receiver_email))


if __name__ == '__main__':
    unittest.main()
