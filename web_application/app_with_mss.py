import copy
import json
import os
import datetime
import urllib
from json import dumps
import logging
import uuid
from pprint import pprint

from json2html import *

from cryptography.fernet import Fernet
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
from pykafka import KafkaClient
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

    encoding = 'utf-8'
    col4 = db["ApplicationStatus"]
    crypto = col4.find_one({"name": "CryptographyKEY"})
    key = crypto["value"].encode(encoding)
    f = Fernet(key)
    decoded_token = (user_id + crypto["time_of_creation"]).encode(encoding)
    token = f.encrypt(decoded_token)
    token = token.decode(encoding)

    col3 = db["API_Credentials"]

    user = col3.find_one({"user_sub": info.get('sub')})

    if user is not None:
        if "credentials" in user:
            access_token_secret = user["credentials"]["access_token_secret"]
            access_token = user["credentials"]["access_token"]
            api_key_secret = user["credentials"]["api_key_secret"]
            api_key = user["credentials"]["api_key"]
            if "tried_to_use" in user:
                tried_to_use = user["tried_to_use"]
                in_use = user["in_use"]
            else:
                tried_to_use = False
                in_use = False
            if "exception" in user:
                exception = user["exception"]
            else:
                exception = None

            table = None

            if "in_use" in user:
                if user["in_use"]:
                    auth = tweepy.OAuthHandler(api_key, api_key_secret)
                    auth.set_access_token(access_token, access_token_secret)

                    api = tweepy.API(auth, retry_count=3, timeout=100000, wait_on_rate_limit=True)

                    data = api.rate_limit_status()

                    # print(data["resources"])

                    for attr in list(data["resources"].keys()):
                        if attr != "users" and attr != "statuses" and attr != "search":
                            del data["resources"][attr]
                        else:
                            for attr1 in list(data["resources"][attr].keys()):
                                if attr1 != "/users/:id" and attr1 != "/statuses/user_timeline" and attr1 != "/search/tweets":
                                    del data["resources"][attr][attr1]

                    for attr in data["resources"].keys():
                        for attr1 in data["resources"][attr].keys():
                            data["resources"][attr][attr1]["reset"] = datetime.datetime.fromtimestamp(
                                data["resources"][attr][attr1]["reset"]).strftime("%I:%M:%S %B %d, %Y ")

                    table = Markup(json2html.convert(json=data["resources"],
                                                     table_attributes="id=\"rate-limit-status-table\" class=\"table table-bordered table-hover\""))

            return render_template("profile.html", app_url=os.environ['APP_URL'],
                                   app_url_path=os.environ['APP_URL_PATH'][:-1],
                                   example_db=os.environ['EXAMPLE_DB'], name=username, email=email, user_id=user_id,
                                   user_name=username, access_token_secret=access_token_secret,
                                   access_token=access_token,
                                   api_key_secret=api_key_secret, api_key=api_key, in_use=in_use,
                                   tried_to_use=tried_to_use,
                                   exception=exception, table=table, token=token)

    return render_template("profile.html", app_url=os.environ['APP_URL'],
                           app_url_path=os.environ['APP_URL_PATH'][:-1],
                           example_db=os.environ['EXAMPLE_DB'], name=username, email=email, user_id=user_id,
                           user_name=username, token=token)


@app.route(os.environ['APP_URL_PATH'] + 'profile/update/credentials', methods=['GET'])
@oidc.require_login
def profile_credentials():
    info = oidc.user_getinfo(['sub'])
    user_id = info.get('sub')

    access_token_secret = request.args.get("access_token_secret")
    access_token = request.args.get("access_token")
    api_key_secret = request.args.get("api_key_secret")
    api_key = request.args.get("api_key")

    col3 = db["API_Credentials"]

    col3.update_one({"user_sub": str(user_id)}, {'$set': {'credentials.access_token_secret': access_token_secret,
                                                          'credentials.access_token': access_token,
                                                          'credentials.api_key_secret': api_key_secret,
                                                          'credentials.api_key': api_key,
                                                          }}, upsert=True)
    col3.update_one({"user_sub": str(user_id)}, {'$set': {'tried_to_use': False}})
    col3.update_one({"user_sub": str(user_id)}, {'$set': {'in_use': False}})

    return redirect((os.environ['APP_URL']) + "/profile")


@app.route(os.environ['APP_URL_PATH'] + 'profile/use/credentials', methods=['GET'])
@oidc.require_login
def profile_use_credentials():
    info = oidc.user_getinfo(['sub'])
    user_id = info.get('sub')

    col3 = db["API_Credentials"]

    user = col3.find_one({"user_sub": info.get('sub')})

    if user is not None:
        if "credentials" in user:
            access_token_secret = user["credentials"]["access_token_secret"]
            access_token = user["credentials"]["access_token"]
            api_key_secret = user["credentials"]["api_key_secret"]
            api_key = user["credentials"]["api_key"]
        else:
            return "Not Found", 404
    else:
        return "Not Found", 404

    # authorization of consumer key and consumer secret
    auth = tweepy.OAuthHandler(api_key, api_key_secret)

    # set access to user's access key and access secret
    auth.set_access_token(access_token, access_token_secret)

    # calling the api
    api = tweepy.API(auth)
    try:
        if api.verify_credentials() == False:
            print("The user credentials are invalid.")
            col3.update_one({"user_sub": str(user_id)}, {'$set': {'tried_to_use': True}})
            col3.update_one({"user_sub": str(user_id)}, {'$set': {'in_use': False}})
        else:
            print("The user credentials are valid.")
            col3.update_one({"user_sub": str(user_id)}, {'$set': {'tried_to_use': True}})
            col3.update_one({"user_sub": str(user_id)}, {'$set': {'in_use': True}})
            col3.update_one({"user_sub": str(user_id)}, {'$set': {'exception': None}})
    except Exception as e:
        print(e)
        print("The user credentials are invalid.")
        col3.update_one({"user_sub": str(user_id)}, {'$set': {'tried_to_use': True}})
        col3.update_one({"user_sub": str(user_id)}, {'$set': {'exception': str(e)}})
        col3.update_one({"user_sub": str(user_id)}, {'$set': {'in_use': False}})

    return redirect((os.environ['APP_URL']) + "/profile")


@app.route(os.environ['APP_URL_PATH'] + 'profile/do-not-use/credentials', methods=['GET'])
@oidc.require_login
def profile_do_not_use_credentials():
    info = oidc.user_getinfo(['sub'])
    user_id = info.get('sub')

    col3 = db["API_Credentials"]

    col3.update_one({"user_sub": str(user_id)}, {'$set': {'tried_to_use': False}})
    col3.update_one({"user_sub": str(user_id)}, {'$set': {'in_use': False}})

    return redirect((os.environ['APP_URL']) + "/profile")


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


