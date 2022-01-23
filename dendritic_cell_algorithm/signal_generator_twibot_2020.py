import copy
import math
import re
import os
from math import log2

import enchant
import nltk
import json
import scipy.stats
from datetime import date, datetime
import operator
import logging


class Signals:
    def __init__(self):
        self._pamp = 0
        self._danger_signal = 0
        self._safe_signal = 0

        self._pamp_bot = 0
        self._danger_signal_bot = 0
        self._safe_signal_bot = 0

        self._pamp_bad_intentions = 0
        self._danger_signal_bad_intentions = 0
        self._safe_signal_bad_intentions = 0

        self._cms = 0
        self._mDC = 0
        self._smDC = 0
        self._k = 0

        self._cms_bot = 0
        self._mDC_bot = 0
        self._smDC_bot = 0
        self._k_bot = 0

        self._cms_bad_intentions = 0
        self._mDC_bad_intentions = 0
        self._smDC_bad_intentions = 0
        self._k_bad_intentions = 0

        self._intentions_are_bad_probability = 0
        self._is_bot_probability = 0

        self._parameters = {}

    def get_pamp(self):
        return self._pamp

    def increase_pamp(self, x, bot_indicator, bad_intentions_indicator, reason=""):
        self._pamp += x
        logging.info(f"PAMP + {x} because of {reason}")
        if bot_indicator:
            self._pamp_bot += x
            logging.info(f"PAMP_bot + {x} because of {reason}")
        if bad_intentions_indicator:
            self._pamp_bad_intentions += x
            logging.info(f"PAMP_bad_intentions + {x} because of {reason}")

    def get_danger_signal(self):
        return self._danger_signal

    def increase_danger_signal(self, x, bot_indicator, bad_intentions_indicator, reason=""):
        self._danger_signal += x
        logging.info(f"Danger Signal + {x} because of {reason}")
        if bot_indicator:
            self._danger_signal_bot += x
            logging.info(f"Danger Signal_bot + {x} because of {reason}")
        if bad_intentions_indicator:
            self._danger_signal_bad_intentions += x
            logging.info(f"Danger Signal_bad_intentions + {x} because of {reason}")

    def get_safe_signal(self):
        return self._safe_signal

    def increase_safe_signal(self, x, bot_indicator, bad_intentions_indicator, reason=""):
        self._safe_signal += x
        logging.info(f"Safe Signal + {x} because of {reason}")
        if bot_indicator:
            self._safe_signal_bot += x
            logging.info(f"Safe Signal_bot + {x} because of {reason}")
        if bad_intentions_indicator:
            self._safe_signal_bad_intentions += x
            logging.info(f"Safe Signal_bad_intentions + {x} because of {reason}")

    def recalculate_probabilities(self, identifies_itself_as_bot):
        self._intentions_are_bad_probability = int(max(0, min(100, self._k_bad_intentions)))
        if identifies_itself_as_bot:
            self._is_bot_probability = int(max(0, min(100, self._k_bot)))
        else:
            self._is_bot_probability = int(max(0, min(99, self._k_bot)))
        logging.info(f"recalculate intentions_are_bad_probability: {self._intentions_are_bad_probability}")
        logging.info(f"recalculate is_bot_probability:{self._is_bot_probability}")

    def get_csm(self):
        return self._cms

    def get_csm_bot(self):
        return self._cms_bot

    def get_csm_bad_intentions(self):
        return self._cms_bad_intentions

    def update_csm(self):
        self._cms = float(os.environ['W_PAMP_CSM']) * self._pamp + int(
            os.environ['W_DS_CSM']) * self._danger_signal + float(os.environ[
                                                                      'W_SS_CSM']) * self._safe_signal
        self._cms_bot = float(os.environ['W_PAMP_CSM']) * self._pamp_bot + int(
            os.environ['W_DS_CSM']) * self._danger_signal_bot + \
                        float(os.environ['W_SS_CSM']) * self._safe_signal_bot
        self._cms_bad_intentions = float(os.environ['W_PAMP_CSM']) * self._pamp_bad_intentions + float(os.environ[
                                                                                                           'W_DS_CSM']) * self._danger_signal_bad_intentions + int(
            os.environ['W_SS_CSM']) * self._safe_signal_bad_intentions
        logging.info(f"CMS: {self._cms}")
        logging.info(f"CMS_bot: {self._cms_bot}")
        logging.info(f"CMS_bad_intentions: {self._cms_bad_intentions}")

    def get_mDC(self):
        return self._mDC

    def get_mDC_bot(self):
        return self._mDC_bot

    def get_mDC_bad_intentions(self):
        return self._mDC_bad_intentions

    def update_mDC(self):
        self._mDC = max(float(os.environ['W_PAMP_MDC']) * self._pamp + int(
            os.environ['W_DS_MDC']) * self._danger_signal + float(os.environ[
                                                                      'W_SS_MDC']) * self._safe_signal, 0)
        self._mDC_bot = max(float(os.environ['W_PAMP_MDC']) * self._pamp_bot + int(
            os.environ['W_DS_MDC']) * self._danger_signal_bot + \
                            float(os.environ['W_SS_MDC']) * self._safe_signal_bot, 0)
        self._mDC_bad_intentions = max(float(os.environ['W_PAMP_MDC']) * self._pamp_bad_intentions + int(
            os.environ['W_DS_MDC']) * self._danger_signal_bad_intentions + int(
            os.environ['W_SS_MDC']) * self._safe_signal_bad_intentions, 0)
        logging.info(f"mDC: {self._mDC}")
        logging.info(f"mDC_bot: {self._mDC_bot}")
        logging.info(f"mDC_bad_intentions: {self._mDC_bad_intentions}")

    def get_smDC(self):
        return self._smDC

    def get_smDC_bot(self):
        return self._smDC_bot

    def get_smDC_bad_intentions(self):
        return self._smDC_bad_intentions

    def update_smDC(self):
        self._smDC = float(os.environ['W_PAMP_SMDC']) * self._pamp + float(
            os.environ['W_DS_SMDC']) * self._danger_signal + \
                     float(os.environ['W_SS_SMDC']) * self._safe_signal
        self._smDC_bot = float(os.environ['W_PAMP_SMDC']) * self._pamp_bot + float(os.environ[
                                                                                       'W_DS_SMDC']) * self._danger_signal_bot + \
                         float(os.environ['W_SS_SMDC']) * self._safe_signal_bot
        self._smDC_bad_intentions = float(os.environ['W_PAMP_SMDC']) * self._pamp_bad_intentions + float(os.environ[
                                                                                                             'W_DS_SMDC']) * self._danger_signal_bad_intentions + \
                                    float(os.environ['W_SS_SMDC']) * self._safe_signal_bad_intentions
        logging.info(f"smDC: {self._smDC}")
        logging.info(f"smDC_bot: {self._smDC_bot}")
        logging.info(f"smDC_bad_intentions: {self._smDC_bad_intentions}")

    def get_k(self):
        return self._k

    def get_k_bot(self):
        return self._k_bot

    def get_k_bad_intentions(self):
        return self._k_bad_intentions

    def update_k(self):
        self._k = self._mDC - self._smDC
        self._k_bot = self._mDC_bot - self._smDC_bot
        self._k_bad_intentions = self._mDC_bad_intentions - self._smDC_bad_intentions
        logging.info(f"K: {self._k}")
        logging.info(f"K_bot: {self._k_bot}")
        logging.info(f"K_bad_intentions: {self._k_bad_intentions}")

    def get_parameters(self):
        return self._parameters

    def update_parameters(self, key, value):
        self._parameters[key] = value
        logging.info(f"{key}: {value}")

    def generate_signals(self, friends_count,
                         statuses_count,
                         followers_count,
                         verified,
                         default_profile,
                         default_profile_image,
                         created_at,
                         name,
                         screen_name,
                         description,
                         tweets):

        if len(tweets) > 20:
            tweets = tweets[:20]

        logging.info("Check default_profile")
        self.increase_danger_signal(float(os.environ["DEFAULT_PROFILE_DS_MULTIPLIER"]) * int(default_profile), True,
                                    False,
                                    "default_profile")
        self.increase_safe_signal(float(os.environ["DEFAULT_PROFILE_SS_MULTIPLIER"]) * (1 - int(default_profile)), True,
                                  False,
                                  "default_profile")

        logging.info("Check default_profile_image")
        self.increase_danger_signal(
            float(os.environ["DEFAULT_PROFILE_IMAGE_DS_MULTIPLIER"]) * int(default_profile_image),
            True, False, "default_profile_image")
        self.increase_safe_signal(
            float(os.environ["DEFAULT_PROFILE_IMAGE_SS_MULTIPLIER"]) * (1 - int(default_profile_image)),
            True, False, "default_profile_image")

        self.increase_safe_signal(float(os.environ['VERIFIED_SS_MULTIPLIER']) * int(verified), False, True, "verified")

        if len(tweets) > 1:
            avg_tweet_similarity = average_tweet_similarity(tweets)  # nltk.edit_distance()
            logging.info("Check avg_tweet_similarity")

            self.increase_pamp(min(determine_signal_strength(avg_tweet_similarity, ">",
                                                             float(os.environ["PAMP_THRESHOLD_AVG_TWEET_SIMILARITY"]),
                                                             float(os.environ["PAMP_INTERVAL_AVG_TWEET_SIMILARITY"])),
                                   float(os.environ["PAMP_UPPER_BOUND_AVG_TWEET_SIMILARITY"]) * len(tweets)),
                               True, False, "avg_tweet_similarity")

            self.increase_safe_signal(determine_signal_strength(avg_tweet_similarity, "<",
                                                                float(os.environ["SS_THRESHOLD_AVG_TWEET_SIMILARITY"]),
                                                                float(os.environ["SS_INTERVAL_AVG_TWEET_SIMILARITY"])),
                                      True, False, "avg_tweet_similarity")

            small_interval_between_tweets_count = None

        else:
            avg_tweet_similarity = None
            small_interval_between_tweets_count = None

        time_entropy = None

        if len(tweets) > 3:
            retweet_tweet_ratio, url_tweet_ratio, user_mentions_tweet_ratio, hashtag_tweet_ratio = calculate_tweet_parameters(
                tweets)

            self.increase_danger_signal(
                min(determine_signal_strength(retweet_tweet_ratio, ">",
                                              float(os.environ["DS_THRESHOLD_BASIC_RATIO"]),
                                              float(os.environ["DS_INTERVAL_BASIC_RATIO"])),
                    float(os.environ["DS_UPPER_BOUND_BASIC_RATIO"]) * len(tweets)),
                True, False, "max(retweet_tweet_ratio, quote_tweet_ratio)")

            self.increase_safe_signal(
                determine_signal_strength(retweet_tweet_ratio, "<",
                                          float(os.environ["SS_THRESHOLD_BASIC_RATIO"]),
                                          float(os.environ["SS_INTERVAL_BASIC_RATIO"])),
                True, False, "max(retweet_tweet_ratio, quote_tweet_ratio)")

            self.increase_danger_signal(min(determine_signal_strength(url_tweet_ratio, ">",
                                                                      float(os.environ["DS_THRESHOLD_BASIC_RATIO"]),
                                                                      float(os.environ["DS_INTERVAL_BASIC_RATIO"])),
                                            float(os.environ["DS_UPPER_BOUND_BASIC_RATIO"]) * len(tweets)),
                                        False, True, "url_tweet_ratio")

            self.increase_safe_signal(determine_signal_strength(url_tweet_ratio, "<",
                                                                float(os.environ["SS_THRESHOLD_BASIC_RATIO"]),
                                                                float(os.environ["SS_INTERVAL_BASIC_RATIO"])),
                                      False, True, "url_tweet_ratio")

            self.increase_danger_signal(
                min(determine_signal_strength(user_mentions_tweet_ratio, ">",
                                              float(os.environ["DS_THRESHOLD_BASIC_RATIO"]),
                                              float(os.environ["DS_INTERVAL_BASIC_RATIO"])),
                    float(os.environ["DS_UPPER_BOUND_BASIC_RATIO"]) * len(tweets)),
                False, True, "user_mentions_tweet_ratio")

            self.increase_safe_signal(determine_signal_strength(user_mentions_tweet_ratio, "<",
                                                                float(os.environ["SS_THRESHOLD_BASIC_RATIO"]),
                                                                float(os.environ["SS_INTERVAL_BASIC_RATIO"])),
                                      False, True, "user_mentions_tweet_ratio")

            self.increase_danger_signal(min(determine_signal_strength(hashtag_tweet_ratio, ">=",
                                                                      float(os.environ[
                                                                                "DS_THRESHOLD_HASHTAG_TWEET_RATIO"]),
                                                                      float(os.environ[
                                                                                "DS_INTERVAL_HASHTAG_TWEET_RATIO"])),
                                            float(os.environ["DS_UPPER_BOUND_BASIC_RATIO"]) * len(tweets)),
                                        False, True, "hashtag_tweet_ratio")

            self.increase_safe_signal(determine_signal_strength(hashtag_tweet_ratio, "<=",
                                                                float(os.environ["SS_THRESHOLD_HASHTAG_TWEET_RATIO"]),
                                                                float(os.environ["SS_INTERVAL_HASHTAG_TWEET_RATIO"])),
                                      False, True, "hashtag_tweet_ratio")

            """
            self.increase_danger_signal(
                min(determine_signal_strength(average_retweet_count, "<=", 0.1, 0.01), len(tweets)),
                False, True, "average_retweet_count")"""

        else:
            retweet_tweet_ratio, url_tweet_ratio, user_mentions_tweet_ratio, hashtag_tweet_ratio = None, None, None, None

        name_screen_name_similarity = similarity(name, screen_name)
        # self.increase_danger_signal(determine_signal_strength(name_screen_name_similarity, ">=", 0.9, 0.05))

        screen_name_length = len(screen_name)
        # self.increase_danger_signal(determine_signal_strength(screen_name_length, ">=", 13, 2))

        identifies_itself_as_bot = contains_bot_info(description)
        self.increase_safe_signal(
            float(os.environ["SS_MULTIPLIER_IDENTIFIES_ITSELF_AS_BOT"]) * int(identifies_itself_as_bot),
            False, True, "identifies_itself_as_bot")
        self.increase_pamp(
            float(os.environ["SS_MULTIPLIER_IDENTIFIES_ITSELF_AS_BOT"]) * int(identifies_itself_as_bot),
            False, True, "identifies_itself_as_bot")

        if friends_count > 0:
            followers_friends_ratio = followers_count / friends_count
            self.increase_safe_signal(
                min(determine_signal_strength(followers_friends_ratio, ">=",
                                              float(os.environ["SS_THRESHOLD_FOLLOWERS_FRIENDS_RATIO"]),
                                              float(os.environ["SS_INTERVAL_FOLLOWERS_FRIENDS_RATIO"])),
                    float(os.environ["SS_UPPER_BOUND_FOLLOWERS_FRIENDS_RATIO"])), True, False,
                "followers_friends_ratio")
        else:
            followers_friends_ratio = None

        user_age = (datetime.now() - datetime.strptime(created_at.replace(" +0000", ""), '%c')).days

        if user_age > 0:
            friends_growth_rate = friends_count / user_age
            statuses_growth_rate = statuses_count / user_age
            logging.info("friends_growth_rate")
            self.increase_danger_signal(
                min(float(os.environ["DS_MULTIPLIER_FRIENDS_GROWTH_RATE"]) * determine_signal_strength(
                    friends_growth_rate, ">=",
                    float(os.environ["DS_THRESHOLD_FRIENDS_GROWTH_RATE"]),
                    float(os.environ["DS_INTERVAL_FRIENDS_GROWTH_RATE"])),
                    user_age * float(os.environ["DS_UPPER_BOUND_FRIENDS_GROWTH_RATE"])), True, False,
                "friends_growth_rate")

            logging.info("statuses_growth_rate")
            self.increase_danger_signal(
                float(os.environ["DS_MULTIPLIER_STATUSES_GROWTH_RATE"]) * determine_signal_strength(
                    statuses_growth_rate, ">=",
                    float(os.environ["DS_THRESHOLD_STATUSES_GROWTH_RATE"]),
                    float(os.environ["DS_INTERVAL_STATUSES_GROWTH_RATE"])), True, False,
                "statuses_growth_rate")

        else:
            friends_growth_rate = None
            statuses_growth_rate = None
        self.update_csm()
        self.update_mDC()
        self.update_smDC()
        self.update_k()
        self.recalculate_probabilities(identifies_itself_as_bot)

        self.update_parameters("cms", self._cms)
        self.update_parameters("mDC", self._mDC)
        self.update_parameters("smDC", self._smDC)
        self.update_parameters("k", self._k)

        self.update_parameters("cms_bot", self._cms_bot)
        self.update_parameters("mDC_bot", self._mDC_bot)
        self.update_parameters("smDC_bot", self._smDC_bot)
        self.update_parameters("k_bot", self._k_bot)

        self.update_parameters("cms_bad_intentions", self._cms_bad_intentions)
        self.update_parameters("mDC_bad_intentions", self._mDC_bad_intentions)
        self.update_parameters("smDC_bad_intentions", self._smDC_bad_intentions)
        self.update_parameters("k_bad_intentions", self._k_bad_intentions)

        self.update_parameters("is_bot_probability", self._is_bot_probability)
        self.update_parameters("intentions_are_bad_probability", self._intentions_are_bad_probability)
        self.update_parameters("avg_tweet_similarity", avg_tweet_similarity)
        self.update_parameters("small_interval_between_tweets_count", small_interval_between_tweets_count)
        self.update_parameters("time_entropy", time_entropy)
        self.update_parameters("retweet_tweet_ratio", retweet_tweet_ratio)
        self.update_parameters("url_tweet_ratio", url_tweet_ratio)
        self.update_parameters("user_mentions_tweet_ratio", user_mentions_tweet_ratio)
        self.update_parameters("hashtag_tweet_ratio", hashtag_tweet_ratio)
        self.update_parameters("average_favorite_count", None)
        self.update_parameters("average_retweet_count", None)
        self.update_parameters("is_sensitive_count", None)
        self.update_parameters("name_screen_name_similarity", name_screen_name_similarity)
        self.update_parameters("screen_name_length", screen_name_length)
        self.update_parameters("identifies_itself_as_bot", identifies_itself_as_bot)
        self.update_parameters("followers_friends_ratio", followers_friends_ratio)
        self.update_parameters("statuses_growth_rate", statuses_growth_rate)
        self.update_parameters("friends_growth_rate", friends_growth_rate)


