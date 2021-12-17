import copy
import math
from math import log2

import nltk
import json
import scipy.stats
from datetime import date, datetime


def generate_signal(friends_count,
                    followers_count,
                    verified,
                    default_profile,
                    default_profile_image,
                    created_at,
                    name,
                    screen_name,
                    description,
                    tweets):
    pamp = 0
    danger_signal = 0
    safe_signal = 0

    avg_tweet_similarity = average_tweet_similarity(tweets)  # nltk.edit_distance

    print(avg_tweet_similarity)
    tweeting_time_entropy = 0  # scipy.stats.entropy()

    default_profile = 0
    verified = 0
    default_profile_image = 0
    retweet_tweet_ratio = 0
    url_tweet_ratio = 0

    hashtag_tweet_ratio = 0
    tweeting_time_entropy = 0
    name_screen_name_similarity = 0
    followers_count = 0
    average_favorite_count = 0
    followers_friends_ratio = 0
    friends_growth_rate = 0
    average_favorite_count = 0
    screen_name = 0
    identifies_itself_as_bot = 0

    cms = 2 * pamp + 1 * danger_signal + 2 * safe_signal
    mDC = 2 * pamp + 1 * danger_signal - 3 * safe_signal
    smDC = 3 * safe_signal
    k = mDC - smDC
    return [k, cms]


def average_tweet_similarity(tweets):
    avg_tweet_similarity = 0
    count = len(tweets) * (len(tweets) - 1) / 2
    tweets_with_replaced_urls = replace_urls(copy.deepcopy(tweets))
    tweets_with_replaced_users = replace_user_mentions(copy.deepcopy(tweets))
    tweets_with_replaced_all = replace_user_mentions(copy.deepcopy(tweets_with_replaced_urls))

    i = 0
    while i < len(tweets):
        j = i
        while j < len(tweets):
            if i != j:
                tweet_similarity = max(similarity(tweets[i]["full_text"], tweets[j]["full_text"]),
                                       similarity(tweets_with_replaced_all[i]["full_text"],
                                                  tweets_with_replaced_all[j]["full_text"]),
                                       similarity(tweets_with_replaced_users[i]["full_text"],
                                                  tweets_with_replaced_users[j]["full_text"]),
                                       similarity(tweets_with_replaced_urls[i]["full_text"],
                                                  tweets_with_replaced_urls[j]["full_text"]))
                avg_tweet_similarity += tweet_similarity
            j += 1
        i += 1
    avg_tweet_similarity = avg_tweet_similarity / count
    print(avg_tweet_similarity)
    return avg_tweet_similarity


def replace_urls(tweets):
    for tweet in tweets:
        i = 0
        while i < len(tweet["entities"]["urls"]):
            tweet["full_text"] = tweet["full_text"].replace(tweet["entities"]["urls"][i]["url"],
                                                            tweet["entities"]["urls"][i]["expanded_url"])
            i += 1
    return tweets


def replace_user_mentions(tweets):
    for tweet in tweets:
        i = 0
        while i < len(tweet["entities"]["user_mentions"]):
            tweet["full_text"] = tweet["full_text"].replace(tweet["entities"]["user_mentions"][i]["screen_name"], "")
            i += 1
    return tweets


def similarity(string1, string2):
    max_length = max(len(string1), len(string2))
    levenshtein_distance = nltk.edit_distance(string1, string2)
    similarity_metric = ((max_length - levenshtein_distance) / max_length)
    return similarity_metric



def tweeting_time_entropy(tweets):
    created_at=[]
    for tweet in tweets:
        created_at.append(datetime.strptime(tweet["created_at"].replace(" +0000", ""), '%c')) # Mon Dec 13 04:16:58 +0000 2021
    res = scipy.stats.entropy(calculate_probability(created_at, 30), base=2)
    print(res)
    return res


def calculate_probability(created_at, measuring_interval):
    intervals = []
    i = 0
    while i < len(created_at) - 1:
        intervals.append((created_at[i] - created_at[i+1]).total_seconds()/60)
        i += 1
    print(intervals)
    max_interval = max(intervals)
    min_interval = min(intervals)
    start = int(math.floor(min_interval / measuring_interval) * measuring_interval)
    print("start")
    print(start)
    end = int(math.ceil(max_interval / measuring_interval) * measuring_interval)
    print("end")
    print(end)
    count = int((end - start) / measuring_interval)
    print("count")
    print(count)
    probability = [0] * count
    for time in intervals:
        probability[int((time - start) / measuring_interval)] += 1
        print(f'probability[{int((time - start) / measuring_interval)}]')
    for i in probability:
        i = i / len(intervals)
        print("probabilities")
        print(i)
    return [i for i in probability if i != 0]