@app.route(os.environ['APP_URL_PATH'] + "/rate-limit-status-all")
def rate_limit_status_all():
    consumer_key = os.environ['CONSUMER_KEY']
    consumer_secret = os.environ['CONSUMER_SECRET']
    access_token = os.environ['ACCESS_TOKEN']
    access_token_secret = os.environ['ACCESS_TOKEN_SECRET']
    bearer = os.environ['BEARER']
    use_bearer = int(os.environ['USE_BEARER'])

    if bearer is not None and use_bearer:
        auth = tweepy.OAuth2BearerHandler(bearer)
    else:
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)

    api = tweepy.API(auth, retry_count=3, timeout=100000, wait_on_rate_limit=True)

    data = api.rate_limit_status()

    for attr, value in data["resources"].items():
        for attr1, value1 in data["resources"][attr].items():
            data["resources"][attr][attr1]["reset"] = datetime.datetime.fromtimestamp(
                data["resources"][attr][attr1]["reset"]).strftime("%I:%M:%S %B %d, %Y ")

    table = Markup(json2html.convert(json=data["resources"],
                                     table_attributes="id=\"rate-limit-status-table\" class=\"table table-bordered table-hover\""))

    if oidc.user_loggedin:
        info = oidc.user_getinfo(['preferred_username', 'email', 'sub'])

        username = info.get('preferred_username')
        return render_template("rate_limit_status.html", app_url=os.environ['APP_URL'],
                               app_url_path=os.environ['APP_URL_PATH'][:-1],
                               example_db=os.environ['EXAMPLE_DB'], user_name=username,
                               table=table, show_only_part=False)
    else:
        return render_template("rate_limit_status.html", app_url=os.environ['APP_URL'],
                               app_url_path=os.environ['APP_URL_PATH'][:-1],
                               example_db=os.environ['EXAMPLE_DB'],
                               table=table, show_only_part=False)


@app.route(os.environ['APP_URL_PATH'] + "/rate-limit-status")
def rate_limit_status():
    consumer_key = os.environ['CONSUMER_KEY']
    consumer_secret = os.environ['CONSUMER_SECRET']
    access_token = os.environ['ACCESS_TOKEN']
    access_token_secret = os.environ['ACCESS_TOKEN_SECRET']
    bearer = os.environ['BEARER']
    use_bearer = int(os.environ['USE_BEARER'])

    if bearer is not None and use_bearer:
        auth = tweepy.OAuth2BearerHandler(bearer)
    else:
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)

    api = tweepy.API(auth, retry_count=3, timeout=100000, wait_on_rate_limit=True)

    data = api.rate_limit_status()

    # print(data["resources"])

    for attr in list(data["resources"].keys()):
        if attr != "users" and attr != "statuses" and attr != "search":
            del data["resources"][attr]
        else:
            for attr1 in list(data["resources"][attr].keys()):
                if attr1 != "/users/:id" and attr1 != "/statuses/user_timeline" and attr1 != "/search/tweets":
                    del data["resources"][attr][attr1]

    for attr in data["resources"].keys():
        for attr1 in data["resources"][attr].keys():
            data["resources"][attr][attr1]["reset"] = datetime.datetime.fromtimestamp(
                data["resources"][attr][attr1]["reset"]).strftime("%I:%M:%S %B %d, %Y ")

    table = Markup(json2html.convert(json=data["resources"],
                                     table_attributes="id=\"rate-limit-status-table\" class=\"table table-bordered table-hover\""))

    if oidc.user_loggedin:
        info = oidc.user_getinfo(['preferred_username', 'email', 'sub'])

        username = info.get('preferred_username')
        return render_template("rate_limit_status.html", app_url=os.environ['APP_URL'],
                               app_url_path=os.environ['APP_URL_PATH'][:-1],
                               example_db=os.environ['EXAMPLE_DB'], user_name=username,
                               table=table, show_only_part=True)
    else:
        return render_template("rate_limit_status.html", app_url=os.environ['APP_URL'],
                               app_url_path=os.environ['APP_URL_PATH'][:-1],
                               example_db=os.environ['EXAMPLE_DB'],
                               table=table, show_only_part=True)


@app.route(os.environ['APP_URL_PATH'] + "/admin-page")
@oidc.require_login
def admin_page():
    col1 = db["ApplicationStatus"]
    main_parameters = col1.find_one({"name": "MainValues"})
    info = oidc.user_getinfo(['preferred_username', 'email', 'sub'])

    if not info["sub"] in main_parameters["admins"]:
        return error403("403")

    username = info.get('preferred_username')

    consumer_key = os.environ['CONSUMER_KEY']
    consumer_secret = os.environ['CONSUMER_SECRET']
    access_token = os.environ['ACCESS_TOKEN']
    access_token_secret = os.environ['ACCESS_TOKEN_SECRET']
    bearer = os.environ['BEARER']
    use_bearer = int(os.environ['USE_BEARER'])

    if bearer is not None and use_bearer:
        auth = tweepy.OAuth2BearerHandler(bearer)
    else:
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)

    api = tweepy.API(auth, retry_count=3, timeout=100000, wait_on_rate_limit=True)

    data = api.rate_limit_status()

    # print(data["resources"])

    for attr in list(data["resources"].keys()):
        if attr != "users" and attr != "statuses" and attr != "search":
            del data["resources"][attr]
        else:
            for attr1 in list(data["resources"][attr].keys()):
                if attr1 != "/users/:id" and attr1 != "/statuses/user_timeline" and attr1 != "/search/tweets":
                    del data["resources"][attr][attr1]

    for attr in data["resources"].keys():
        for attr1 in data["resources"][attr].keys():
            data["resources"][attr][attr1]["reset"] = datetime.datetime.fromtimestamp(
                data["resources"][attr][attr1]["reset"]).strftime("%I:%M:%S %B %d, %Y ")

    table_twitter_api_rate_limits = Markup(json2html.convert(json=data["resources"],
                                                             table_attributes="id=\"rate-limit-status-table\" class=\"table table-bordered table-hover\""))

    del main_parameters["_id"]
    del main_parameters["name"]

    table_main_parameters = Markup(json2html.convert(json=main_parameters,
                                                     table_attributes="id=\"main-parameters-table\" class=\"table table-bordered table-hover\""))

    dca_coefficients = col1.find_one(
        {"name": "DCACoefficients", "version": main_parameters["coefficients_collection_id"]})
    del dca_coefficients["_id"]
    del dca_coefficients["name"]

    table_dca_coefficients = Markup(json2html.convert(json=dca_coefficients,
                                                      table_attributes="id=\"dca-coefficients-table\" class=\"table table-bordered table-hover\""))

    env_vars = os.environ.copy()
    for attr in list(env_vars.keys()):
        if not ("PAMP_" in attr or "DS_" in attr or "SS_" in attr) or "ACCESS" in attr:
            del env_vars[attr]

    table_env_vars = Markup(json2html.convert(json=env_vars,
                                              table_attributes="id=\"dca-coefficients-table\" class=\"table table-bordered table-hover\""))

    col2 = db["Requests"]
    r = list(col2.find())
    for req in r:
        req["_id"] = str(req["_id"].generation_time).replace("+00:00", "")

    return render_template("admin_page.html", app_url=os.environ['APP_URL'],
                           app_url_path=os.environ['APP_URL_PATH'][:-1],
                           example_db=os.environ['EXAMPLE_DB'], user_name=username,
                           table_twitter_api_rate_limits=table_twitter_api_rate_limits,
                           table_main_parameters=table_main_parameters,
                           table_dca_coefficients=table_dca_coefficients,
                           table_env_vars=table_env_vars, requests=r)


