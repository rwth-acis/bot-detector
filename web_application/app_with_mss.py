import copy
import json
import os
import datetime
import urllib
from json import dumps
import logging
import uuid

import requests
import tweepy
from bson import json_util

from flask_oidc import OpenIDConnect
from flask import Flask, render_template, url_for, request, send_from_directory, jsonify, g, abort
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

app.config.update({
    'SECRET_KEY': 'NotVerySecretKey',
    'TESTING': True,
    'DEBUG': True,
    'OIDC_CLIENT_SECRETS': 'client_secrets.json',
    'OIDC_ID_TOKEN_COOKIE_SECURE': False,
    'OIDC_REQUIRE_VERIFIED_EMAIL': False,
    'OIDC_USER_INFO_ENABLED': True,
    'OIDC_OPENID_REALM': 'main',
    'OIDC_SCOPES': ['openid', 'email', 'profile'],
    'OIDC_INTROSPECTION_AUTH_METHOD': 'client_secret_post',
    'OIDC_TOKEN_TYPE_HINT': 'access_token'
})

app.config["OIDC_CALLBACK_ROUTE"] = "/bot-detector/*"

oidc = OpenIDConnect(app)

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


@app.route(os.environ['APP_URL_PATH'] + 'login', methods=['GET'])
@oidc.require_login
def secureEndpoint():
    redirect_to = request.args.get('redirect-to')
    return redirect((os.environ['APP_URL']) + "/" + redirect_to)
    return "OK"


@app.route(os.environ['APP_URL_PATH'] + 'profile', methods=['GET'])
@oidc.require_login
def profile():
    info = oidc.user_getinfo(['preferred_username', 'email', 'sub'])

    username = info.get('preferred_username')
    email = info.get('email')
    user_id = info.get('sub')

    return render_template("profile.html", app_url=os.environ['APP_URL'],
                           app_url_path=os.environ['APP_URL_PATH'][:-1],
                           example_db=os.environ['EXAMPLE_DB'], name=username, email=email, user_id=user_id,
                           user_name=username)


@app.route(os.environ['APP_URL_PATH'] + 'logout', methods=['GET'])
# @oidc.require_login
def logout():
    # return redirect((os.environ['APP_URL']) + "profile")
    oidc.logout()
    return redirect(
        "https://auth.las2peer.org/auth/realms/main" + "/protocol/openid-connect/logout?redirect_uri=" + urllib.parse.quote(
            os.environ['APP_URL'] + "/", safe=''))


@app.route(os.environ['APP_URL_PATH'] + "static/images/<image_name>")
def static_dir(image_name):
    return send_from_directory("frontend/static/images", image_name)


@app.route(os.environ['APP_URL_PATH'] + 'static/<path:path>')
def send_js(path):
    return send_from_directory("frontend/static/", path)


@app.route(os.environ['APP_URL_PATH'])
def home():
    if oidc.user_loggedin:
        info = oidc.user_getinfo(['preferred_username', 'email', 'sub'])

        username = info.get('preferred_username')
        return render_template("base.html", app_url=os.environ['APP_URL'],
                               app_url_path=os.environ['APP_URL_PATH'][:-1],
                               example_db=os.environ['EXAMPLE_DB'], user_name=username)
    else:
        return render_template("base.html", app_url=os.environ['APP_URL'],
                               app_url_path=os.environ['APP_URL_PATH'][:-1],
                               example_db=os.environ['EXAMPLE_DB'])


###############################################################################
# ============================      API       ==================================
###############################################################################

@app.route(os.environ['APP_URL_PATH'] + 'api/result/<id>')
def api_resultid(id):
    col1 = db[str(id)]
    users = col1.find()
    col2 = db["Requests"]
    parameters = col2.find_one({"collection": str(id)})
    print(parameters)
    ready_count = 0
    try:
        for user in users:
            ready_count += 1

        # print(parameters["limit"])
        # print("_______________")
        if not ("completed" in parameters):
            ready_count = int(ready_count / (int(parameters["limit"])) * 100)
        else:
            ready_count = 100
        # print(ready_count)
        # print(jsonify(users=col1.find(), collection=str(id), parameters=parameters, ready_percent=ready_count))
        return json_util.dumps(
            {"users": col1.find(), "collection": str(id), "parameters": parameters, "ready_percent": ready_count})

    except Exception as e:
        # return dumps({'error': str(e)})
        logging.info(e)


