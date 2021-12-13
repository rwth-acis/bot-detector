import os
import sys
import json
import csv
import json.decoder


def cresci_csv_to_json(path):
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