@app.route(os.environ['APP_URL_PATH'] + "/admin-page/use-new-env-vars")
@oidc.require_login
def admin_page_set_new_env_vars():
    col1 = db["ApplicationStatus"]
    main_parameters = col1.find_one({"name": "MainValues"})
    info = oidc.user_getinfo(['preferred_username', 'email', 'sub'])

    if not info["sub"] in main_parameters["admins"]:
        return error403("403")

    dca_coefficients = col1.find_one(
        {"name": "DCACoefficients", "version": main_parameters["coefficients_collection_id"]})

    for attr in list(dca_coefficients["coefficients"].keys()):
        os.environ[attr] = str(dca_coefficients["coefficients"][attr])

    return "Ok, DCACoefficients version " + main_parameters["coefficients_collection_id"]


@app.route(os.environ['APP_URL_PATH'] + "/admin-page/use-new-env-vars/signal-generator")
@oidc.require_login
def sg_set_new_env_vars():
    col1 = db["ApplicationStatus"]
    main_parameters = col1.find_one({"name": "MainValues"})
    info = oidc.user_getinfo(['preferred_username', 'email', 'sub'])

    if not info["sub"] in main_parameters["admins"]:
        return error403("403")

    sg_data = {
        "coefficients_collection_id": main_parameters["coefficients_collection_id"]
    }

    ms_sg_addr = os.environ['MS_SG_ADDRESS']
    sg_result = requests.post((ms_sg_addr + os.environ['MS_SG_URL_PATH'] + "use-new-env-vars"), data=sg_data)

    return "OK" + sg_result.text


@app.route(os.environ['APP_URL_PATH'] + "/admin-page/use-new-env-vars/bot-detector")
@oidc.require_login
def bd_set_new_env_vars():
    col1 = db["ApplicationStatus"]
    main_parameters = col1.find_one({"name": "MainValues"})
    info = oidc.user_getinfo(['preferred_username', 'email', 'sub'])

    if not info["sub"] in main_parameters["admins"]:
        return error403("403")

    bd_data = {
        "coefficients_collection_id": main_parameters["coefficients_collection_id"]
    }

    ms_bd_addr = os.environ['MS_BD_ADDRESS']
    bd_result = requests.post((ms_bd_addr + os.environ['MS_BD_URL_PATH'] + "use-new-env-vars"), data=bd_data)

    return "OK" + bd_result.text


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

    token = request.args.get('token')

    is_loggedin = False

    try:

        if token is not None:
            encoding = 'utf-8'
            col1 = db["ApplicationStatus"]
            crypto = col1.find_one({"name": "CryptographyKEY"})
            key = crypto["value"].encode(encoding)
            # key = Fernet.generate_key()
            f = Fernet(key)
            token_decrypted = f.decrypt(token.encode(encoding)).decode(encoding)
            print(token_decrypted)

            if len(token_decrypted) > 10:
                if token_decrypted[-10:] == crypto["time_of_creation"]:
                    is_loggedin = True

    except Exception as e:
        return "Bad Request", 400

    if parameters is not None:
        if "owner" in parameters:
            if parameters["owner"] is not None:
                if not is_loggedin:
                    return 403

                sub = token_decrypted[:len(token_decrypted) - 10]

                col5 = db["ApplicationStatus"]
                main_parameters = col5.find_one({"name": "MainValues"})

                if not sub in main_parameters["admins"]:

                    if not ((sub in parameters["owner"]) or (
                            sub in parameters["read_permission"]) or (
                                    sub in parameters["write_permission"])):
                        return 403

    else:
        return "Not Found", 404

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
        return "Not Found", 404


@app.route(os.environ['APP_URL_PATH'] + "api/create-request", methods=['post', 'get'])
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
        token = request.args.get('token')

        is_loggedin = False

        try:

            if token is not None:
                encoding = 'utf-8'
                col1 = db["ApplicationStatus"]
                crypto = col1.find_one({"name": "CryptographyKEY"})
                key = crypto["value"].encode(encoding)
                # key = Fernet.generate_key()
                f = Fernet(key)
                token_decrypted = f.decrypt(token.encode(encoding)).decode(encoding)
                print(token_decrypted)

                if len(token_decrypted) > 10:
                    if token_decrypted[-10:] == crypto["time_of_creation"]:
                        is_loggedin = True

        except Exception as e:
            return "Bad Request", 400

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

        if is_loggedin:

            sub = token_decrypted[:len(token_decrypted) - 10]

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
                "owner": [sub],
                "read_permission": [],
                "write_permission": [],
            }

            col3 = db["Permissions"]
            col3.update_one({'user_id': sub}, {"$push": {"owner": str(id)}}, upsert=True)


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

        if is_loggedin:
            sub = token_decrypted[:len(token_decrypted) - 10]
            col3 = db["API_Credentials"]
            current_user = col3.find_one({"user_sub": sub})

            if current_user is not None:
                if "in_use" in current_user:
                    if current_user["in_use"]:
                        access_token_secret = current_user["credentials"]["access_token_secret"]
                        access_token = current_user["credentials"]["access_token"]
                        consumer_secret = current_user["credentials"]["api_key_secret"]
                        consumer_key = current_user["credentials"]["api_key"]
                        bearer = None

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
        return "Bad Request", 400


@app.route(os.environ['APP_URL_PATH'] + 'api/user-check/<screen_name>')
def api_user_check(screen_name):
    screen_name = screen_name.replace("@", "")

    consumer_key = os.environ['CONSUMER_KEY']
    consumer_secret = os.environ['CONSUMER_SECRET']
    access_token = os.environ['ACCESS_TOKEN']
    access_token_secret = os.environ['ACCESS_TOKEN_SECRET']
    bearer = os.environ['BEARER']

    use_bearer = int(os.environ['USE_BEARER'])
    if bearer is None:
        use_bearer = False

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
        return "Not Found", 404


@app.route(os.environ['APP_URL_PATH'] + 'api/<collection>/user/<id>')
def api_user(collection, id):
    try:
        col = db[collection]
        user_found = col.find_one(ObjectId(id))
        if user_found:
            return json_util.dumps(user_found)
        else:
            return "Not Found", 404
    except Exception as e:
        return "Not Found", 404


###############################################################################
# ==========================      API END       ================================
###############################################################################