@app.route(os.environ['APP_URL_PATH'] + "api/create-request")
def api_part_result():
    # print(request.json)
    id = str(uuid.uuid4())
    logging.info(id)

    # ________________________________________________________
    # _______________________PARAMETERS_______________________
    # ________________________________________________________

    try:
        keywords = request.args.get('keywords')
        print(keywords)
        limit = request.args.get('limit')
        print(limit)
        areaParameters1 = request.args.get('areaParameters1')
        print(areaParameters1)
        areaParameters2 = request.args.get('areaParameters2')
        print(areaParameters2)
        areaParameters3 = request.args.get('areaParameters3')
        print(areaParameters3)
        SearchParameters1 = request.args.get('SearchParameters1')
        print(SearchParameters1)
        start_date = request.args.get('start-date')
        end_date = request.args.get('end-date')
        requestOptions = request.args.get('requestOptions')
        print(requestOptions)

        if SearchParameters1 == "time-period":
            if not start_date:
                start_date = datetime.datetime.date(datetime.datetime.now() - datetime.timedelta(days=7)).strftime(
                    "%Y-%m-%d")
            if not end_date:
                end_date = datetime.datetime.date(datetime.datetime.now()).strftime("%Y-%m-%d")

        if SearchParameters1 == "seven-days":
            start_date = datetime.datetime.date(datetime.datetime.now() - datetime.timedelta(days=7)).strftime(
                "%Y-%m-%d")
            end_date = datetime.datetime.date(datetime.datetime.now()).strftime("%Y-%m-%d")

        if SearchParameters1 == "time-period" and (start_date > end_date):
            date = start_date
            start_date = end_date
            end_date = date

        if SearchParameters1 == "time-period" and (start_date == end_date):
            end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")
            end_date = datetime.datetime.date(end_date + datetime.timedelta(days=1)).strftime("%Y-%m-%d")

        print(start_date)
        print(end_date)

        if requestOptions == "basic":
            SearchParameters1 = "mixed"
            print(SearchParameters1)
            limit = 20
            print(limit)
            areaParameters1 = "all"
            print(areaParameters1)
            areaParameters2 = "all"
            print(areaParameters2)
            areaParameters3 = "all"
            print(areaParameters3)

        if SearchParameters1 == "real-time":
            areaParameters1 = "all"
            print(areaParameters1)
            areaParameters2 = "all"
            print(areaParameters2)
            areaParameters3 = "all"
            print(areaParameters3)

        parameters = {
            "collection": str(id),
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

        col1 = db[str(id)]
        col2 = db["Requests"]
        col2.insert_one(parameters)

        # ___________________________________________________________
        # ______________________END_PARAMETERS_______________________
        # ___________________________________________________________

        consumer_key = os.environ['CONSUMER_KEY']
        consumer_secret = os.environ['CONSUMER_SECRET']
        access_token = os.environ['ACCESS_TOKEN']
        access_token_secret = os.environ['ACCESS_TOKEN_SECRET']
        bearer = os.environ['BEARER']

        kafka_url = os.environ['KAFKA_URL']

        tl_data = {
            "keywords": keywords,
            "producer_servers": kafka_url,
            "producer_topic": str(id),
            "topic_key": "test1-id",
            "parameters": parameters,
            "consumer_key": consumer_key,
            "consumer_secret": consumer_secret,
            "access_token": access_token,
            "access_token_secret": access_token_secret,
            "bearer": bearer,

            "collection": str(id),
            "limit": limit,
            "areaParameters1": areaParameters1,
            "areaParameters2": areaParameters2,
            "areaParameters3": areaParameters3,
            "SearchParameters1": SearchParameters1,
            "start_date": start_date,
            "end_date": end_date,
            "requestOptions": requestOptions
        }

        sg_data = {
            "consumer_servers": kafka_url,
            "consumer_group_id": 'test1-id',
            "consumer_offset": 'earliest',
            "consumer_topic": str(id),
            "producer_servers": kafka_url,
            "producer_topic": (str(id) + "-signals"),
            "consumer_key": consumer_key,
            "consumer_secret": consumer_secret,
            "access_token": access_token,
            "access_token_secret": access_token_secret,
            "bearer": bearer
        }

        bd_data = {
            "consumer_servers": kafka_url,
            "consumer_group_id": 'test1-id',
            "consumer_offset": 'earliest',
            "consumer_topic": (str(id) + "-signals"),
            "producer_servers": kafka_url,
            "collection_name": str(id)
        }

        ms_tl_addr = os.environ['MS_TL_ADDRESS']
        ms_sg_addr = os.environ['MS_SG_ADDRESS']
        ms_bd_addr = os.environ['MS_BD_ADDRESS']

        tl_result = requests.post((ms_tl_addr + os.environ['MS_TL_URL_PATH'] + "load-tweets"), data=tl_data)
        print(tl_result.text)
        print(tl_data)
        sg_result = requests.post((ms_sg_addr + os.environ['MS_SG_URL_PATH'] + "generate-signals"), data=sg_data)
        print(sg_result.text)
        bd_result = requests.post((ms_bd_addr + os.environ['MS_BD_URL_PATH'] + "detect-bots"), data=bd_data)
        print(bd_result.text)

        return json_util.dumps(parameters), 201

    except Exception as e:
        return jsonify(e), 404


@app.route(os.environ['APP_URL_PATH'] + 'api/user-check/<screen_name>')
def api_user_check(screen_name):
    screen_name = screen_name.replace("@", "")

    consumer_key = os.environ['CONSUMER_KEY']
    consumer_secret = os.environ['CONSUMER_SECRET']
    access_token = os.environ['ACCESS_TOKEN']
    access_token_secret = os.environ['ACCESS_TOKEN_SECRET']
    bearer = os.environ['BEARER']
    use_bearer = int(os.environ['USE_BEARER'])

    if use_bearer:
        auth = tweepy.OAuth2BearerHandler(bearer)
    else:
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)

    api = tweepy.API(auth, retry_count=3, timeout=100000, wait_on_rate_limit=True)

    userObj = {}
    try:
        user = api.get_user(screen_name=screen_name)._json
        user.pop('status', None)
        userObj["user"] = user

        userObj["tweets"] = []
        logging.info(screen_name)
        tweets_raw = api.user_timeline(screen_name=screen_name,
                                       # max 200 tweets
                                       count=20,
                                       include_rts=False,
                                       # Necessary to keep full_text
                                       tweet_mode='extended'
                                       )
        logging.info(tweets_raw)
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

        logging.info(new_signals.get_parameters())
        userObj["signals"] = new_signals.get_parameters()

        return jsonify(userObj), 200

    except Exception as e:
        # return dumps({'error': str(e)})
        return jsonify(e), 404


