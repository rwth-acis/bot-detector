import tweepy
from confluent_kafka import Producer

import os

from tweepy import OAuthHandler
from tweepy.streaming import Stream
import json
from dotenv import load_dotenv


class StdOutListener(Stream):
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
            print("TweetsLoader: Send " + str(data)[:50])
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

    def on_disconnect(self):
        self.producer.flush()
        self.producer.produce(self.topic, key="INFO", value="END", callback=delivery_report)
        self.producer.flush()



def delivery_report(err, msg):
    """ Called once for each message produced to indicate delivery result.
        Triggered by poll() or flush(). """
    if err is not None:
        print('TweetsLoader: Message delivery failed: {}'.format(err))
    else:
        print('TweetsLoader: Message delivered to {} [{}]'.format(msg.topic(), msg.partition()))


def startTweetsLoader(keywords, producer_servers, producer_topic, topic_key, parameters,
                      consumer_key, consumer_secret, access_token,
                      access_token_secret):
    if not keywords:
        keywords = "a"

    keywords = keywords.replace('"', '')
    keywords = list((keywords.replace(", ", ",")).split(","))
    print(keywords)

    limit = int(parameters["limit"])

    stream = StdOutListener(consumer_key, consumer_secret, access_token, access_token_secret, producer_servers,
                            producer_topic, topic_key, limit)
    stream.filter(track=keywords)
    stream.timeout = 10000
    # stream = StdOutListener(consumer_key, consumer_secret, access_token, access_token_secret, 'localhost:9091',
    #                        'tweets-test-monday5', "set0")
    # stream.filter(track=["covid19", "corona virus"])

# stream = StdOutListener(consumer_key, consumer_secret, access_token, access_token_secret, {'bootstrap.servers': 'localhost:9091'})
# stream.filter(track=["covid19", "corona virus"])