@app.route(os.environ['APP_URL_PATH'] + 'result/<id>')
def resultid(id):
    isPublic = False
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

                if isinstance(parameters["owner"], dict):
                    col2.update_one({"collection": str(id)}, {'$set': {'owner': [parameters["owner"]["sub"]]}})
                    parameters = col2.find_one({"collection": str(id)})

                col5 = db["ApplicationStatus"]
                main_parameters = col5.find_one({"name": "MainValues"})

                if not info["sub"] in main_parameters["admins"]:

                    if not ((info.get('sub') in parameters["owner"]) or (
                            info.get('sub') in parameters["read_permission"]) or (
                                    info.get('sub') in parameters["write_permission"])):
                        return error403("403")

                if not ((info.get('sub') in parameters["owner"]) or (
                        info.get('sub') in parameters["write_permission"])) and (
                        info.get('sub') in parameters["read_permission"]):
                    isPublic = True
            else:
                isPublic = True

        else:
            isPublic = True

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
        data_time = str(parameters["_id"].generation_time).replace("+00:00", "")

        if oidc.user_loggedin:
            info = oidc.user_getinfo(['preferred_username', 'email', 'sub'])

            username = info.get('preferred_username')

            col5 = db[str(id)]
            users2 = list(col5.find({}))

            for user2 in users2:

                # print("user2 before")
                # print(user2)

                user2.pop('classification_result_botness', None)
                user2.pop('classification_result_bad_intentions', None)

                if 'classification_result_botness_agreed' in user2:

                    if info["sub"] in user2["classification_result_botness_agreed"]:
                        user2["classification_result_botness"] = "agree"

                    user2["classification_result_botness_agreed_count"] = len(
                        user2["classification_result_botness_agreed"])
                else:
                    user2["classification_result_botness_agreed_count"] = 0

                if "classification_result_botness_disagreed" in user2:
                    if info["sub"] in user2["classification_result_botness_disagreed"]:
                        user2["classification_result_botness"] = "disagree"

                    user2["classification_result_botness_disagreed_count"] = len(
                        user2["classification_result_botness_disagreed"])
                else:
                    user2["classification_result_botness_disagreed_count"] = 0

                if "classification_result_bad_intentions_agreed" in user2:

                    if info["sub"] in user2["classification_result_bad_intentions_agreed"]:
                        user2["classification_result_bad_intentions"] = "agree"

                    user2["classification_result_bad_intentions_agreed_count"] = len(
                        user2["classification_result_bad_intentions_agreed"])
                else:
                    user2["classification_result_bad_intentions_agreed_count"] = 0

                if "classification_result_bad_intentions_disagreed" in user2:

                    if info["sub"] in user2["classification_result_bad_intentions_disagreed"]:
                        user2["classification_result_bad_intentions"] = "disagree"

                    user2["classification_result_bad_intentions_disagreed_count"] = len(
                        user2["classification_result_bad_intentions_disagreed"])

                else:
                    user2["classification_result_bad_intentions_disagreed_count"] = 0

                # print("user2 after")
                # print(user2)

            col4 = db["SavedFavoriteRequests"]
            string_of_parameters = parameters["keywords"].replace("#", "") + \
                                   parameters["areaParameters1"] + \
                                   parameters["areaParameters2"] + parameters[
                                       "areaParameters3"] + \
                                   parameters["SearchParameters1"] + parameters["start_date"] + \
                                   parameters["end_date"]

            saved_by_user = col4.find_one({'user_id': info.get('sub'),
                                           "requests.string_of_parameters": string_of_parameters})

            if saved_by_user is not None:
                already_saved = True
            else:
                already_saved = False

            return render_template('result.html', users=users2, folium_map=Markup(folium_map._repr_html_()),
                                   app_url=os.environ['APP_URL'],
                                   negative_count1=negative_count1, positive_count1=positive_count1,
                                   neutral_count1=neutral_count1, negative_count2=negative_count2,
                                   positive_count2=positive_count2, neutral_count2=neutral_count2,
                                   collection=str(id), parameters=parameters, ready_count=ready_count,
                                   app_url_path=os.environ['APP_URL_PATH'][:-1],
                                   example_db=os.environ['EXAMPLE_DB'], user_name=username, isPublic=isPublic,
                                   already_saved=already_saved, data_time=data_time)
        else:
            return render_template('result.html', users=col1.find(), folium_map=Markup(folium_map._repr_html_()),
                                   app_url=os.environ['APP_URL'],
                                   negative_count1=negative_count1, positive_count1=positive_count1,
                                   neutral_count1=neutral_count1, negative_count2=negative_count2,
                                   positive_count2=positive_count2, neutral_count2=neutral_count2,
                                   collection=str(id), parameters=parameters, ready_count=ready_count,
                                   app_url_path=os.environ['APP_URL_PATH'][:-1],
                                   example_db=os.environ['EXAMPLE_DB'], isPublic=isPublic, data_time=data_time)

    except Exception as e:
        # return dumps({'error': str(e)})
        logging.info(e)


@app.route(os.environ['APP_URL_PATH'] + 'result/<id1>/delete/<id2>')
@oidc.require_login
def delete_user_from_result(id1, id2):
    info = oidc.user_getinfo(['preferred_username', 'email', 'sub'])
    col2 = db["Requests"]
    parameters = col2.find_one({"collection": str(id1)})

    if parameters is not None:
        if "owner" in parameters:
            if parameters["owner"] is not None:
                if not (info.get('sub') in parameters["owner"]):
                    if "write_permission" in parameters:
                        if parameters["write_permission"] is not None:
                            if not (info.get('sub') in parameters["write_permission"]):
                                return error403("403")
                        else:
                            return error403("403")
                    else:
                        return error403("403")

            else:
                return error403("403")
        else:
            return error403("403")

    else:
        return page_not_found("404")

    db[str(id1)].delete_one({"_id": ObjectId(str(id2))})

    return redirect((os.environ['APP_URL']) + "/result/" + id1)


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
    r1 = []
    r2 = []
    col2 = db["Requests"]
    if user is not None:
        if "owner" in user:
            for collection in user["owner"]:
                req = col2.find_one({"collection": collection})
                if req is not None:
                    r.append(req)

        for req in r:
            req["_id"] = str(req["_id"].generation_time).replace("+00:00", "")

        if "read_permission" in user:
            for collection in user["read_permission"]:
                req = col2.find_one({"collection": collection})
                if req is not None:
                    r1.append(req)

        for req in r1:
            req["_id"] = str(req["_id"].generation_time).replace("+00:00", "")

        if "write_permission" in user:
            for collection in user["write_permission"]:
                req = col2.find_one({"collection": collection})
                if req is not None:
                    r2.append(req)

        for req in r2:
            req["_id"] = str(req["_id"].generation_time).replace("+00:00", "")

    return render_template('history.html', requests_owner=r, requests_read=r1, requests_write=r2,
                           app_url=os.environ['APP_URL'],
                           app_url_path=os.environ['APP_URL_PATH'][:-1],
                           example_db=os.environ['EXAMPLE_DB'], user_name=username, user_history=True)


@app.route(os.environ['APP_URL_PATH'] + 'saved-request-dashboard/<hash>')
@oidc.require_login
def saved_request_dashboard(hash):
    info = oidc.user_getinfo(['preferred_username', 'email', 'sub'])
    username = info.get('preferred_username')
    col1 = db["SavedFavoriteRequests"]
    user = col1.find_one({"user_id": info.get('sub')})

    r = []

    col2 = db["Requests"]
    if user is not None:
        if "requests" in user:
            for request1 in user["requests"]:
                if request1["string_of_parameters"] == hash:
                    for collection in request1["collection"]:
                        req = col2.find_one({"collection": collection})
                        if req is not None:
                            r.append(req)
                    break

        for req in r:
            req["_id"] = str(req["_id"].generation_time).replace("+00:00", "")

    return render_template('saved_request_history.html', requests_owner=r,
                           app_url=os.environ['APP_URL'],
                           app_url_path=os.environ['APP_URL_PATH'][:-1],
                           example_db=os.environ['EXAMPLE_DB'], user_name=username, user_history=True)


@app.route(os.environ['APP_URL_PATH'] + 'favourite-requests')
@oidc.require_login
def favourite_requests():
    info = oidc.user_getinfo(['preferred_username', 'email', 'sub'])
    username = info.get('preferred_username')
    col1 = db["SavedFavoriteRequests"]
    user = col1.find_one({"user_id": info.get('sub')})

    r = []
    if user is not None:
        if "requests" in user:
            r = user["requests"]

    return render_template('saved_favourite_requests.html', saved_requests=r,
                           app_url=os.environ['APP_URL'],
                           app_url_path=os.environ['APP_URL_PATH'][:-1],
                           example_db=os.environ['EXAMPLE_DB'], user_name=username)