@app.route(os.environ['APP_URL_PATH'] + 'api/<collection>/user/<id>')
def api_user(collection, id):
    try:
        col = db[collection]
        user_found = col.find_one(ObjectId(id))
        if user_found:
            return json_util.dumps(user_found)
        else:
            return 404
    except Exception as e:
        return jsonify(e), 404


###############################################################################
# ==========================      API END       ================================
###############################################################################


@app.route(os.environ['APP_URL_PATH'] + 'result/<id>')
def resultid(id):
    col1 = db[str(id)]
    users = col1.find()
    col2 = db["Requests"]
    parameters = col2.find_one({"collection": str(id)})
    print(parameters)
    if parameters is not None:
        if "owner" in parameters:
            if parameters["owner"] is not None:
                if not oidc.user_loggedin:
                    return redirect(
                        (os.environ['APP_URL']) + "/login?redirect-to=" + urllib.parse.quote("/result/" + str(id),
                                                                                             safe=''))

                info = oidc.user_getinfo(['preferred_username', 'email', 'sub'])
                username = info.get('preferred_username')
                print("loggedin")
                print(info.get('sub'))
                print(parameters["owner"])
                if not (info.get('sub') in parameters["owner"]["sub"]):
                    return error403("403")
                    # return abort(403)

    else:
        return page_not_found("404")
        # return abort(404)

    ready_count = 0
    try:
        folium_map = folium.Map(location=[0, 0], zoom_start=2)

        negative_count1 = 0
        positive_count1 = 0
        neutral_count1 = 0
        negative_count2 = 0
        positive_count2 = 0
        neutral_count2 = 0

        for user in users:
            ready_count += 1
            # print(user)
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

            if user["signals"]["is_bot_probability"] >= 50:
                if user["found_tweet"]["sentiment"] == "negative":
                    negative_count1 += 1
                if user["found_tweet"]["sentiment"] == "positive":
                    positive_count1 += 1
                if user["found_tweet"]["sentiment"] == "neutral":
                    neutral_count1 += 1
            else:
                if user["found_tweet"]["sentiment"] == "negative":
                    negative_count2 += 1
                if user["found_tweet"]["sentiment"] == "positive":
                    positive_count2 += 1
                if user["found_tweet"]["sentiment"] == "neutral":
                    neutral_count2 += 1

        print(parameters["limit"])
        print("_______________")
        if not ("completed" in parameters):
            ready_count = int(ready_count / (int(parameters["limit"])) * 100)
        else:
            ready_count = 100
        print(ready_count)
        if oidc.user_loggedin:
            info = oidc.user_getinfo(['preferred_username', 'email', 'sub'])

            username = info.get('preferred_username')
            return render_template('result.html', users=col1.find(), folium_map=Markup(folium_map._repr_html_()),
                                   app_url=os.environ['APP_URL'],
                                   negative_count1=negative_count1, positive_count1=positive_count1,
                                   neutral_count1=neutral_count1, negative_count2=negative_count2,
                                   positive_count2=positive_count2, neutral_count2=neutral_count2,
                                   collection=str(id), parameters=parameters, ready_count=ready_count,
                                   app_url_path=os.environ['APP_URL_PATH'][:-1],
                                   example_db=os.environ['EXAMPLE_DB'], user_name=username)
        else:
            return render_template('result.html', users=col1.find(), folium_map=Markup(folium_map._repr_html_()),
                                   app_url=os.environ['APP_URL'],
                                   negative_count1=negative_count1, positive_count1=positive_count1,
                                   neutral_count1=neutral_count1, negative_count2=negative_count2,
                                   positive_count2=positive_count2, neutral_count2=neutral_count2,
                                   collection=str(id), parameters=parameters, ready_count=ready_count,
                                   app_url_path=os.environ['APP_URL_PATH'][:-1],
                                   example_db=os.environ['EXAMPLE_DB'])

    except Exception as e:
        # return dumps({'error': str(e)})
        logging.info(e)


