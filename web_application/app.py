import copy
import json
import os
from json import dumps

import tweepy as tweepy
from flask import Flask, render_template, url_for, request
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

load_dotenv()

app = Flask(__name__, template_folder='frontend')

app.static_folder = 'frontend/static'

client = pymongo.MongoClient(os.environ['DATABASE_URL'])
db = client["TwitterData"]
col = db["Users"]


@app.route("/")
def home():
    return render_template("base.html", app_url=os.environ['APP_URL'])


@app.route("/index")
def about():
    return render_template("index.html", app_url=os.environ['APP_URL'])


@app.route('/result')
def result():
    users = col.find()
    try:
        folium_map = folium.Map(location=[0, 0], zoom_start=2)

        geo_locator = Nominatim(user_agent="findBots")

        negative_count1 = 0
        positive_count1 = 0
        neutral_count1 = 0
        negative_count2 = 0
        positive_count2 = 0
        neutral_count2 = 0

        for user in users:
            if "coordinates" in user:
                if user["coordinates"]:
                    if user["signals"]["is_bot_probability"] >= 50:
                        folium.Marker(user["coordinates"], popup="@" + user["user"]["screen_name"],
                                      icon=folium.Icon(color='red')).add_to(
                            folium_map)
                    else:
                        if user["signals"]["is_bot_probability"] >= 30:
                            folium.Marker(user["coordinates"], popup="@" + user["user"]["screen_name"],
                                          icon=folium.Icon(color='orange')).add_to(
                                folium_map)
                        else:
                            folium.Marker(user["coordinates"], popup="@" + user["user"]["screen_name"],
                                          icon=folium.Icon(color='green')).add_to(
                                folium_map)
            else:
                if user["user"]["location"]:
                    try:
                        location = geo_locator.geocode(user["user"]["location"])
                        print(location)
                        if location is None:
                            print("try to add loc")
                            col.update_one({"_id": user["_id"]}, {'$set': {'coordinates': ""}})
                    except Exception as e:
                        continue
                    if location:
                        if user["signals"]["is_bot_probability"] >= 50:
                            folium.Marker([location.latitude, location.longitude],
                                          popup="@" + user["user"]["screen_name"],
                                          icon=folium.Icon(color='red')).add_to(
                                folium_map)
                        else:
                            if user["signals"]["is_bot_probability"] >= 30:
                                folium.Marker([location.latitude, location.longitude],
                                              popup="@" + user["user"]["screen_name"],
                                              icon=folium.Icon(color='orange')).add_to(
                                    folium_map)
                            else:
                                folium.Marker([location.latitude, location.longitude],
                                              popup="@" + user["user"]["screen_name"],
                                              icon=folium.Icon(color='green')).add_to(
                                    folium_map)

                        print("try to add loc")
                        col.update_one({"_id": user["_id"]},
                                       {'$set': {'coordinates': [location.latitude, location.longitude]}})
            if user["signals"]["is_bot_probability"] >= 50:
                if user["found_tweet"]["sentiment"] == "negative":
                    negative_count2 += 1
                if user["found_tweet"]["sentiment"] == "positive":
                    positive_count2 += 1
                if user["found_tweet"]["sentiment"] == "neutral":
                    neutral_count2 += 1
            else:
                if user["found_tweet"]["sentiment"] == "negative":
                    negative_count1 += 1
                if user["found_tweet"]["sentiment"] == "positive":
                    positive_count1 += 1
                if user["found_tweet"]["sentiment"] == "neutral":
                    neutral_count1 += 1

        return render_template('result.html', users=col.find(), folium_map=Markup(folium_map._repr_html_()),
                               users_list=str(list(col.find())), app_url=os.environ['APP_URL'],
                               negative_count1=negative_count1, positive_count1=positive_count1,
                               neutral_count1=neutral_count1, negative_count2=negative_count2,
                               positive_count2=positive_count2, neutral_count2=neutral_count2)
    except Exception as e:
        # return dumps({'error': str(e)})
        print(e)


