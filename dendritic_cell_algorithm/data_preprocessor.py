import os
import sys
import json
import csv
import json.decoder
import tweepy
import csv
import json
import pandas as pd
import datetime


def cresci_csv_to_json(path):
    """Three json files sre created from two csv files

    Parameters
    ----------
    path : str
        path to the directory where csv files are located

    """
    # csv.field_size_limit(2147483647)
    csvfileusers = open(f'{path}users.csv', 'r', encoding="cp850")
    csvfiletweets = open(f'{path}tweets.csv', 'r', encoding="cp850")
    jsonfileusers = open(f'{path}users.json', 'w', encoding='cp850')
    jsonfiletweets = open(f'{path}tweets.json', 'w', encoding='cp850')

    fieldnames1 = (
        "id", "name", "screen_name", "statuses_count", "followers_count", "friends_count", "favourites_count",
        "listed_count",
        "url", "lang", "time_zone", "location", "default_profile", "default_profile_image", "geo_enabled",
        "profile_image_url",
        "profile_banner_url", "profile_use_background_image", "profile_background_image_url_https",
        "profile_text_color",
        "profile_image_url_https", "profile_sidebar_border_color", "profile_background_tile",
        "profile_sidebar_fill_color",
        "profile_background_image_url", "profile_background_color", "profile_link_color", "utc_offset", "is_translator",
        "follow_request_sent", "protected", "verified", "notifications", "description", "contributors_enabled",
        "following",
        "created_at", "timestamp", "crawled_at", "updated")
    reader = csv.DictReader(csvfileusers, fieldnames1)
    userObj = {'users': []}

    for row in reader:
        userObj['users'].append(row)
        # print(row)

    jsonfileusers.write(json.dumps(userObj, ensure_ascii=False, indent=4))
    csvfileusers.close()
    jsonfileusers.close()

    fieldnames2 = ("id", "text", "source", "user_id", "truncated", "in_reply_to_status_id", "in_reply_to_user_id",
                   "in_reply_to_screen_name", "retweeted_status_id", "geo", "place", "contributors", "retweet_count",
                   "reply_count", "favorite_count", "favorited", "retweeted", "possibly_sensitive", "num_hashtags",
                   "num_urls", "num_mentions", "created_at", "timestamp", "crawled_at", "updated")

    reader = csv.DictReader(csvfiletweets, fieldnames2)

    tweetsObj = {'tweets': []}

    for row in reader:
        tweetsObj['tweets'].append(row)
        # print(row)

    jsonfiletweets.write(json.dumps(tweetsObj, ensure_ascii=False, indent=4))
    csvfiletweets.close()
    jsonfiletweets.close()

    for d in userObj["users"]:
        d["tweets"] = []

    for data_item in userObj["users"]:
        # print(data_item['id'], data_item['name'])
        for tweet in tweetsObj["tweets"]:
            if tweet['user_id'] == data_item['id']:
                data_item["tweets"].append(tweet)
                # print(f'Time: {tweet["timestamp"]}, text: {tweet["text"]}')

    with open(f'{path}result.json', "w", encoding='cp850') as outfile:
        outfile.write(json.dumps(userObj, ensure_ascii=False, indent=4))


def collect_from_twitter(keyword, user_count, tweet_count):
    """Generates json file that includes users and their tweets

    Parameters
    ----------
    keyword : str
    keyword used to search for users

    user_count : int
    required number of users

    tweet_count : int
    required number of tweets from users
    """

    # input your credentials here
    consumer_key = ''
    consumer_secret = ''
    access_token = ''
    access_token_secret = ''

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth, wait_on_rate_limit=True)

    # Open/Create a file to append data
    jsonFile = open("tweets.json", "w", encoding='utf-8')

    # When using extended mode, text is replaced by a full_text, which contains the entire untruncated tweet (more than 140 characters)
    tweets = tweepy.Cursor(api.search_tweets, q=keyword, lang="en", tweet_mode='extended').items(user_count)

    final_info_for_json = {"users": []}

    for tweet in tweets:
        # print("created_at: ", tweet.created_at, ", text: ", tweet.retweeted_status.full_text, ", user: user_id: ",tweet.user.id, ", user_name: ", tweet.user.name, ", followers_count: ", tweet.user.followers_count)
        userObj = {}
        user = api.get_user(screen_name=tweet.user.screen_name)._json
        user.pop('status', None)
        userObj["user"] = user
        userObj["tweets"] = []
        for fulltweet in api.user_timeline(screen_name=tweet.user.screen_name,
                                           # max 200 tweets
                                           count=tweet_count,
                                           include_rts=False,
                                           # Necessary to keep full_text
                                           tweet_mode='extended'
                                           ):
            tw = fulltweet._json
            tw.pop('user', None)
            userObj["tweets"].append(tw)
        final_info_for_json["users"].append(userObj)

    jsonString = json.dumps(final_info_for_json, ensure_ascii=False, indent=4)

    jsonFile.write(jsonString)
    jsonFile.close()