@app.route(os.environ['APP_URL_PATH'] + 'requests-history')
def history():
    col2 = db["Requests"]
    r = list(col2.find())
    for req in r:
        req["_id"] = str(req["_id"].generation_time).replace("+00:00", "")

    if oidc.user_loggedin:
        info = oidc.user_getinfo(['preferred_username', 'email', 'sub'])

        username = info.get('preferred_username')
        return render_template('history.html', requests=r,
                               app_url=os.environ['APP_URL'],
                               app_url_path=os.environ['APP_URL_PATH'][:-1],
                               example_db=os.environ['EXAMPLE_DB'], user_name=username)
    else:
        return render_template('history.html', requests=r,
                               app_url=os.environ['APP_URL'],
                               app_url_path=os.environ['APP_URL_PATH'][:-1],
                               example_db=os.environ['EXAMPLE_DB'])


@app.route(os.environ['APP_URL_PATH'] + 'dashboard')
@oidc.require_login
def dashboard():
    info = oidc.user_getinfo(['preferred_username', 'email', 'sub'])
    username = info.get('preferred_username')
    col1 = db["Permissions"]
    user = col1.find_one({"user_id": info.get('sub')})

    r = []
    col2 = db["Requests"]
    if user is not None:
        for collection in user["owner"]:
            req = col2.find_one({"collection": collection})
            if req is not None:
                r.append(req)

        for req in r:
            req["_id"] = str(req["_id"].generation_time).replace("+00:00", "")

    print(r)

    return render_template('history.html', requests=r,
                           app_url=os.environ['APP_URL'],
                           app_url_path=os.environ['APP_URL_PATH'][:-1],
                           example_db=os.environ['EXAMPLE_DB'], user_name=username, user_history=True)


@app.route(os.environ['APP_URL_PATH'] + 'dashboard/delete/<id>')
@oidc.require_login
def dashboard_delete_request(id):
    info = oidc.user_getinfo(['preferred_username', 'email', 'sub'])
    username = info.get('preferred_username')

    col2 = db["Requests"]
    parameters = col2.find_one({"collection": str(id)})

    if parameters is not None:
        if "owner" in parameters:
            if parameters["owner"] is not None:
                if not (info.get('sub') in parameters["owner"]["sub"]):
                    return error403("403")
            else:
                return error403("403")

    else:
        return page_not_found("404")

    col2.delete_one({"collection": str(id)})
    db[str(id)].drop()

    col1 = db["Permissions"]

    col1.update_one({"user_id": info.get('sub')}, {'$pullAll': {'owner': [id]}})

    return redirect((os.environ['APP_URL']) + "/dashboard")


@app.route(os.environ['APP_URL_PATH'] + 'access/<id>')
@oidc.require_login
def access(id):
    info = oidc.user_getinfo(['preferred_username', 'email', 'sub'])
    username = info.get('preferred_username')

    # col1 = db["Permissions"]

    # user = col1.find_one({"user_id": info.get('sub')})

    col2 = db["Requests"]
    req = col2.find_one({"collection": str(id)})

    if not (info.get('sub') in req["owner"]["sub"]):
        return error403("403")

    req["_id"] = str(req["_id"].generation_time).replace("+00:00", "")

    return render_template('access.html', collection_id=id,
                           app_url=os.environ['APP_URL'],
                           app_url_path=os.environ['APP_URL_PATH'][:-1],
                           example_db=os.environ['EXAMPLE_DB'], user_name=username, user_id=req["owner"]["sub"],
                           read_permission=req["read_permission"], write_permission=req["write_permission"])