@app.route(os.environ['APP_URL_PATH'] + 'result/favourite-requests/add/<collection>')
@oidc.require_login
def favourite_requests_add_request(collection):
    info = oidc.user_getinfo(['preferred_username', 'email', 'sub'])

    col2 = db["Requests"]
    parameters = col2.find_one({"collection": str(collection)})
    parameters["string_of_parameters"] = parameters["keywords"].replace("#", "") + \
                                         parameters["areaParameters1"] + \
                                         parameters["areaParameters2"] + parameters["areaParameters3"] + \
                                         parameters["SearchParameters1"] + parameters["start_date"] + \
                                         parameters["end_date"]

    col4 = db["SavedFavoriteRequests"]
    saved_parameters = parameters.copy()
    saved_parameters["collection"] = [collection]
    saved_parameters.pop("owner", None)
    saved_parameters.pop("read_permission", None)
    saved_parameters.pop("write_permission", None)

    saved_by_user = col4.find_one({'user_id': info.get('sub'),
                                   "requests.string_of_parameters": saved_parameters[
                                       "string_of_parameters"]})

    if saved_by_user is not None:
        col4.update_one({'user_id': info.get('sub'),
                         "requests.string_of_parameters": saved_parameters["string_of_parameters"]},
                        {"$addToSet": {'requests.$.collection': str(id)}})
    else:
        col4.update_one({'user_id': info.get('sub')}, {"$addToSet": {"requests": saved_parameters}},
                        upsert=True)

    return redirect((os.environ['APP_URL']) + "/result/" + collection)


@app.route(os.environ['APP_URL_PATH'] + 'saved_favourite_requests/delete/<collection>')
@oidc.require_login
def favourite_requests_delete_request(collection):
    info = oidc.user_getinfo(['preferred_username', 'email', 'sub'])

    col1 = db["SavedFavoriteRequests"]
    col1.update_one({"user_id": info.get('sub'), }, {'$pull': {'requests': {"collection": collection}}})

    return redirect((os.environ['APP_URL']) + "/favourite-requests")


@app.route(os.environ['APP_URL_PATH'] + 'dashboard/delete/owner/<id>')
@oidc.require_login
def dashboard_delete_request_owner(id):
    info = oidc.user_getinfo(['preferred_username', 'email', 'sub'])

    col2 = db["Requests"]
    parameters = col2.find_one({"collection": str(id)})

    if parameters is not None:
        if "owner" in parameters:
            if parameters["owner"] is not None:
                if not (info.get('sub') in parameters["owner"]):
                    return error403("403")
            else:
                return error403("403")
        else:
            return error403("403")

    else:
        return page_not_found("404")

    if len(parameters["owner"]) == 1:
        col2.delete_one({"collection": str(id)})
        db[str(id)].drop()
    else:
        col2.update_one({"collection": str(id)}, {'$pullAll': {'owner': [info.get('sub')]}})

    col1 = db["Permissions"]

    col1.update_one({"user_id": info.get('sub')}, {'$pullAll': {'owner': [id]}})

    return redirect((os.environ['APP_URL']) + "/dashboard")


@app.route(os.environ['APP_URL_PATH'] + 'dashboard/delete/read_permission/<id>')
@oidc.require_login
def dashboard_delete_request_read_permission(id):
    info = oidc.user_getinfo(['preferred_username', 'email', 'sub'])

    col2 = db["Requests"]
    col1 = db["Permissions"]

    col1.update_one({"user_id": info.get('sub')}, {'$pullAll': {'read_permission': [str(id)]}})

    col2.update_one({"collection": str(id)}, {'$pullAll': {'read_permission': [str(info.get('sub'))]}})

    return redirect((os.environ['APP_URL']) + "/dashboard")


@app.route(os.environ['APP_URL_PATH'] + 'dashboard/delete/write_permission/<id>')
@oidc.require_login
def dashboard_delete_request_write_permission(id):
    info = oidc.user_getinfo(['preferred_username', 'email', 'sub'])

    col2 = db["Requests"]
    col1 = db["Permissions"]

    col1.update_one({"user_id": info.get('sub')}, {'$pullAll': {'write_permission': [str(id)]}})

    col2.update_one({"collection": str(id)}, {'$pullAll': {'write_permission': [str(info.get('sub'))]}})

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

    if isinstance(req["owner"], dict):
        col2.update_one({"collection": str(id)}, {'$set': {'owner': [req["owner"]["sub"]]}})
        req = col2.find_one({"collection": str(id)})

    if not (info.get('sub') in req["owner"]):
        return error403("403")

    req["_id"] = str(req["_id"].generation_time).replace("+00:00", "")

    return render_template('access.html', collection_id=id,
                           app_url=os.environ['APP_URL'],
                           app_url_path=os.environ['APP_URL_PATH'][:-1],
                           example_db=os.environ['EXAMPLE_DB'], user_name=username, user_sub=info.get('sub'),
                           owner=req["owner"],
                           read_permission=req["read_permission"], write_permission=req["write_permission"])


@app.route(os.environ['APP_URL_PATH'] + 'access/add/owner/<id1>/<id2>')
@oidc.require_login
def add_access_owner(id1, id2):
    info = oidc.user_getinfo(['preferred_username', 'email', 'sub'])
    username = info.get('preferred_username')

    col2 = db["Requests"]
    req = col2.find_one({"collection": str(id1)})

    if not (info.get('sub') in req["owner"]):
        return error403("403")

    col1 = db["Permissions"]

    col1.update_one({"user_id": str(id2)}, {'$addToSet': {'owner': str(id1)}})
    col2.update_one({"collection": str(id1)}, {'$addToSet': {'owner': str(id2)}})

    req = col2.find_one({"collection": str(id1)})
    req["_id"] = str(req["_id"].generation_time).replace("+00:00", "")

    return redirect((os.environ['APP_URL']) + "/access/" + id1)


@app.route(os.environ['APP_URL_PATH'] + 'access/delete/owner/<id1>/<id2>')
@oidc.require_login
def delete_access_owner(id1, id2):
    info = oidc.user_getinfo(['preferred_username', 'email', 'sub'])
    username = info.get('preferred_username')

    col2 = db["Requests"]
    req = col2.find_one({"collection": str(id1)})

    if not (info.get('sub') in req["owner"]):
        return error403("403")

    if (str(info.get('sub')) != str(id2)):
        return error403("403")

    col1 = db["Permissions"]

    col1.update_one({"user_id": info.get('sub')}, {'$pullAll': {'owner': [str(id1)]}})

    col2.update_one({"collection": str(id1)}, {'$pullAll': {'owner': [str(id2)]}})

    req = col2.find_one({"collection": str(id1)})
    req["_id"] = str(req["_id"].generation_time).replace("+00:00", "")

    return redirect((os.environ['APP_URL']) + "/dashboard")