@app.route('/covid')
def covid():
    # input your credentials here
    consumer_key = os.environ['CONSUMER_KEY']
    consumer_secret = os.environ['CONSUMER_SECRET']
    access_token = os.environ['ACCESS_TOKEN']
    access_token_secret = os.environ['ACCESS_TOKEN_SECRET']

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth, wait_on_rate_limit=True)

    # When using extended mode, text is replaced by a full_text, which contains the entire untruncated tweet (more than 140 characters)
    tweets = tweepy.Cursor(api.search_tweets, q="#covid19", lang="en", tweet_mode='extended').items(20)

    for tweet in tweets:
        # print("created_at: ", tweet.created_at, ", text: ", tweet.retweeted_status.full_text, ", user: user_id: ",tweet.user.id, ", user_name: ", tweet.user.name, ", followers_count: ", tweet.user.followers_count)
        userObj = {}
        user = api.get_user(screen_name=tweet.user.screen_name)._json
        user.pop('status', None)
        userObj["user"] = user
        userObj["found_tweet"] = tweet._json

        print("sentiment!")
        analyzer = SentimentIntensityAnalyzer()
        tweet_modified = remove_user_mentions(remove_urls(copy.deepcopy(userObj["found_tweet"])))
        sentence = tweet_modified["full_text"]
        sentiment = analyzer.polarity_scores(sentence)
        print(sentence)
        print(sentiment['compound'])
        if sentiment['compound'] >= 0.1:
            print("Positive")
            userObj["found_tweet"]["sentiment"] = "positive"

        elif sentiment['compound'] <= - 0.2:
            print("Negative")
            userObj["found_tweet"]["sentiment"] = "negative"

        else:
            print("Neutral")
            userObj["found_tweet"]["sentiment"] = "positive"

        userObj["tweets"] = []
        for fulltweet in api.user_timeline(screen_name=tweet.user.screen_name,
                                           # max 200 tweets
                                           count=10,
                                           include_rts=False,
                                           # Necessary to keep full_text
                                           tweet_mode='extended'
                                           ):
            tw = fulltweet._json
            tw.pop('user', None)
            userObj["tweets"].append(tw)

        new_signals = Signals()
        # friends_count, followers_count, verified, default_profile, default_profile_image, created_at, name,
        # screen_name, description, tweets
        new_signals.generate_signals(user["friends_count"], user["statuses_count"], user["followers_count"],
                                     user["verified"],
                                     user["default_profile"],
                                     user["default_profile_image"], user["created_at"], user["name"],
                                     user["screen_name"],
                                     user["description"],
                                     userObj["tweets"])

        print(new_signals.get_parameters())
        userObj["signals"] = new_signals.get_parameters()
        col.insert_one(dict(userObj))

    return "OK!"


@app.route('/delete')
def delete():
    users = col.find()
    for user in users:
        print("check!")
        print(user["_id"])
        if user["signals"]["k"] < 30:
            print("delete!")
            col.delete_one({"_id": user["_id"]})
    return "OK!"


@app.route('/all/recalculate')
def recalculate():
    users = col.find()
    for user in users:
        print("recalculate!")
        new_signals = Signals()
        new_signals.generate_signals(user["user"]["friends_count"], user["user"]["statuses_count"],
                                     user["user"]["followers_count"],
                                     user["user"]["verified"],
                                     user["user"]["default_profile"],
                                     user["user"]["default_profile_image"],
                                     user["user"]["created_at"],
                                     user["user"]["name"],
                                     user["user"]["screen_name"],
                                     user["user"]["description"],
                                     user["tweets"])
        col.update_one({"_id": user["_id"]},
                       {'$set': {'signals': new_signals.get_parameters()}})
    return "OK!"


@app.route('/calculate-sentiment')
def calculate_sentiment():
    users = col.find()
    for user in users:
        print("sentiment!")
        analyzer = SentimentIntensityAnalyzer()
        tweet = remove_user_mentions(remove_urls(user["found_tweet"]))
        sentence = tweet["full_text"]
        sentiment = analyzer.polarity_scores(sentence)
        print(sentence)
        print(sentiment['compound'])
        if sentiment['compound'] >= 0.1:
            print("Positive")
            col.update_one({"_id": user["_id"]},
                           {'$set': {'found_tweet.sentiment': "positive"}})

        elif sentiment['compound'] <= - 0.2:
            print("Negative")
            col.update_one({"_id": user["_id"]},
                           {'$set': {'found_tweet.sentiment': "negative"}})

        else:
            print("Neutral")
            col.update_one({"_id": user["_id"]},
                           {'$set': {'found_tweet.sentiment': "neutral"}})
    return "OK!"


