import pprint

from confluent_kafka import Producer

import os

import tweepy

import json
from dotenv import load_dotenv


def delivery_report(err, msg):
    """ Called once for each message produced to indicate delivery result.
        Triggered by poll() or flush(). """
    if err is not None:
        print('TweetsLoader: Message delivery failed: {}'.format(err))
    else:
        print('TweetsLoader: Message delivered to {} [{}]'.format(msg.topic(), msg.partition()))


def startTweetsLoaderWithParameters(keywords, producer_servers, producer_topic, topic_key, parameters,
                                    consumer_key=None, consumer_secret=None, access_token=None,
                                    access_token_secret=None, bearer=None):

    producer = Producer({'bootstrap.servers': producer_servers})

    if bearer is not None:
        auth = tweepy.OAuth2BearerHandler(bearer)
    else:
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)

    api = tweepy.API(auth, retry_count=3, timeout=100000, wait_on_rate_limit=True)

    print(keywords)
    if keywords:
        keywords = "(" + keywords.replace(",", " OR ") + ")"
    else:
        keywords = "a"

    if parameters["areaParameters1"] == "only":
        keywords += " filter:retweets "
    if parameters["areaParameters1"] == "do-not":
        keywords += " -filter:retweets "
    if parameters["areaParameters2"] == "only":
        keywords += " filter:links "
    if parameters["areaParameters2"] == "do-not":
        keywords += " -filter:links "
    if parameters["areaParameters3"] == "only":
        keywords += " filter:media "
    if parameters["areaParameters3"] == "do-not":
        keywords += " -filter:media "
    q = keywords
    print(q)
    limit = int(parameters["limit"])
    count_for_limit = limit
    while count_for_limit > 0:
        print("___________COUNT_FOR_LIMIT____________")
        print(count_for_limit)
        if parameters["SearchParameters1"] == "real-time":
            for tweet in tweepy.Cursor(api.search_tweets, q=q,  # searching tweets
                                       tweet_mode='extended',
                                       include_entities=True).items(count_for_limit):
                producer.produce(producer_topic, key=topic_key, value=json.dumps(tweet._json), callback=delivery_report)
                producer.flush()
                print("TweetsLoader: Send " + str(tweet._json)[:50])
                count_for_limit -= 1

        if parameters["SearchParameters1"] == "time-period":
            for tweet in tweepy.Cursor(api.search_tweets, q=q,  # searching tweets
                                       since=parameters["start_date"],  # start date
                                       until=parameters["end_date"],  # end date
                                       tweet_mode='extended',
                                       include_entities=True).items(count_for_limit):
                producer.produce(producer_topic, key=topic_key, value=json.dumps(tweet._json), callback=delivery_report)
                producer.flush()
                print("TweetsLoader: Send " + str(tweet._json)[:50])
                count_for_limit -= 1

        if parameters["SearchParameters1"] == "seven-days":
            for tweet in tweepy.Cursor(api.search_tweets, q=q,  # searching tweets
                                       since=parameters["start_date"],  # start date
                                       until=parameters["end_date"],  # end date
                                       tweet_mode='extended',
                                       include_entities=True).items(count_for_limit):
                producer.produce(producer_topic, key=topic_key, value=json.dumps(tweet._json), callback=delivery_report)
                producer.flush()
                print("TweetsLoader: Send " + str(tweet._json)[:50])
                count_for_limit -= 1

    producer.flush()
    producer.produce(producer_topic, key="INFO", value="END", callback=delivery_report)
    producer.flush()
    print("TweetsLoader: Send " + str("END")[:50])