@app.route(os.environ['APP_URL_PATH'] + 'access/add/read_permission/<id1>/<id2>')
@oidc.require_login
def add_access_read_permission(id1, id2):
    info = oidc.user_getinfo(['preferred_username', 'email', 'sub'])
    username = info.get('preferred_username')

    col2 = db["Requests"]
    req = col2.find_one({"collection": str(id1)})

    if not (info.get('sub') in req["owner"]):
        return error403("403")

    col1 = db["Permissions"]

    col1.update_one({"user_id": str(id2)}, {'$addToSet': {'read_permission': str(id1)}})
    col2.update_one({"collection": str(id1)}, {'$addToSet': {'read_permission': str(id2)}})

    req = col2.find_one({"collection": str(id1)})
    req["_id"] = str(req["_id"].generation_time).replace("+00:00", "")

    return redirect((os.environ['APP_URL']) + "/access/" + id1)


@app.route(os.environ['APP_URL_PATH'] + 'access/delete/read_permission/<id1>/<id2>')
@oidc.require_login
def delete_access_read_permission(id1, id2):
    info = oidc.user_getinfo(['preferred_username', 'email', 'sub'])
    username = info.get('preferred_username')

    col2 = db["Requests"]
    req = col2.find_one({"collection": str(id1)})

    if not (info.get('sub') in req["owner"]):
        if (str(info.get('sub')) != str(id2)):
            return error403("403")

    col1 = db["Permissions"]

    col1.update_one({"user_id": info.get('sub')}, {'$pullAll': {'read_permission': [str(id1)]}})

    col2.update_one({"collection": str(id1)}, {'$pullAll': {'read_permission': [str(id2)]}})

    req = col2.find_one({"collection": str(id1)})
    req["_id"] = str(req["_id"].generation_time).replace("+00:00", "")

    return redirect((os.environ['APP_URL']) + "/access/" + id1)


@app.route(os.environ['APP_URL_PATH'] + 'access/add/write_permission/<id1>/<id2>')
@oidc.require_login
def add_access_write_permission(id1, id2):
    info = oidc.user_getinfo(['preferred_username', 'email', 'sub'])
    username = info.get('preferred_username')

    col2 = db["Requests"]
    req = col2.find_one({"collection": str(id1)})

    if not (info.get('sub') in req["owner"]):
        return error403("403")

    col1 = db["Permissions"]

    col1.update_one({"user_id": str(id2)}, {'$addToSet': {'write_permission': str(id1)}})
    col2.update_one({"collection": str(id1)}, {'$addToSet': {'write_permission': str(id2)}})

    req = col2.find_one({"collection": str(id1)})
    req["_id"] = str(req["_id"].generation_time).replace("+00:00", "")

    return redirect((os.environ['APP_URL']) + "/access/" + id1)


@app.route(os.environ['APP_URL_PATH'] + 'access/delete/write_permission/<id1>/<id2>')
@oidc.require_login
def delete_access_write_permission(id1, id2):
    info = oidc.user_getinfo(['preferred_username', 'email', 'sub'])
    username = info.get('preferred_username')

    col2 = db["Requests"]
    req = col2.find_one({"collection": str(id1)})

    if not (info.get('sub') in req["owner"]):
        if (str(info.get('sub')) != str(id2)):
            return error403("403")

    col1 = db["Permissions"]

    col1.update_one({"user_id": info.get('sub')}, {'$pullAll': {'write_permission': [str(id1)]}})

    col2.update_one({"collection": str(id1)}, {'$pullAll': {'write_permission': [str(id2)]}})

    req = col2.find_one({"collection": str(id1)})
    req["_id"] = str(req["_id"].generation_time).replace("+00:00", "")

    return redirect((os.environ['APP_URL']) + "/access/" + id1)


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
    if "preset_values" in request.args:
        preset_values = request.args["preset_values"]
        col2 = db["Requests"]
        parameters = col2.find_one({"collection": request.args["collection"]})
    else:
        preset_values = False
        parameters = None

    if oidc.user_loggedin:
        info = oidc.user_getinfo(['preferred_username', 'email', 'sub'])

        username = info.get('preferred_username')
        return render_template("index.html", app_url=os.environ['APP_URL'],
                               app_url_path=os.environ['APP_URL_PATH'][:-1],
                               example_db=os.environ['EXAMPLE_DB'], user_name=username, isPublic=False,
                               preset_values=preset_values, parameters=parameters)
    else:
        return render_template("index.html", app_url=os.environ['APP_URL'],
                               app_url_path=os.environ['APP_URL_PATH'][:-1],
                               example_db=os.environ['EXAMPLE_DB'], isPublic=True,
                               preset_values=preset_values, parameters=parameters)


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
                "owner": [info["sub"]],
                "read_permission": [],
                "write_permission": [],
            }

            col3 = db["Permissions"]
            col3.update_one({'user_id': info.get('sub')}, {"$push": {"owner": str(id)}}, upsert=True)

            print("save as favourite!")
            col4 = db["SavedFavoriteRequests"]
            saved_parameters = parameters.copy()
            saved_parameters["string_of_parameters"] = parameters["keywords"].replace("#", "") + \
                                                       parameters["areaParameters1"] + \
                                                       parameters["areaParameters2"] + parameters[
                                                           "areaParameters3"] + \
                                                       parameters["SearchParameters1"] + parameters["start_date"] + \
                                                       parameters["end_date"]
            saved_parameters["collection"] = [str(id)]
            saved_parameters.pop("owner", None)
            saved_parameters.pop("read_permission", None)
            saved_parameters.pop("write_permission", None)

            saved_by_user = col4.find_one({'user_id': info.get('sub'),
                                           "requests.string_of_parameters": saved_parameters[
                                               "string_of_parameters"]})
            if saved_by_user is not None:
                col4.update_one({'user_id': info.get('sub'),
                                 "requests.string_of_parameters": saved_parameters["string_of_parameters"]},
                                {"$addToSet": {'requests.$.collection': str(id)}})
            elif request.form.get('save-as-favourite'):

                col4.update_one({'user_id': info.get('sub')}, {"$addToSet": {"requests": saved_parameters}},
                                upsert=True)

            else:
                print("do not save as favourite")

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

        if oidc.user_loggedin:
            info = oidc.user_getinfo(['preferred_username', 'email', 'sub'])
            col3 = db["API_Credentials"]
            current_user = col3.find_one({"user_sub": info.get('sub')})

            if "in_use" in current_user:
                if current_user["in_use"]:
                    access_token_secret = current_user["credentials"]["access_token_secret"]
                    access_token = current_user["credentials"]["access_token"]
                    consumer_secret = current_user["credentials"]["api_key_secret"]
                    consumer_key = current_user["credentials"]["api_key"]
                    bearer = None

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


def send_data_to_kafka(json_data1, topic_name):
    client = KafkaClient(hosts=os.environ["KAFKA_URL"])
    topic = client.topics[topic_name]
    with topic.get_sync_producer() as producer:
        print((json.dumps(json_data1)).encode("utf-8"))
        producer.produce((json.dumps(json_data1)).encode("utf-8"))


