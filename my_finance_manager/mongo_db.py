import atexit
import subprocess

from pymongo import MongoClient

from exceptions import logging, os, sys, datetime, TODAY

LOG = logging.getLogger('MongoDB.Logger')
handler = logging.StreamHandler(sys.stdout)
LOG.addHandler(handler)


class MyMongoDB:
    _client = MongoClient()
    db = _client['mfm']
    user_name = os.getlogin()

    def __init__(self):
        LOG.debug('initializing MongoDB object')

        self.stocks = _Stocks()
        self.user_info = _UserInfo()
        self.history_data = _HistoryData()
        self.last_modified = _LastModified()

        if not self.user_info.collection.find_one({}):
            self.user_info.collection.insert_one({'user_name': self.user_name})
        else:
            self.user_name = self.user_info.collection.find_one({}, {'user_name': 1})['user_name']

        # close connection on exit
        atexit.register(self.close_connection)

        LOG.info('MongoDB object created successfully')

    def _setup_test_collections(self):
        self.stocks.collection.aggregate([
            {'$merge': {'into': {'db': 'mfm_test', 'coll': 'stocks'}}}
        ])
        self.user_info.collection.aggregate([
            {'$merge': {'into': {'db': 'mfm_test', 'coll': 'user_info'}}}
        ])
        self.history_data.collection.aggregate([
            {'$merge': {'into': {'db': 'mfm_test', 'coll': 'history_data'}}}
        ])
        self.last_modified.collection.aggregate([
            {'$merge': {'into': {'db': 'mfm_test', 'coll': 'last_modified'}}}
        ])
        self.db = self._client['mfm_test']
        _Stocks.collection = self.db['stocks']
        _UserInfo().collection = self.db['user_info']
        _HistoryData().collection = self.db['history_data']
        _LastModified().collection = self.db['last_modified']

    @classmethod
    def _drop_db(cls, db_name: str):
        cls._client.drop_database(db_name)
        LOG.info(f'Database {db_name} dropped')
        return True

    def _check_collections(self):
        """checking if collections exists and in correct length"""
        collections_count = len(self.db.list_collection_names())
        return True if collections_count == 4 else False

    def close_connection(self):
        self._client.close()
        LOG.info('MongoDB connection closed')
        return True

    @staticmethod
    def backup_database(path: str):
        subprocess.call(['mongodump', '-d', 'mfm', '-o', path])
        LOG.info('Database backup completed')
        return True


class _Stocks:
    collection = MyMongoDB.db['stocks']

    def fetch_data_for_df(self):
        data = list(self.collection.aggregate([
            {'$project': {'_id': 0, 'Symbol': '$symbol', 'Market_Value_ILS': 1, 'Lot_Num': 1, 'Date': 1, 'Amount': 1,
                          'Buy_Price': 1, 'Currency': 1, 'Profit_%': 1, 'Profit_ILS': 1}},
            {'$sort': {'Market_Value_ILS': -1}}
        ]))
        return data

    def sum_portfolio_field(self, field_name):
        field_sum = list(self.collection.aggregate([
            {'$group': {'_id': None, 'total': {'$sum': f'${field_name}'}}},
            {'$project': {'_id': 0}}
        ]
        ))[0]
        return field_sum['total']

    def get_stocks_names(self):
        return self.collection.distinct('symbol')

    def insert_lot_to_stock(self, symbol: str, d: dict):
        self.collection.update_one({'symbol': symbol}, {'$set': d})
        return True

    def update_stock_amount(self, symbol: str, lot_num: int, sell_amount: int):
        self.collection.update_one({'symbol': symbol, 'Lot_Num': lot_num}, {'$inc': {'Amount': -sell_amount}})
        return True

    def update_stock_lot(self, symbol: str, lot_num: int, market_val_ils: float, market_val_usd: float,
                         profit_usd: float, profit_ils: float, profit_percentage: float):
        self.collection.update_one({'symbol': symbol, 'Lot_Num': lot_num}, {'$set': {
            'Market_Value_USD': market_val_usd,
            'Market_Value_ILS': market_val_ils,
            'Profit_%': profit_percentage,
            'Profit_ILS': profit_ils,
            'Profit_USD': profit_usd,
        }})
        return True

    def get_field_from_stock(self, symbol: str, lot_num: int, field: str):
        return self.collection.find_one({'symbol': symbol, 'Lot_Num': lot_num},
                                        {field: 1})[field]

    def insert_stock(self, d):
        self.collection.insert_one(d)
        return True

    def get_stock_lots_count(self, symbol: str = None, per_stock: bool = False):
        if per_stock:
            lots_count = list(self.collection.aggregate([
                {'$group': {'_id': '$symbol', 'count': {'$sum': 1}}},
                {'$project': {'symbol': '$_id', '_id': 0, 'count': 1}}
            ]))
            return [s for s in lots_count]

        elif symbol:
            lots_count = list(self.collection.aggregate([
                {'$match': {'symbol': symbol}},
                {'$group': {'_id': '$symbol', 'count': {'$sum': 1}}},
            ]))
            if len(lots_count) == 0:
                return 0
            return lots_count[0]['count']

    def remove_stock(self, symbol: str, lot_num: int = None):
        if lot_num:
            self.collection.delete_one({'symbol': symbol, 'Lot_Num': lot_num})
        else:
            self.collection.delete_one({'symbol': symbol})
        return True


