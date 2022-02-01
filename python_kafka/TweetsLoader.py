from confluent_kafka import Producer

import os
from tweepy.streaming import Stream as StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from kafka import KafkaProducer
import json
from dotenv import load_dotenv




"""access_token = "--"
access_token_secret = "--"
api_key = "--"
api_secret = "--" """




class StdOutListener(StreamListener):
    def __init__(self, consumer_key, consumer_secret, access_token, access_token_secret, servers, topic, key, limit=10):
        super().__init__(consumer_key, consumer_secret, access_token, access_token_secret)
        self.counter = 0
        self.limit = limit
        self.producer = Producer({'bootstrap.servers': servers})
        self.topic = topic
        self.key = key

    def on_data(self, data):
        self.counter += 1
        data_json = json.loads(data)
        if self.counter <= self.limit:
            self.producer.produce(self.topic, key=self.key, value=data, callback=delivery_report)
            self.producer.flush()
            print("TweetsLoader: Send "+str(data)[:50])
            return True
        else:
            self.producer.flush()
            self.producer.produce(self.topic, key="INFO", value="END", callback=delivery_report)
            self.producer.flush()
            self.disconnect()

    def on_error(self, status):
        self.counter += 1
        if self.counter < self.limit:
            print(status)
        else:
            self.producer.flush()
            self.producer.produce(self.topic, key="INFO", value="END", callback=delivery_report)
            self.producer.flush()
            self.disconnect()


def delivery_report(err, msg):
    """ Called once for each message produced to indicate delivery result.
        Triggered by poll() or flush(). """
    if err is not None:
        print('TweetsLoader: Message delivery failed: {}'.format(err))
    else:
        print('TweetsLoader: Message delivered to {} [{}]'.format(msg.topic(), msg.partition()))


def startTweetsLoader(keywords, producer_servers, producer_topic, topic_key, limit=10):
    load_dotenv()
    consumer_key = os.environ['CONSUMER_KEY']
    consumer_secret = os.environ['CONSUMER_SECRET']
    access_token = os.environ['ACCESS_TOKEN']
    access_token_secret = os.environ['ACCESS_TOKEN_SECRET']
    print(keywords)
    stream = StdOutListener(consumer_key, consumer_secret, access_token, access_token_secret, producer_servers,
                            producer_topic, topic_key, limit)
    stream.filter(track=keywords)

    # stream = StdOutListener(consumer_key, consumer_secret, access_token, access_token_secret, 'localhost:9091',
    #                        'tweets-test-monday5', "set0")
    # stream.filter(track=["covid19", "corona virus"])


#stream = StdOutListener(consumer_key, consumer_secret, access_token, access_token_secret, {'bootstrap.servers': 'localhost:9091'})
#stream.filter(track=["covid19", "corona virus"])

