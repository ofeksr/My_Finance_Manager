import os
import sys
import unittest

import database


class Test(unittest.TestCase):

    def setUp(self) -> None:
        for path in ['database', 'logs']:
            if not os.path.isdir(path):
                os.mkdir(path)
        self.mfm = database.MyFinanceManager.import_database('04.11.2019-Portfolio-Data')

    def tearDown(self) -> None:
        self.mfm = None

    def test_save_db(self):
        self.assertIsNotNone(self.mfm.save_database('C:/Users/Ofek/PycharmProjects/My Finance Manager/'
                                                    'test/database/example_db.json'),
                             msg='Failed to save database')

    def test_add_stock(self):
        for i in range(2):
            with self.subTest(msg=i):
                if i == 0:
                    self.assertTrue(self.mfm.add_stock('BNDX', 'TODAY', 150, 120.2, 'USD'),
                                    msg='Failed to add USD stock')
                else:
                    self.assertTrue(self.mfm.add_stock('ILS_ETF', 'TODAY', 150, 120.2, 'ILS', 5109889),
                                    msg='Failed to add israeli stock')

    def test_update_stock(self):
        for i in range(2):
            with self.subTest(msg=i):
                if i == 0:
                    self.assertTrue(self.mfm.update_stocks_price(),
                                    msg='Failed to updates all stocks')
                else:
                    self.assertTrue(self.mfm.update_stocks_price(symbol='VTI'),
                                    msg='Failed to update specific stock')

    def test_remove_stock(self):
        self.assertIsInstance(self.mfm.remove_stock(symbol='VTI', amount=10),
                              bool,
                              msg='Failed to remove specific stock')

    def test_get_redemption_price(self):
        self.assertIsInstance(self.mfm.get_redemption_price(fund_id=5109889),
                              float,
                              msg='Failed to get red price')

    def test_df_stocks(self):
        pass

    def test_total_profit(self):
        self.assertIsInstance(self.mfm.total_profit(),
                              tuple,
                              msg='Failed to get total profit')

    def test_graph_profit_percentage(self):
        self.assertIsNotNone(self.mfm.graph(profit_percentage=True, save_only=True),
                             msg='Failed to graph profit percentage')

    def test_schedule(self):
        sys.path.append('C:/Users/Ofek/PycharmProjects/My Finance Manager/my finance manager')
        from mfm_schedule import run_script

        self.assertTrue(run_script(),
                        msg='Failed to run schedule script')