@app.route(os.environ['APP_URL_PATH'] + "table")
def table():
    if oidc.user_loggedin:
        info = oidc.user_getinfo(['preferred_username', 'email', 'sub'])

        username = info.get('preferred_username')
        return render_template("table.html", app_url=os.environ['APP_URL'],
                               app_url_path=os.environ['APP_URL_PATH'][:-1],
                               example_db=os.environ['EXAMPLE_DB'], user_name=username)
    else:
        return render_template("table.html", app_url=os.environ['APP_URL'],
                               app_url_path=os.environ['APP_URL_PATH'][:-1],
                               example_db=os.environ['EXAMPLE_DB'])


@app.route(os.environ['APP_URL_PATH'] + "index")
def about():
    if oidc.user_loggedin:
        info = oidc.user_getinfo(['preferred_username', 'email', 'sub'])

        username = info.get('preferred_username')
        return render_template("index.html", app_url=os.environ['APP_URL'],
                               app_url_path=os.environ['APP_URL_PATH'][:-1],
                               example_db=os.environ['EXAMPLE_DB'], user_name=username)
    else:
        return render_template("index.html", app_url=os.environ['APP_URL'],
                               app_url_path=os.environ['APP_URL_PATH'][:-1],
                               example_db=os.environ['EXAMPLE_DB'])


@app.route(os.environ['APP_URL_PATH'] + "part-result", methods=['post', 'get'])
def part_result():
    if request.method == 'POST':
        print(request.form)
        id = str(uuid.uuid4())
        logging.info(id)

        # ________________________________________________________
        # _______________________PARAMETERS_______________________
        # ________________________________________________________

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

        if SearchParameters1 == "time-period":
            if not start_date:
                start_date = datetime.datetime.date(datetime.datetime.now() - datetime.timedelta(days=7)).strftime(
                    "%Y-%m-%d")
            if not end_date:
                end_date = datetime.datetime.date(datetime.datetime.now()).strftime("%Y-%m-%d")

        if SearchParameters1 == "seven-days":
            start_date = datetime.datetime.date(datetime.datetime.now() - datetime.timedelta(days=7)).strftime(
                "%Y-%m-%d")
            end_date = datetime.datetime.date(datetime.datetime.now()).strftime("%Y-%m-%d")

        if (start_date > end_date) and SearchParameters1 == "time-period":
            date = start_date
            start_date = end_date
            end_date = date

        if (start_date == end_date) and SearchParameters1 == "time-period":
            end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")
            end_date = datetime.datetime.date(end_date + datetime.timedelta(days=1)).strftime("%Y-%m-%d")

        print(start_date)
        print(end_date)

        if requestOptions == "basic":
            SearchParameters1 = "mixed"
            print(SearchParameters1)
            limit = 20
            print(limit)
            areaParameters1 = "all"
            print(areaParameters1)
            areaParameters2 = "all"
            print(areaParameters2)
            areaParameters3 = "all"
            print(areaParameters3)

        if SearchParameters1 == "real-time":
            areaParameters1 = "all"
            print(areaParameters1)
            areaParameters2 = "all"
            print(areaParameters2)
            areaParameters3 = "all"
            print(areaParameters3)

        if oidc.user_loggedin:
            info = oidc.user_getinfo(['preferred_username', 'email', 'sub'])

            parameters = {
                "collection": str(id),
                "keywords": keywords,
                "limit": limit,
                "areaParameters1": areaParameters1,
                "areaParameters2": areaParameters2,
                "areaParameters3": areaParameters3,
                "SearchParameters1": SearchParameters1,
                "start_date": start_date,
                "end_date": end_date,
                "requestOptions": requestOptions,
                "owner": info,
                "read_permission": [],
                "write_permission": [],
            }

            col3 = db["Permissions"]
            col3.update_one({'user_id': info.get('sub')}, {"$push": {"owner": str(id)}}, upsert=True);

        else:
            parameters = {
                "collection": str(id),
                "keywords": keywords,
                "limit": limit,
                "areaParameters1": areaParameters1,
                "areaParameters2": areaParameters2,
                "areaParameters3": areaParameters3,
                "SearchParameters1": SearchParameters1,
                "start_date": start_date,
                "end_date": end_date,
                "requestOptions": requestOptions,
                "owner": None
            }

        col1 = db[str(id)]
        col2 = db["Requests"]
        col2.insert_one(parameters)

        # ___________________________________________________________
        # ______________________END_PARAMETERS_______________________
        # ___________________________________________________________

        consumer_key = os.environ['CONSUMER_KEY']
        consumer_secret = os.environ['CONSUMER_SECRET']
        access_token = os.environ['ACCESS_TOKEN']
        access_token_secret = os.environ['ACCESS_TOKEN_SECRET']
        bearer = os.environ['BEARER']

        kafka_url = os.environ['KAFKA_URL']

        tl_data = {
            "keywords": keywords,
            "producer_servers": kafka_url,
            "producer_topic": str(id),
            "topic_key": "test1-id",
            "parameters": parameters,
            "consumer_key": consumer_key,
            "consumer_secret": consumer_secret,
            "access_token": access_token,
            "access_token_secret": access_token_secret,
            "bearer": bearer,

            "collection": str(id),
            "limit": limit,
            "areaParameters1": areaParameters1,
            "areaParameters2": areaParameters2,
            "areaParameters3": areaParameters3,
            "SearchParameters1": SearchParameters1,
            "start_date": start_date,
            "end_date": end_date,
            "requestOptions": requestOptions
        }

        sg_data = {
            "consumer_servers": kafka_url,
            "consumer_group_id": 'test1-id',
            "consumer_offset": 'earliest',
            "consumer_topic": str(id),
            "producer_servers": kafka_url,
            "producer_topic": (str(id) + "-signals"),
            "consumer_key": consumer_key,
            "consumer_secret": consumer_secret,
            "access_token": access_token,
            "access_token_secret": access_token_secret,
            "bearer": bearer
        }

        bd_data = {
            "consumer_servers": kafka_url,
            "consumer_group_id": 'test1-id',
            "consumer_offset": 'earliest',
            "consumer_topic": (str(id) + "-signals"),
            "producer_servers": kafka_url,
            "collection_name": str(id)
        }

        ms_tl_addr = os.environ['MS_TL_ADDRESS']
        ms_sg_addr = os.environ['MS_SG_ADDRESS']
        ms_bd_addr = os.environ['MS_BD_ADDRESS']

        tl_result = requests.post((ms_tl_addr + os.environ['MS_TL_URL_PATH'] + "load-tweets"), data=tl_data)
        print(tl_result.text)
        print(tl_data)
        sg_result = requests.post((ms_sg_addr + os.environ['MS_SG_URL_PATH'] + "generate-signals"), data=sg_data)
        print(sg_result.text)
        bd_result = requests.post((ms_bd_addr + os.environ['MS_BD_URL_PATH'] + "detect-bots"), data=bd_data)
        print(bd_result.text)

    return redirect((os.environ['APP_URL']) + "/result/" + str(id))


