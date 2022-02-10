import logging
import multiprocessing
import time
import os
import uuid

import pymongo
from dotenv import load_dotenv
from SignalGenerator import startSignalGenerator
from TweetsLoader import startTweetsLoader
from BotDetector import startBotDetector

load_dotenv()
client = pymongo.MongoClient(os.environ['DATABASE_URL'])
#client = pymongo.MongoClient('localhost', 27017, username='admin',password='pass')

try:
    db = client["TwitterData"]
    col = db["Users1"]
except AttributeError as error:
    print(error)


if __name__ == '__main__':

    keywords = ["cat"]
    id = uuid.uuid4()
    logging.info(id)
    col1 = db[str(id)]
    p1 = multiprocessing.Process(name='p1', target=startTweetsLoader,
                                 args=(keywords, 'kafka.milki-psy.dbis.rwth-aachen.de:31039', str(id), "set0", 10,))
    p2 = multiprocessing.Process(name='p2', target=startSignalGenerator, args=(
        'kafka.milki-psy.dbis.rwth-aachen.de:31039', 'test1-id', 'earliest', str(id), 'kafka.milki-psy.dbis.rwth-aachen.de:31039', (str(id) + "-signals"),))
    p3 = multiprocessing.Process(name='p3', target=startBotDetector, args=(
        'kafka.milki-psy.dbis.rwth-aachen.de:31039', 'test1-id', 'earliest', (str(id) + "-signals"), 'kafka.milki-psy.dbis.rwth-aachen.de:31039', str(id),))
    p1.start()
    p2.start()
    p3.start()