def average_tweet_similarity(tweets):
    avg_tweet_similarity = 0
    count = len(tweets) * (len(tweets) - 1) / 2
    if count == 0:
        return 0
    # tweets_with_replaced_urls = replace_urls(copy.deepcopy(tweets))
    # tweets_with_replaced_users = replace_user_mentions(copy.deepcopy(tweets))
    # tweets_with_replaced_all = replace_user_mentions(replace_urls(copy.deepcopy(tweets)))

    i = 0
    while i < len(tweets):
        j = i
        while j < len(tweets):
            if i != j:
                tweet_similarity = similarity(tweets[i], tweets[j])
                """
                                       similarity(tweets_with_replaced_all[i]["text"],
                                                  tweets_with_replaced_all[j]["text"]),
                                       similarity(tweets_with_replaced_users[i]["text"],
                                                  tweets_with_replaced_users[j]["text"]),
                                       similarity(tweets_with_replaced_urls[i]["text"],
                                                  tweets_with_replaced_urls[j]["text"])
                """
                avg_tweet_similarity += tweet_similarity
            j += 1
        i += 1
    avg_tweet_similarity = avg_tweet_similarity / count
    print(f"average tweet similarity: {avg_tweet_similarity}")
    return avg_tweet_similarity


def replace_urls(tweets):
    for tweet in tweets:
        i = 0
        while i < len(tweet["entities"]["urls"]):
            tweet["text"] = tweet["text"].replace(tweet["entities"]["urls"][i]["url"],
                                                  tweet["entities"]["urls"][i]["expanded_url"])
            i += 1
    return tweets
    """
    for tweet in tweets:
        i = 0
        while i < len(tweet["entities"]["urls"]):
            tweet["text"] = tweet["text"].replace(tweet["entities"]["urls"][i]["url"],
                                                  "https://hier-is-url")
            i += 1
    return tweets"""