@app.route(os.environ['APP_URL_PATH'] + '<collection>/agree/<decision>/<id>', methods=["POST", "GET"])
@oidc.require_login
def agree_with_result(collection, decision, id):
    if request.method == "POST":

        info = oidc.user_getinfo(['preferred_username', 'email', 'sub'])
        col2 = db["Requests"]

        parameters = col2.find_one({"collection": str(collection)})

        if parameters is not None:
            if "owner" in parameters:
                if parameters["owner"] is not None:
                    if not (info.get('sub') in parameters["owner"]):
                        if "write_permission" in parameters:
                            if parameters["write_permission"] is not None:
                                if not (info.get('sub') in parameters["write_permission"]):
                                    return error403("403")
                            else:
                                return error403("403")
                        else:
                            return error403("403")

                else:
                    return error403("403")
            else:
                return error403("403")

        else:
            return page_not_found("404")

        col1 = db[collection]

        col1.update_one({"_id": ObjectId(id)},
                        {'$addToSet': {'classification_result_' + decision + "_agreed": info.get('sub')}}, upsert=True)

        col1.update_one({"_id": ObjectId(id)},
                        {'$pullAll': {'classification_result_' + decision + "_disagreed": [info.get('sub')]}})

        curr_dt = datetime.datetime.now()
        timestamp = int(round(curr_dt.timestamp()) * 1000000000)

        json_data1 = {
            "name": "BotDetectorAgreeDisagreeData",
            "string_collection": str(collection),
            "string_type_of_classification_result": str(decision),
            "string_decision": "agree",
            "string_botdetector_user_id": info.get('sub'),
            "string_user_id_in_collection": str(id),
            "timestamp": str(timestamp)
        }

        p1 = multiprocessing.Process(name='p2', target=startSignalGenerator,
                                     args=(json_data1, "telegraf-to-influxdb-json",))
        p1.start()

        return "Ok", 200


@app.route(os.environ['APP_URL_PATH'] + '<collection>/disagree/<decision>/<id>', methods=["POST", "GET"])
@oidc.require_login
def disagree_with_result(collection, decision, id):
    if request.method == "POST":

        info = oidc.user_getinfo(['preferred_username', 'email', 'sub'])
        col2 = db["Requests"]

        parameters = col2.find_one({"collection": str(collection)})

        if parameters is not None:
            if "owner" in parameters:
                if parameters["owner"] is not None:
                    if not (info.get('sub') in parameters["owner"]):
                        if "write_permission" in parameters:
                            if parameters["write_permission"] is not None:
                                if not (info.get('sub') in parameters["write_permission"]):
                                    return error403("403")
                            else:
                                return error403("403")
                        else:
                            return error403("403")

                else:
                    return error403("403")
            else:
                return error403("403")

        else:
            return page_not_found("404")

        col1 = db[collection]
        col1.update_one({"_id": ObjectId(id)},
                        {'$addToSet': {'classification_result_' + decision + "_disagreed": info.get('sub')}},
                        upsert=True)

        col1.update_one({"_id": ObjectId(id)},
                        {'$pullAll': {'classification_result_' + decision + "_agreed": [info.get('sub')]}})

        curr_dt = datetime.datetime.now()
        timestamp = int(round(curr_dt.timestamp()) * 1000000000)

        json_data1 = {
            "name": "BotDetectorAgreeDisagreeData",
            "string_collection": str(collection),
            "string_type_of_classification_result": str(decision),
            "string_decision": "agree",
            "string_botdetector_user_id": info.get('sub'),
            "string_user_id_in_collection": str(id),
            "timestamp": str(timestamp)
        }

        p1 = multiprocessing.Process(name='p2', target=startSignalGenerator,
                                     args=(json_data1, "telegraf-to-influxdb-json",))
        p1.start()

        return "Ok", 200


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

    if oidc.user_loggedin:
        info = oidc.user_getinfo(['preferred_username', 'email', 'sub'])
        col3 = db["API_Credentials"]
        current_user = col3.find_one({"user_sub": info.get('sub')})

        if "in_use" in current_user:
            if current_user["in_use"]:
                access_token_secret = current_user["credentials"]["access_token_secret"]
                access_token = current_user["credentials"]["access_token"]
                consumer_secret = current_user["credentials"]["api_key_secret"]
                consumer_key = current_user["credentials"]["api_key"]
                bearer = None

    if bearer is None:
        use_bearer = False

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


