import json
import pprint
import os
from datetime import datetime

from pymongo import MongoClient

client = MongoClient()
client.drop_database('mfm')
db = client['mfm']

with open('../database/jsons/01.01.2020-Portfolio-Data.json') as f:
    file_data = json.load(f)


    def replace_dots_for_keys(d):
        new = {}
        for k, v in d.items():
            if isinstance(v, dict):
                v = replace_dots_for_keys(v)
            new[k.replace('.', '/')] = v
        return new


    def replace_spaces_for_keys(d):
        new = {}
        for k, v in d.items():
            if isinstance(v, dict):
                v = replace_spaces_for_keys(v)
            new[k.replace(' ', '_')] = v
        return new


    file_data = replace_dots_for_keys(file_data)
    file_data = replace_spaces_for_keys(file_data)

stocks, user_info, history_data, last_modified = [], [], [], []
for d in file_data:
    if d == 'stocks':
        for symbol in file_data[d]:
            for lot in file_data[d][symbol]:
                if lot != 'Lot_1':
                    data = file_data[d][symbol][lot]
                    lot_num = lot.split('_')[1]
                    data.update({'Lot_Num': int(lot_num)})

                    stocks.append({'symbol': symbol, **data})
                    index = stocks.index({'symbol': symbol, **data})
                    stocks[index]['Date'] = \
                        datetime.strptime(stocks[index]['Date'], '%d.%m.%Y')
                    if 'num' in stocks[index]:
                        temp = stocks[index]['num']
                        del stocks[index]['num']
                        stocks[index]['TASE_INDEX'] = temp
                else:
                    data = file_data[d][symbol][lot]
                    lot_num = lot.split('_')[1]
                    data.update({'Lot_Num': int(lot_num)})

                    stocks.append({'symbol': symbol, **data})
                    index = stocks.index({'symbol': symbol, **data})
                    stocks[index]['Date'] = datetime.strptime(stocks[index]['Date'], '%d.%m.%Y')
                    if 'num' in stocks[index]:
                        temp = stocks[index]['num']
                        del stocks[index]['num']
                        stocks[index]['TASE_INDEX'] = temp

    elif d == 'user_email':
        user_info.append({'email_address': file_data[d], 'user_name': os.getlogin()})

    elif d == 'update_dates':
        last_modified.extend([{'type': 'stocks'}, {'type': 'bank'}, {'type': 'trader'}])

    elif d == 'history_data':
        for index, date in enumerate(file_data[d]):
            history_data.append({
                'date': datetime.strptime(date, '%d/%m/%Y'),
                'bank_cf': file_data[d][date]['bank_cf'],
                'market_value': file_data[d][date]['market_value'],
                'profit': file_data[d][date]['profit'],
                'trader_cf': file_data[d][date]['trader_cf'],
            })
            ILS, USD = history_data[index]['market_value']['portfolio']
            history_data[index]['market_value']['portfolio'] = {'ILS': ILS, 'USD': USD}
            ILS, USD = history_data[index]['market_value']['total_assets']
            history_data[index]['market_value']['total_assets'] = {'ILS': ILS, 'USD': USD}
            percentage, ILS = history_data[index]['profit']
            history_data[index]['profit'] = {'ILS': ILS, 'percentage': percentage}

pprint.pprint(stocks)
pprint.pprint(history_data)
pprint.pprint(user_info)
pprint.pprint(last_modified)

collection_stocks = db['stocks']
collection_history = db['history_data']
collection_user_info = db['user_info']
collection_last_modified = db['last_modified']

for collection, document in zip([collection_stocks, collection_history, collection_user_info, collection_last_modified],
                                [stocks, history_data, user_info, last_modified]):
    collection.insert_many(document)

client.close()
