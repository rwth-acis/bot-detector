import copy
import json
import os
import datetime
from json import dumps
import logging
import uuid

import tweepy
from flask import Flask, render_template, url_for, request, send_from_directory
from flask_pymongo import PyMongo
import folium
from geopy.exc import GeocoderTimedOut
from geopy.geocoders import Nominatim
import pymongo

from flask import Markup
from bson.objectid import ObjectId
from werkzeug.utils import redirect
from dotenv import load_dotenv

from dendritic_cell_algorithm.signal_generator import Signals, remove_urls, remove_user_mentions
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from python_kafka.SignalGenerator import startSignalGenerator
from python_kafka.TweetsLoader import startTweetsLoader
from python_kafka.TweetsLoaderWithParameters import startTweetsLoaderWithParameters
from python_kafka.BotDetector import startBotDetector
import multiprocessing

from confluent_kafka import Producer

load_dotenv()
logging.getLogger().setLevel(logging.INFO)

app = Flask(__name__, template_folder='frontend')

app.static_folder = 'frontend/static'

if int(os.environ['USE_DATABASE_SERVICE']):
    print("use db service")
    client = pymongo.MongoClient(os.environ['DATABASE_SERVICE'], int(os.environ['DATABASE_PORT']),
                                 username=os.environ['DATABASE_USERNAME'],
                                 password=os.environ['DATABASE_PASSWORD'])
else:
    print("don't use db service")
    client = pymongo.MongoClient(os.environ['DATABASE_URL'])

try:
    db = client["TwitterData"]
    col = db["Users1"]
except AttributeError as error:
    print(error)


@app.route(os.environ['MS_TL_URL_PATH'] + "load-tweets", methods=['post', 'get'])
def load_tweets():
    if request.method == 'POST':
        print(request.form)

        collection = request.form.get('collection')
        print(collection)
        keywords = request.form.get('keywords')
        print(keywords)
        limit = request.form.get('limit')
        print(limit)
        areaParameters1 = request.form.get('areaParameters1')
        print(areaParameters1)
        areaParameters2 = request.form.get('areaParameters2')
        print(areaParameters2)
        areaParameters3 = request.form.get('areaParameters3')
        print(areaParameters3)
        SearchParameters1 = request.form.get('SearchParameters1')
        print(SearchParameters1)
        start_date = request.form.get('start-date')
        end_date = request.form.get('end-date')
        requestOptions = request.form.get('requestOptions')
        print(requestOptions)

        parameters = {
            "collection": str(collection),
            "keywords": keywords,
            "limit": limit,
            "areaParameters1": areaParameters1,
            "areaParameters2": areaParameters2,
            "areaParameters3": areaParameters3,
            "SearchParameters1": SearchParameters1,
            "start_date": start_date,
            "end_date": end_date,
            "requestOptions": requestOptions
        }

        producer_servers = request.form.get("producer_servers")
        producer_topic = request.form.get("producer_topic")
        topic_key = request.form.get("topic_key")
        # parameters = request.form.get("parameters")

        consumer_key = request.form.get("consumer_key")
        consumer_secret = request.form.get("consumer_secret")
        access_token = request.form.get("access_token")
        access_token_secret = request.form.get("access_token_secret")
        bearer = request.form.get("bearer")

        use_bearer = int(os.environ['USE_BEARER'])

        if parameters["SearchParameters1"] == "real-time":
            p1 = multiprocessing.Process(name='p1', target=startTweetsLoader,
                                         args=(
                                             keywords, producer_servers, producer_topic, topic_key, parameters,
                                             consumer_key, consumer_secret, access_token,
                                             access_token_secret,))
        else:
            if use_bearer:
                print("use_bearer")
                p1 = multiprocessing.Process(name='p1', target=startTweetsLoaderWithParameters,
                                             args=(
                                                 keywords, producer_servers, producer_topic, topic_key, parameters,
                                                 None, None, None, None, bearer,))
            else:
                print("don't use_bearer")
                p1 = multiprocessing.Process(name='p1', target=startTweetsLoaderWithParameters,
                                             args=(
                                                 keywords, producer_servers, producer_topic, topic_key,
                                                 parameters, consumer_key, consumer_secret, access_token,
                                                 access_token_secret, None,))
        p1.start()
    return "OK"


if __name__ == "__main__":
    # app.run()
    app.run(host='0.0.0.0')