@app.route(os.environ['APP_URL_PATH'] + 'user-check/<screen_name>', methods=['post', 'get'])
def user_check(screen_name):
    if request.method == 'POST':
        screen_name = request.form.get('screen-name').replace("@", "")
    if screen_name == "form":
        if oidc.user_loggedin:
            info = oidc.user_getinfo(['preferred_username', 'email', 'sub'])
            username = info.get('preferred_username')
            return render_template('user-check.html', blank=True, exception=False,
                                   app_url=os.environ['APP_URL'],
                                   app_url_path=os.environ['APP_URL_PATH'][:-1],
                                   example_db=os.environ['EXAMPLE_DB'], user_name=username)
        else:
            return render_template('user-check.html', blank=True, exception=False,
                                   app_url=os.environ['APP_URL'],
                                   app_url_path=os.environ['APP_URL_PATH'][:-1],
                                   example_db=os.environ['EXAMPLE_DB'])

    consumer_key = os.environ['CONSUMER_KEY']
    consumer_secret = os.environ['CONSUMER_SECRET']
    access_token = os.environ['ACCESS_TOKEN']
    access_token_secret = os.environ['ACCESS_TOKEN_SECRET']
    bearer = os.environ['BEARER']
    use_bearer = int(os.environ['USE_BEARER'])

    if use_bearer:
        auth = tweepy.OAuth2BearerHandler(bearer)
    else:
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)

    api = tweepy.API(auth, retry_count=3, timeout=100000, wait_on_rate_limit=True)

    userObj = {}
    try:
        user = api.get_user(screen_name=screen_name)._json
        user.pop('status', None)
        userObj["user"] = user

        userObj["tweets"] = []
        logging.info(screen_name)
        tweets_raw = api.user_timeline(screen_name=screen_name,
                                       # max 200 tweets
                                       count=20,
                                       include_rts=False,
                                       # Necessary to keep full_text
                                       tweet_mode='extended'
                                       )
        logging.info(tweets_raw)
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

        logging.info(new_signals.get_parameters())
        userObj["signals"] = new_signals.get_parameters()

        if oidc.user_loggedin:
            info = oidc.user_getinfo(['preferred_username', 'email', 'sub'])

            username = info.get('preferred_username')

            return render_template('user-check.html', blank=False, exception=False,
                                   tweetArr=json.dumps(userObj["tweets"]),
                                   user=userObj,
                                   app_url=os.environ['APP_URL'],
                                   app_url_path=os.environ['APP_URL_PATH'][:-1],
                                   example_db=os.environ['EXAMPLE_DB'], user_name=username)
        else:
            return render_template('user-check.html', blank=False, exception=False,
                                   tweetArr=json.dumps(userObj["tweets"]),
                                   user=userObj,
                                   app_url=os.environ['APP_URL'],
                                   app_url_path=os.environ['APP_URL_PATH'][:-1],
                                   example_db=os.environ['EXAMPLE_DB'])


    except Exception as e:
        # return dumps({'error': str(e)})
        if oidc.user_loggedin:
            info = oidc.user_getinfo(['preferred_username', 'email', 'sub'])
            username = info.get('preferred_username')
            return render_template('user-check.html', blank=True, exception=True,
                                   app_url=os.environ['APP_URL'],
                                   app_url_path=os.environ['APP_URL_PATH'][:-1],
                                   example_db=os.environ['EXAMPLE_DB'], user_name=username)
        else:
            return render_template('user-check.html', blank=True, exception=True,
                                   app_url=os.environ['APP_URL'],
                                   app_url_path=os.environ['APP_URL_PATH'][:-1],
                                   example_db=os.environ['EXAMPLE_DB'])