@app.route('/recalculate/<id>')
def recalc(id):
    consumer_key = os.environ['CONSUMER_KEY']
    consumer_secret = os.environ['CONSUMER_SECRET']
    access_token = os.environ['ACCESS_TOKEN']
    access_token_secret = os.environ['ACCESS_TOKEN_SECRET']

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth, wait_on_rate_limit=True)

    user = col.find_one(ObjectId(id))

    col.update_one({"_id": user["_id"]},
                   {'$set': {'tweets': []}})

    for fulltweet in api.user_timeline(user_id=user["user"]["id"],
                                       # max 200 tweets
                                       count=20,
                                       include_rts=False,
                                       # Necessary to keep full_text
                                       tweet_mode='extended'
                                       ):
        tw = fulltweet._json
        tw.pop('user', None)

        """
        col.update_one({"_id": user["_id"]},
                       {'$pull': {'tweets': {'id': tw["id"]}}}
                       )
        """

        col.update_one({"_id": user["_id"]},
                       {'$addToSet': {'tweets': tw}})

    user = col.find_one(ObjectId(id))
    new_signals = Signals()
    new_signals.generate_signals(user["user"]["friends_count"], user["user"]["statuses_count"],
                                 user["user"]["followers_count"],
                                 user["user"]["verified"],
                                 user["user"]["default_profile"],
                                 user["user"]["default_profile_image"],
                                 user["user"]["created_at"],
                                 user["user"]["name"],
                                 user["user"]["screen_name"],
                                 user["user"]["description"],
                                 user["tweets"])
    col.update_one({"_id": user["_id"]},
                   {'$set': {'signals': new_signals.get_parameters()}})

    return redirect(os.environ['APP_URL'] + "/user/" + id)


@app.route('/user-check/<screen_name>', methods=['post', 'get'])
def user_check(screen_name):
    if request.method == 'POST':
        screen_name = request.form.get('screen-name').replace("@", "")
    if screen_name == "form":
        return render_template('user-check.html', blank=True, exception=False)

    consumer_key = os.environ['CONSUMER_KEY']
    consumer_secret = os.environ['CONSUMER_SECRET']
    access_token = os.environ['ACCESS_TOKEN']
    access_token_secret = os.environ['ACCESS_TOKEN_SECRET']

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth, wait_on_rate_limit=True)

    userObj = {}
    try:
        user = api.get_user(screen_name=screen_name)._json
        user.pop('status', None)
        userObj["user"] = user

        userObj["tweets"] = []
        print(screen_name)
        tweets_raw = api.user_timeline(screen_name=screen_name,
                                       # max 200 tweets
                                       count=20,
                                       include_rts=False,
                                       # Necessary to keep full_text
                                       tweet_mode='extended'
                                       )
        print(tweets_raw)
        for fulltweet in tweets_raw:
            tw = fulltweet._json
            tw.pop('user', None)
            userObj["tweets"].append(tw)

        new_signals = Signals()
        # friends_count, followers_count, verified, default_profile, default_profile_image, created_at, name,
        # screen_name, description, tweets
        new_signals.generate_signals(user["friends_count"], user["statuses_count"], user["followers_count"],
                                     user["verified"],
                                     user["default_profile"],
                                     user["default_profile_image"], user["created_at"], user["name"],
                                     user["screen_name"],
                                     user["description"],
                                     userObj["tweets"])

        print(new_signals.get_parameters())
        userObj["signals"] = new_signals.get_parameters()

        return render_template('user-check.html', blank=False, exception=False, tweetArr=json.dumps(userObj["tweets"]), user=userObj)
    except Exception as e:
        # return dumps({'error': str(e)})
        return render_template('user-check.html', blank=True, exception=True)

@app.route('/user/<id>')
def user(id):
    try:
        user_found = col.find_one(ObjectId(id))
        if user_found:
            return render_template('user.html', tweetArr=json.dumps(user_found["tweets"]), user=user_found,
                                   tweet=json.dumps(user_found["found_tweet"]))
        else:
            return render_template('404.html')
    except Exception as e:
        return render_template('404.html')


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


if __name__ == "__main__":
    app.run(debug=True)
