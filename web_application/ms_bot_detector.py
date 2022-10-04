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


@app.route(os.environ['MS_BD_URL_PATH'] + "detect-bots", methods=['post', 'get'])
def detect_bots():
    if request.method == 'POST':
    
        producer_servers = request.form.get("producer_servers")
        consumer_servers = request.form.get("consumer_servers")
        consumer_group_id = request.form.get("consumer_group_id")
        consumer_offset = request.form.get("consumer_offset")
        consumer_topic = request.form.get("consumer_topic")
        collection_name = request.form.get("collection_name")

        p3 = multiprocessing.Process(name='p3', target=startBotDetector, args=(
            consumer_servers, consumer_group_id, consumer_offset, consumer_topic, producer_servers,
            collection_name,))

        p3.start()
    return "OK"


@app.route(os.environ['MS_BD_URL_PATH'] + "use-new-env-vars", methods=['post', 'get'])
def use_new_env_vars():
    if request.method == 'POST':

        col1 = db["ApplicationStatus"]
        main_parameters = col1.find_one({"name": "MainValues"})

        dca_coefficients = col1.find_one(
            {"name": "DCACoefficients", "version": main_parameters["coefficients_collection_id"]})

        for attr in list(dca_coefficients["coefficients"].keys()):
            os.environ[attr] = str(dca_coefficients["coefficients"][attr])

        return "BotDetector: Ok, DCACoefficients version " + main_parameters["coefficients_collection_id"]

    else:
        return 404


if __name__ == "__main__":
    # app.run()
    app.run(host='0.0.0.0')