@app.route(os.environ['APP_URL_PATH'] + '<collection>/user/<id>')
def user(collection, id):
    try:
        col = db[collection]
        user_found = col.find_one(ObjectId(id))
        if user_found:
            if oidc.user_loggedin:
                info = oidc.user_getinfo(['preferred_username', 'email', 'sub'])
                username = info.get('preferred_username')

                return render_template('user.html', tweetArr=json.dumps(user_found["tweets"]), user=user_found,
                                       tweet=json.dumps(user_found["found_tweet"]),
                                       app_url=os.environ['APP_URL'],
                                       app_url_path=os.environ['APP_URL_PATH'][:-1],
                                       collection=collection,
                                       example_db=os.environ['EXAMPLE_DB'], user_name=username)
            else:
                return render_template('user.html', tweetArr=json.dumps(user_found["tweets"]), user=user_found,
                                       tweet=json.dumps(user_found["found_tweet"]),
                                       app_url=os.environ['APP_URL'],
                                       app_url_path=os.environ['APP_URL_PATH'][:-1],
                                       collection=collection,
                                       example_db=os.environ['EXAMPLE_DB'])

        else:
            if oidc.user_loggedin:
                info = oidc.user_getinfo(['preferred_username', 'email', 'sub'])
                username = info.get('preferred_username')

                return render_template('404.html', app_url=os.environ['APP_URL'],
                                       app_url_path=os.environ['APP_URL_PATH'][:-1],
                                       example_db=os.environ['EXAMPLE_DB'], user_name=username)
            else:
                return render_template('404.html', app_url=os.environ['APP_URL'],
                                       app_url_path=os.environ['APP_URL_PATH'][:-1],
                                       example_db=os.environ['EXAMPLE_DB'])

    except Exception as e:
        if oidc.user_loggedin:
            info = oidc.user_getinfo(['preferred_username', 'email', 'sub'])
            username = info.get('preferred_username')

            return render_template('404.html', app_url=os.environ['APP_URL'],
                                   app_url_path=os.environ['APP_URL_PATH'][:-1],
                                   example_db=os.environ['EXAMPLE_DB'], user_name=username)
        else:
            return render_template('404.html', app_url=os.environ['APP_URL'],
                                   app_url_path=os.environ['APP_URL_PATH'][:-1],
                                   example_db=os.environ['EXAMPLE_DB'])


