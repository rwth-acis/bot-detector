import json
from json import dumps

import tweepy as tweepy
from flask import Flask, render_template, url_for
from flask_pymongo import PyMongo
import folium
from geopy.exc import GeocoderTimedOut
from geopy.geocoders import Nominatim
import pymongo
from bs4 import BeautifulSoup
from flask import Markup
from bson.objectid import ObjectId
from werkzeug.utils import redirect

from dendritic_cell_algorithm.signal_generator import Signals

app = Flask(__name__, template_folder='frontend')

app.static_folder = 'frontend/static'

client = pymongo.MongoClient("")
db = client["TwitterData"]
col = db["Users"]


@app.route("/")
def home():
    return render_template("base.html")


@app.route("/index")
def about():
    return render_template("index.html")


@app.route('/result')
def result():
    users = col.find()
    try:
        folium_map = folium.Map(location=[0, 0], zoom_start=2)

        geo_locator = Nominatim(user_agent="findBots")

        for user in users:
            if "coordinates" in user:
                if user["coordinates"]:
                    if user["signals"]["k"] > 0:
                        folium.Marker(user["coordinates"], popup=user["user"]["name"],
                                      icon=folium.Icon(color='red')).add_to(
                            folium_map)
                    else:
                        folium.Marker(user["coordinates"], popup=user["user"]["name"],
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
                        if user["signals"]["k"] > 0:
                            folium.Marker([location.latitude, location.longitude], popup=user["user"]["name"],
                                          icon=folium.Icon(color='red')).add_to(
                                folium_map)
                        else:
                            folium.Marker([location.latitude, location.longitude], popup=user["user"]["name"],
                                          icon=folium.Icon(color='green')).add_to(
                                folium_map)

                        print("try to add loc")
                        col.update_one({"_id": user["_id"]},
                                       {'$set': {'coordinates': [location.latitude, location.longitude]}})
        return render_template('result.html', users=col.find(), folium_map=Markup(folium_map._repr_html_()))
    except Exception as e:
        # return dumps({'error': str(e)})
        print(e)


@app.route('/covid')
def covid():
    # input your credentials here
    consumer_key = ''
    consumer_secret = ''
    access_token = ''
    access_token_secret = ''

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
        new_signals.generate_signals(user["friends_count"], user["followers_count"], user["verified"],
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


@app.route('/recalculate')
def recalculate():
    users = col.find()
    for user in users:
        print("recalculate!")
        new_signals = Signals()
        new_signals.generate_signals(user["user"]["friends_count"], user["user"]["followers_count"],
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


@app.route('/user/<id>')
def user(id):
    user_found = col.find_one(ObjectId(id))
    print(user_found)
    return render_template('user.html', tweetArr=json.dumps(user_found["tweets"]), user=user_found)


if __name__ == "__main__":
    app.run(debug=True)