def get_scale_parameters():
    scale_object = {}
    scale_object["small_interval_between_tweets_count"] = {
        "danger_threshold": float(os.environ["PAMP_THRESHOLD_SMALL_INTERVAL"]),
        "pamp_threshold": float(os.environ["PAMP_THRESHOLD_SMALL_INTERVAL"]) + \
                          float(os.environ["PAMP_MULTIPLIER_SMALL_INTERVAL"]) * \
                          float(os.environ["PAMP_INTERVAL_SMALL_INTERVAL"]),

    }

    scale_object["average_favorite_count"] = {
        "safe_threshold": float(os.environ["SS_THRESHOLD_AVERAGE_FAVORITE_COUNT"]),
    }

    scale_object["average_retweet_count"] = {
        "safe_threshold": float(os.environ["SS_THRESHOLD_AVERAGE_RETWEET_COUNT"]),
    }

    # TIME ENTROPY

    scale_object["time_entropy"] = {
        "pamp_threshold": float(os.environ["PAMP_THRESHOLD_TIME_ENTROPY"]),
        "danger_threshold": float(os.environ["SS_THRESHOLD_TIME_ENTROPY"]),
        "borders": [0, 4.5],
        "progressbar": {
            "pamp": 0,
            "danger": 0,
            "safe": 0,
        }
    }

    scale_object["time_entropy"]["progressbar"]["pamp"] = int(100 * scale_object["time_entropy"]["pamp_threshold"] / \
                                                                 scale_object["time_entropy"]["borders"][1])


    scale_object["time_entropy"]["progressbar"]["danger"] = int(100 * (
            scale_object["time_entropy"]["danger_threshold"] - scale_object["time_entropy"]["pamp_threshold"]) / \
                                                                   scale_object["time_entropy"]["borders"][1])


    scale_object["time_entropy"]["progressbar"]["safe"] = int(100 - \
                                                                 scale_object["time_entropy"]["progressbar"]["danger"] - \
                                                                 scale_object["time_entropy"]["progressbar"]["pamp"])

    # BASIC

    scale_object["basic"] = {
        "danger_threshold": float(os.environ["DS_THRESHOLD_BASIC_RATIO"]),
        "safe_threshold": float(os.environ["SS_THRESHOLD_BASIC_RATIO"]),
        "borders": [0, 1],
        "progressbar": {
            "pamp": 0,
            "danger": 0,
            "safe": 0,
            "safe_and_danger": 0,
        }
    }

    scale_object["basic"]["progressbar"]["safe"] = int(100 * scale_object["basic"]["safe_threshold"])


    scale_object["basic"]["progressbar"]["danger"] = int(100 * (
            scale_object["basic"]["danger_threshold"] - scale_object["basic"]["safe_threshold"]))


    scale_object["basic"]["progressbar"]["pamp"] = int(100 - scale_object["basic"]["progressbar"]["danger"] - \
                                                          scale_object["basic"]["progressbar"]["safe"])


    scale_object["basic"]["progressbar"]["safe_and_danger"] = int(scale_object["basic"]["progressbar"]["safe"] + \
                                                                     scale_object["basic"]["progressbar"]["danger"])


    # HASHTAG

    scale_object["hashtag_tweet_ratio"] = {
        "danger_threshold": float(os.environ["DS_THRESHOLD_HASHTAG_TWEET_RATIO"]),
        "safe_threshold": float(os.environ["SS_THRESHOLD_HASHTAG_TWEET_RATIO"]),
        "borders": [0, float(os.environ["DS_THRESHOLD_HASHTAG_TWEET_RATIO"]) + 2],
        "progressbar": {
            "pamp": 0,
            "danger": 0,
            "safe": 0,
        }
    }


    scale_object["hashtag_tweet_ratio"]["progressbar"]["safe"] = int(100 * scale_object["hashtag_tweet_ratio"][
        "safe_threshold"] / scale_object["hashtag_tweet_ratio"]["borders"][1])


    scale_object["hashtag_tweet_ratio"]["progressbar"]["danger"] = int(100 * (
            scale_object["hashtag_tweet_ratio"]["danger_threshold"] - scale_object["hashtag_tweet_ratio"][
        "safe_threshold"]) / scale_object["hashtag_tweet_ratio"]["borders"][1])


    scale_object["hashtag_tweet_ratio"]["progressbar"]["pamp"] = int(100 -
                                            scale_object["hashtag_tweet_ratio"]["progressbar"]["danger"] -
                                            scale_object["hashtag_tweet_ratio"]["progressbar"]["safe"])

    # FRIENDS GROWTH RATE

    scale_object["friends_growth_rate"] = {
        "danger_threshold": float(os.environ["DS_THRESHOLD_FRIENDS_GROWTH_RATE"]) + \
                            float(os.environ["DS_MULTIPLIER_FRIENDS_GROWTH_RATE"]) * \
                            float(os.environ["DS_INTERVAL_FRIENDS_GROWTH_RATE"]),
        "safe_threshold": float(os.environ["DS_THRESHOLD_FRIENDS_GROWTH_RATE"]),
        "borders": [0, 25],
        "progressbar": {
            "pamp": 0,
            "danger": 0,
            "safe": 0,
        }
    }

    scale_object["friends_growth_rate"]["progressbar"]["safe"] = int(100 * scale_object["friends_growth_rate"][
        "safe_threshold"] / scale_object["friends_growth_rate"]["borders"][1])


    scale_object["friends_growth_rate"]["progressbar"]["danger"] = int(100 * (
            scale_object["friends_growth_rate"]["danger_threshold"] - scale_object["friends_growth_rate"][
        "safe_threshold"]) / scale_object["friends_growth_rate"]["borders"][1])


    scale_object["friends_growth_rate"]["progressbar"]["pamp"] = int(100 -
                                    scale_object["friends_growth_rate"]["progressbar"]["safe"] -
                                    scale_object["friends_growth_rate"]["progressbar"]["danger"])


    # STATUSES GROWTH RATE

    scale_object["statuses_growth_rate"] = {
        "danger_threshold": float(os.environ["DS_THRESHOLD_STATUSES_GROWTH_RATE"]) + \
                            float(os.environ["DS_MULTIPLIER_STATUSES_GROWTH_RATE"]) * \
                            float(os.environ["DS_INTERVAL_STATUSES_GROWTH_RATE"]),
        "safe_threshold": float(os.environ["DS_THRESHOLD_STATUSES_GROWTH_RATE"]),
        "borders": [0, 100],
        "progressbar": {
            "pamp": 0,
            "danger": 0,
            "safe": 0,
        }
    }

    scale_object["statuses_growth_rate"]["progressbar"]["safe"] = int(100 * scale_object["statuses_growth_rate"][
        "safe_threshold"] / scale_object["statuses_growth_rate"]["borders"][1])


    scale_object["statuses_growth_rate"]["progressbar"]["danger"] = int(100 * (
            scale_object["statuses_growth_rate"]["danger_threshold"] - scale_object["statuses_growth_rate"][
        "safe_threshold"]) / scale_object["statuses_growth_rate"]["borders"][1])


    scale_object["statuses_growth_rate"]["progressbar"]["pamp"] = int(100 -
                                                scale_object["statuses_growth_rate"]["progressbar"]["safe"] -
                                                scale_object["statuses_growth_rate"]["progressbar"]["danger"])


    # AVG TWEET SIMILARITY

    scale_object["avg_tweet_similarity"] = {
        "danger_threshold": float(os.environ["SS_THRESHOLD_AVG_TWEET_SIMILARITY"]),
        "pamp_threshold": float(os.environ["PAMP_THRESHOLD_AVG_TWEET_SIMILARITY"]),
        "borders": [0, 1],
        "progressbar": {
            "pamp": 0,
            "danger": 0,
            "safe": 0,
        }
    }

    scale_object["avg_tweet_similarity"]["progressbar"]["safe"] = int(100 * scale_object["avg_tweet_similarity"][
        "danger_threshold"])


    scale_object["avg_tweet_similarity"]["progressbar"]["danger"] = int(100 * (
            scale_object["avg_tweet_similarity"]["pamp_threshold"] - scale_object["avg_tweet_similarity"][
        "danger_threshold"]))


    scale_object["avg_tweet_similarity"]["progressbar"]["pamp"] = int(100 - scale_object["avg_tweet_similarity"][
        "progressbar"]["danger"] - scale_object["avg_tweet_similarity"]["progressbar"]["safe"])


    return scale_object


@app.route(os.environ['APP_URL_PATH'] + '<collection>/advanced/<id>')
def user_advanced(collection, id):
    #try:
        scale_parameters = get_scale_parameters()
        pprint(scale_parameters)

        col = db[collection]
        user_found = col.find_one(ObjectId(id))
        if user_found:
            if oidc.user_loggedin:
                info = oidc.user_getinfo(['preferred_username', 'email', 'sub'])
                username = info.get('preferred_username')

                return render_template('user_advanced.html', tweetArr=json.dumps(user_found["tweets"]), user=user_found,
                                       tweet=json.dumps(user_found["found_tweet"]),
                                       app_url=os.environ['APP_URL'],
                                       app_url_path=os.environ['APP_URL_PATH'][:-1],
                                       collection=collection,
                                       example_db=os.environ['EXAMPLE_DB'], user_name=username,
                                       scale_parameters=scale_parameters)
            else:
                return render_template('user_advanced.html', tweetArr=json.dumps(user_found["tweets"]), user=user_found,
                                       tweet=json.dumps(user_found["found_tweet"]),
                                       app_url=os.environ['APP_URL'],
                                       app_url_path=os.environ['APP_URL_PATH'][:-1],
                                       collection=collection,
                                       example_db=os.environ['EXAMPLE_DB'],
                                       scale_parameters=scale_parameters)

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


"""
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
"""


@app.route(os.environ['APP_URL_PATH'] + 'recalculate/<collection>/<id>')
def recalc(collection, id):
    consumer_key = os.environ['CONSUMER_KEY']
    consumer_secret = os.environ['CONSUMER_SECRET']
    access_token = os.environ['ACCESS_TOKEN']
    access_token_secret = os.environ['ACCESS_TOKEN_SECRET']
    bearer = os.environ['BEARER']
    use_bearer = int(os.environ['USE_BEARER'])
    if bearer is None:
        use_bearer = False

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


@app.errorhandler(400)
def error400(e):
    if oidc.user_loggedin:
        info = oidc.user_getinfo(['preferred_username', 'email', 'sub'])
        username = info.get('preferred_username')

        return render_template('400.html', app_url=os.environ['APP_URL'],
                               app_url_path=os.environ['APP_URL_PATH'][:-1],
                               example_db=os.environ['EXAMPLE_DB'], user_name=username, code=e), 400
    else:
        return render_template('400.html', app_url=os.environ['APP_URL'],
                               app_url_path=os.environ['APP_URL_PATH'][:-1],
                               example_db=os.environ['EXAMPLE_DB'], code=e), 400


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