def remove_urls(tweet):
    i = 0
    while i < len(tweet["entities"]["urls"]):
        tweet["text"] = tweet["text"].replace(tweet["entities"]["urls"][i]["url"], "")
        i += 1
    return tweet


def remove_user_mentions(tweet):
    i = 0
    while i < len(tweet["entities"]["user_mentions"]):
        tweet["text"] = tweet["text"].replace(tweet["entities"]["user_mentions"][i]["screen_name"], "")
        i += 1
    return tweet


def replace_user_mentions(tweets):
    for tweet in tweets:
        i = 0
        while i < len(tweet["entities"]["user_mentions"]):
            tweet["text"] = tweet["text"].replace(tweet["entities"]["user_mentions"][i]["screen_name"], "")
            i += 1
    return tweets
    """
    for tweet in tweets:
        i = 0
        while i < len(tweet["entities"]["user_mentions"]):
            tweet["text"] = tweet["text"].replace(tweet["entities"]["user_mentions"][i]["screen_name"], "screen_name")
            i += 1
    return tweets"""


def similarity(string1, string2):
    max_length = max(len(string1), len(string2))
    # levenshtein_distance = nltk.edit_distance(string1, string2)
    levenshtein_distance = enchant.utils.levenshtein(string1, string2)
    if max_length > 0:
        similarity_metric = ((max_length - levenshtein_distance) / max_length)
    else:
        similarity_metric = 1
    return similarity_metric


