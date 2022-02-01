import multiprocessing
import time
import os
from dotenv import load_dotenv
from SignalGenerator import startSignalGenerator
from TweetsLoader import startTweetsLoader



if __name__ == '__main__':
    p1 = multiprocessing.Process(name='p1', target=startTweetsLoader, args=(["covid19", "corona virus"], 'localhost:9091', 'tweets-test-monday14', "set0"))
    p2 = multiprocessing.Process(name='p2', target=startSignalGenerator, args=('localhost:9091', 'test1-id', 'earliest', 'tweets-test-monday14', 'localhost:9091','tweets-test-monday14-next',))
    p1.start()
    p2.start()