@app.route(os.environ['APP_URL_PATH'] + 'recalculate/<collection>/<id>')
def recalc(collection, id):
    consumer_key = os.environ['CONSUMER_KEY']
    consumer_secret = os.environ['CONSUMER_SECRET']
    access_token = os.environ['ACCESS_TOKEN']
    access_token_secret = os.environ['ACCESS_TOKEN_SECRET']
    bearer = os.environ['BEARER']
    use_bearer = int(os.environ['USE_BEARER'])

    if use_bearer:
        auth = tweepy.OAuth2BearerHandler(bearer)
    else:
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)

    api = tweepy.API(auth, retry_count=3, timeout=100000, wait_on_rate_limit=True)

    col1 = db[collection]

    user = col1.find_one(ObjectId(id))

    col1.update_one({"_id": user["_id"]},
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

        """"""
        col1.update_one({"_id": user["_id"]},
                        {'$pull': {'tweets': {'id': tw["id"]}}}
                        )
        """"""

        col1.update_one({"_id": user["_id"]},
                        {'$addToSet': {'tweets': tw}})

    user = col1.find_one(ObjectId(id))
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
    col1.update_one({"_id": user["_id"]},
                    {'$set': {'signals': new_signals.get_parameters()}})

    return redirect(os.environ['APP_URL'] + "/" + collection + "/user/" + id)


@app.errorhandler(404)
def page_not_found(e):
    if oidc.user_loggedin:
        info = oidc.user_getinfo(['preferred_username', 'email', 'sub'])
        username = info.get('preferred_username')

        return render_template('404.html', app_url=os.environ['APP_URL'],
                               app_url_path=os.environ['APP_URL_PATH'][:-1],
                               example_db=os.environ['EXAMPLE_DB'], user_name=username), 404
    else:
        return render_template('404.html', app_url=os.environ['APP_URL'],
                               app_url_path=os.environ['APP_URL_PATH'][:-1],
                               example_db=os.environ['EXAMPLE_DB']), 404


@app.errorhandler(403)
def error403(e):
    if oidc.user_loggedin:
        info = oidc.user_getinfo(['preferred_username', 'email', 'sub'])
        username = info.get('preferred_username')

        return render_template('403.html', app_url=os.environ['APP_URL'],
                               app_url_path=os.environ['APP_URL_PATH'][:-1],
                               example_db=os.environ['EXAMPLE_DB'], user_name=username), 403
    else:
        return render_template('403.html', app_url=os.environ['APP_URL'],
                               app_url_path=os.environ['APP_URL_PATH'][:-1],
                               example_db=os.environ['EXAMPLE_DB']), 403


"""
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
                        logging.info(location)
                        if location is None:
                            logging.info("try to add loc")
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

                        logging.info("try to add loc")
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
                               app_url=os.environ['APP_URL'],
                               negative_count1=negative_count1, positive_count1=positive_count1,
                               neutral_count1=neutral_count1, negative_count2=negative_count2,
                               positive_count2=positive_count2, neutral_count2=neutral_count2)
    except Exception as e:
        # return dumps({'error': str(e)})
        logging.info(e)



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
        # logging.info("created_at: ", tweet.created_at, ", text: ", tweet.retweeted_status.full_text, ", user: user_id: ",tweet.user.id, ", user_name: ", tweet.user.name, ", followers_count: ", tweet.user.followers_count)
        userObj = {}
        user = api.get_user(screen_name=tweet.user.screen_name)._json
        user.pop('status', None)
        userObj["user"] = user
        userObj["found_tweet"] = tweet._json

        logging.info("sentiment!")
        analyzer = SentimentIntensityAnalyzer()
        tweet_modified = remove_user_mentions(remove_urls(copy.deepcopy(userObj["found_tweet"])))
        sentence = tweet_modified["full_text"]
        sentiment = analyzer.polarity_scores(sentence)
        logging.info(sentence)
        logging.info(sentiment['compound'])
        if sentiment['compound'] >= 0.1:
            logging.info("Positive")
            userObj["found_tweet"]["sentiment"] = "positive"

        elif sentiment['compound'] <= - 0.2:
            logging.info("Negative")
            userObj["found_tweet"]["sentiment"] = "negative"

        else:
            logging.info("Neutral")
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

        logging.info(new_signals.get_parameters())
        userObj["signals"] = new_signals.get_parameters()
        col.insert_one(dict(userObj))

    return "OK!"


@app.route('/delete')
def delete():
    users = col.find()
    for user in users:
        logging.info("check!")
        logging.info(user["_id"])
        if user["signals"]["k"] < 30:
            logging.info("delete!")
            col.delete_one({"_id": user["_id"]})
    return "OK!"


@app.route('/all/recalculate')
def recalculate():
    users = col.find()
    for user in users:
        logging.info("recalculate!")
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
        logging.info("sentiment!")
        analyzer = SentimentIntensityAnalyzer()
        tweet = remove_user_mentions(remove_urls(user["found_tweet"]))
        sentence = tweet["full_text"]
        sentiment = analyzer.polarity_scores(sentence)
        logging.info(sentence)
        logging.info(sentiment['compound'])
        if sentiment['compound'] >= 0.1:
            logging.info("Positive")
            col.update_one({"_id": user["_id"]},
                           {'$set': {'found_tweet.sentiment': "positive"}})

        elif sentiment['compound'] <= - 0.2:
            logging.info("Negative")
            col.update_one({"_id": user["_id"]},
                           {'$set': {'found_tweet.sentiment': "negative"}})

        else:
            logging.info("Neutral")
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

        """"""
        col.update_one({"_id": user["_id"]},
                       {'$pull': {'tweets': {'id': tw["id"]}}}
                       )
        """"""

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
"""

if __name__ == "__main__":
    # app.run()
    app.run(host='0.0.0.0')