def tweeting_time_entropy(tweets):
    created_at = []
    for tweet in tweets:
        created_at.append(
            datetime.strptime(tweet["timestamp"].replace(" +0000", ""),
                              '%Y-%m-%d %X'))  # Mon Dec 13 04:16:58 +0000 2021
    res = scipy.stats.entropy(calculate_probability(created_at, 1), base=2)
    print(f"entropy: {res}")
    return float(res)


def calculate_small_intervals(tweets):
    created_at = []
    for tweet in tweets:
        created_at.append(
            datetime.strptime(tweet["timestamp"].replace(" +0000", ""),
                              '%Y-%m-%d %X'))  # Mon Dec 13 04:16:58 +0000 2021

    created_at.sort(reverse=True)
    small_intervals_count = 0
    i = 0
    while i < len(created_at) - 1:
        if (created_at[i] - created_at[i + 1]).total_seconds() < 10:
            small_intervals_count += 1;
        i += 1

    print(f"small_intervals_count: {small_intervals_count}")
    return small_intervals_count


def calculate_probability(created_at, measuring_interval):
    created_at.sort(reverse=True)
    intervals = []
    # intervals_seconds = []
    i = 0
    while i < len(created_at) - 1:
        intervals.append(int((created_at[i] - created_at[i + 1]).total_seconds() / 60 * 4))
        # intervals_seconds.append(int((created_at[i] - created_at[i + 1]).total_seconds()))
        i += 1
    print(intervals)
    # print(intervals_seconds)
    max_interval = max(intervals)
    min_interval = min(intervals)
    if max_interval == min_interval:
        print("max=min")
        return [1]
    start = int(math.floor(min_interval / measuring_interval) * measuring_interval)
    print("start")
    print(start)
    end = int(math.ceil(max_interval / measuring_interval) * measuring_interval)
    print("end")
    print(end)
    count = int((end - start) / measuring_interval) + 1
    if count == 0:
        print("count=0")
        return [1]
    print("count")
    print(count)
    probability = [0] * count
    for time in intervals:
        print(f'probability[{int((time - start) / measuring_interval)}]')
        probability[int((time - start) / measuring_interval)] += 1
        print(f'OK! probability[{int((time - start) / measuring_interval)}]')

    print([i / len(intervals) for i in probability if i != 0])
    return [i / len(intervals) for i in probability if i != 0]