class _UserInfo:
    collection = MyMongoDB.db['user_info']

    def get_user_email_address(self):
        return self.collection.find_one({'user_name': MyMongoDB.user_name}, {'email_address': 1})['email_address']

    def change_email_address(self, new_email_address: str):
        self.collection.update_one({'user_name': MyMongoDB.user_name},
                                   {'$set': {'email_address': new_email_address}})
        return True


class _HistoryData:
    collection = MyMongoDB.db['history_data']

    def get_latest_trader_cf(self):
        cf = list(self.collection.aggregate([
            {'$sort': {'date': -1}},
            {'$limit': 1},
            {'$project': {'_id': 0, 'trader_cf': 1}},
        ]))[0]['trader_cf']
        return cf

    def get_latest_bank_cf(self):
        cf = list(self.collection.aggregate([
            {'$sort': {'date': -1}},
            {'$limit': 1},
            {'$project': {'_id': 0, 'bank_cf': 1}},
        ]))[0]['bank_cf']
        return cf

    def fetch_data_for_df(self):
        data = list(self.collection.aggregate([
            {'$project': {'_id': 0, 'Portfolio_ILS': '$market_value.portfolio.ILS',
                          'Portfolio_USD': '$market_value.portfolio.USD',
                          'Total_ILS': '$market_value.total_assets.ILS',
                          'Total_USD': '$market_value.total_assets.USD',
                          'Profit_%': '$profit.percentage',
                          'Profit_ILS': '$profit.ILS',
                          'Bank_CF': '$bank_cf', 'Trader_CF': '$trader_cf', 'Date': '$date',
                          }},
            {'$sort': {'Date': -1}}
        ]))
        return data

    def update_trader(self, cf: float):
        self.collection.update_one({'date': datetime.datetime.strptime(TODAY, '%d-%m-%Y')},
                                   {'$set': {'trader_cf': cf}}, upsert=True)
        return True

    def update_bank(self, cf: float):
        self.collection.update_one({'date': datetime.datetime.strptime(TODAY, '%d-%m-%Y')},
                                   {'$set': {'bank_cf': cf}}, upsert=True)
        return True

    def update_all(self, total_assets_ils: float, total_assets_usd: float, total_profit: tuple):
        d = list(self.collection.aggregate([
            {'$project': {'trader_cf': 1, 'bank_cf': 1, 'date': 1}},
            {'$sort': {'date': -1}},
            {'$limit': 1},
            {'$lookup': {
                'from': 'stocks',
                'pipeline': [{'$group': {'_id': None, 'sum': {'$sum': '$Profit_ILS'}}}],
                'as': 'Profit_ILS'
            }},
            {'$lookup': {
                'from': 'stocks',
                'pipeline': [{'$group': {'_id': None, 'sum': {'$sum': '$Market_Value_USD'}}}],
                'as': 'Market_Value_USD'
            }},
            {'$lookup': {
                'from': 'stocks',
                'pipeline': [{'$group': {'_id': None, 'sum': {'$sum': '$Market_Value_ILS'}}}],
                'as': 'Market_Value_ILS'
            }},
            {'$project': {'_id': 0, 'Total_Profit_ILS': '$Profit_ILS.sum',
                          'Total_Market_Value_ILS': '$Market_Value_ILS.sum',
                          'Total_Market_Value_USD': '$Market_Value_USD.sum', 'trader_cf': 1, 'bank_cf': 1}},
        ]))[0]

        portfolio_market_value = {
            'ILS': d["Total_Market_Value_ILS"][0],
            'USD': d["Total_Market_Value_USD"][0]
        }
        total_assets = {
            'ILS': total_assets_ils,
            'USD': total_assets_usd
        }
        profit = {
            'ILS': d["Total_Profit_ILS"][0],
            'percentage': total_profit[0]
        }

        self.collection.update_one({'date': datetime.datetime.strptime(TODAY, '%d-%m-%Y')},
                                   {'$set': {'trader_cf': d["trader_cf"], 'bank_cf': d["bank_cf"],
                                             'market_value': {'portfolio': portfolio_market_value,
                                                              'total_assets': total_assets},
                                             'profit': profit}},
                                   upsert=True)
        return True


class _LastModified:
    collection = MyMongoDB.db['last_modified']

    def get_all(self):
        data = self.collection.find({}, {'last_modified': 1, '_id': 0})
        return [d['last_modified'].strftime('%d-%m-%Y') for d in data]

    def get_field(self, field_name: str):
        return self.collection.find_one({'type': field_name}, {'last_modified': 1})['last_modified']

    def update_field(self, field_name: str):
        self.collection.update_one({'type': field_name}, {'$set': {'last_modified': datetime.datetime.now()}})
        return True
