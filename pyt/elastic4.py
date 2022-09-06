from datetime import datetime
from pymongo import MongoClient
from elasticsearch import Elasticsearch
from elasticsearch import helpers
import schedule
import time
# 指定針對 ES 中哪個 index 進行操作 (儲存 mongo 資料)
index = "emily-logs-home1"
# mongo 匯入資料到 ES, query 主要是比對 ES 與 mongo 資料的時間，如果 mongo 無較新資料 doc 會得到 empty list，bulk 也不會發生
def transfer(mongo, es, query):
    doc = list()
    
    for x in mongo['datastore']['log'].find(query, {'_id':False}):
        doc.append({
            "_op_type": "index",
            "_index": index,
            "_source": x
        })
    if len(doc) != 0:
        helpers.bulk(es, doc)

def transferData():
    # mongo = MongoClient("mongodb://matt:1234@192.168.39.105:27017/")
    # es = Elasticsearch(hosts='http://192.168.39.63:9200')

    mongo = MongoClient("mongodb://mongo:27017")
    es = Elasticsearch(hosts='http://elasticsearch:9200')

    res = None
    try:
        res = es.search(index=index, size=1, sort=[{'timestamp':{'order':'desc'}}]) # 1. 查詢 ES 最新一筆 doc
    except:
        transfer(mongo, es, {}) # 1.false-> 2. 若 ES 尚無資料，將 mongo 中所有資料匯入 ES
        return
    # 2. 比對 ES 最新一筆資料的時間點，爬取 mongo 中時間點更新的資料匯入 ES
    esRecentTime = res.get('hits').get('hits')[0].get('_source').get('timestamp')
    d = datetime.fromisoformat(esRecentTime) # 因為 mongo query 吃 ISODatetime
    transfer(mongo, es, {'timestamp': {'$gt': d}})

schedule.every().minutes.do(transferData)
# keeps on running all time.
while True:
    # Checks whether a scheduled task
    # is pending to run or not
    schedule.run_pending()
    time.sleep(5)