def determine_signal_strength(value, comparison_sign, threshold, interval):
    ops = {'>': operator.gt,
           '<': operator.lt,
           '>=': operator.ge,
           '<=': operator.le,
           '==': operator.eq}
    signal = 0
    if ops[comparison_sign](value, threshold):
        signal = 1 + int(abs(threshold - value) / interval)

    return signal


# retweet_tweet_ratio, quote_tweet_ratio, url_tweet_ratio, user_mentions_count, hashtag_tweet_ratio, average_favorite_count, average_retweet_count, is_sensitive_count
def calculate_tweet_parameters(tweets):
    count = 0
    is_retweet_count = 0
    urls_count = 0
    hashtag_count = 0
    favorite_count = 0
    retweet_count = 0
    is_sensitive_count = 0
    user_mentions_count = 0
    for tweet in tweets:
        count += 1
        if tweet.startswith('RT '):
            is_retweet_count += 1

        urls_count += tweet.count("http")
        user_mentions_count += tweet.count("@")
        hashtag_count += tweet.count("#")

    return is_retweet_count / count, urls_count / count, user_mentions_count / count, hashtag_count / count


def contains_bot_info(description):
    return contain_words(description, ["bot", "Bot", "automated", "Automated", "robot", "Robot"])


def contain_words(string, words):
    has_word = False
    modified_string = " " + string + " "
    modified_string = re.sub(r"[^a-zA-Z ]+", " ", modified_string)
    for word in words:
        if modified_string.find(f' {word} ') != -1:
            has_word = True
            break
    return has_word
