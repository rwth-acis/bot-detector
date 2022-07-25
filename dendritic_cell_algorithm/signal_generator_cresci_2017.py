import copy
import math
import re
import os
from math import log2

# import enchant
from Levenshtein import distance
import nltk
import json
import scipy.stats
from datetime import date, datetime
import operator
import logging

from dotenv import load_dotenv


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
        load_dotenv(dotenv_path="var.env")

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

        self._cms_bot = float(os.environ['W_PAMP_CSM']) * self._pamp_bot + float(
            os.environ['W_DS_CSM']) * self._danger_signal_bot + \
                        float(os.environ['W_SS_CSM']) * self._safe_signal_bot
        self._cms_bad_intentions = float(os.environ['W_PAMP_CSM']) * self._pamp_bad_intentions + float(os.environ[
                                                                                                           'W_DS_CSM']) * self._danger_signal_bad_intentions + float(
            os.environ['W_SS_CSM']) * self._safe_signal_bad_intentions

        self._cms = self._cms_bot + self._cms_bad_intentions

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

        self._mDC_bot = max(float(os.environ['W_PAMP_MDC']) * self._pamp_bot + float(
            os.environ['W_DS_MDC']) * self._danger_signal_bot + \
                            float(os.environ['W_SS_MDC']) * self._safe_signal_bot, 0)
        self._mDC_bad_intentions = max(float(os.environ['W_PAMP_MDC']) * self._pamp_bad_intentions + float(
            os.environ['W_DS_MDC']) * self._danger_signal_bad_intentions + float(
            os.environ['W_SS_MDC']) * self._safe_signal_bad_intentions, 0)

        self._mDC = self._mDC_bot + self._mDC_bad_intentions
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

        self._smDC_bot = float(os.environ['W_PAMP_SMDC']) * self._pamp_bot + float(os.environ[
                                                                                       'W_DS_SMDC']) * self._danger_signal_bot + \
                         float(os.environ['W_SS_SMDC']) * self._safe_signal_bot
        self._smDC_bad_intentions = float(os.environ['W_PAMP_SMDC']) * self._pamp_bad_intentions + float(os.environ[
                                                                                                             'W_DS_SMDC']) * self._danger_signal_bad_intentions + \
                                    float(os.environ['W_SS_SMDC']) * self._safe_signal_bad_intentions

        self._smDC = self._smDC_bot + self._smDC_bad_intentions

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
                         tweets,
                         crawled_at = "2014-12-31 23:59:59"):
        """
        if len(tweets) > 40:
            tweets = tweets[:40]
        """
        logging.info("Check default_profile")
        self.increase_danger_signal(float(os.environ["DEFAULT_PROFILE_DS_MULTIPLIER"]) * float(default_profile), True,
                                    False,
                                    "default_profile")
        self.increase_safe_signal(float(os.environ["DEFAULT_PROFILE_SS_MULTIPLIER"]) * (1 - float(default_profile)),
                                  True,
                                  False,
                                  "default_profile")

        logging.info("Check default_profile_image")
        self.increase_danger_signal(
            float(os.environ["DEFAULT_PROFILE_IMAGE_DS_MULTIPLIER"]) * float(default_profile_image),
            True, False, "default_profile_image")
        self.increase_safe_signal(
            float(os.environ["DEFAULT_PROFILE_IMAGE_SS_MULTIPLIER"]) * (1 - float(default_profile_image)),
            True, False, "default_profile_image")

        self.increase_safe_signal(float(os.environ['VERIFIED_SS_MULTIPLIER']) * float(verified), False, True,
                                  "verified")

        name_screen_name_similarity = similarity(name, screen_name)
        # self.increase_danger_signal(determine_signal_strength(name_screen_name_similarity, ">=", 0.9, 0.05))

        screen_name_length = len(screen_name)
        # self.increase_danger_signal(determine_signal_strength(screen_name_length, ">=", 13, 2))

        identifies_itself_as_bot = contains_bot_info(description)
        self.increase_safe_signal(
            float(os.environ["SS_MULTIPLIER_IDENTIFIES_ITSELF_AS_BOT"]) * float(identifies_itself_as_bot),
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

        user_age = (datetime.strptime(crawled_at.replace(" +0000", ""), '%Y-%m-%d %X') - datetime.strptime(created_at.replace(" +0000", ""), '%c')).days

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

        array_counter = 0

        avg_tweet_similarity = None
        small_interval_between_tweets_count = None
        time_entropy = None
        retweet_tweet_ratio, url_tweet_ratio, user_mentions_tweet_ratio, hashtag_tweet_ratio, average_favorite_count, average_retweet_count, is_sensitive_count = None, None, None, None, None, None, None

        if len(tweets) > int(float(os.environ["TWEETS_ARRAYS_LIMIT"])):
            tweets = tweets[:int(float(os.environ["TWEETS_ARRAYS_LIMIT"]))]

        while len(tweets) / 20 >= array_counter:
            # print(array_counter)

            if len(tweets[20 * array_counter:20 * (array_counter + 1)]) > 10:
                avg_tweet_similarity_i = average_tweet_similarity(
                    tweets[20 * array_counter:20 * (array_counter + 1)])  # nltk.edit_distance()
                if avg_tweet_similarity is None or avg_tweet_similarity_i > avg_tweet_similarity:
                    avg_tweet_similarity = avg_tweet_similarity_i
                logging.info("Check avg_tweet_similarity")

            if len(tweets[20 * array_counter:20 * (array_counter + 1)]) > 10:
                time_entropy_i = tweeting_time_entropy(
                    tweets[20 * array_counter:20 * (array_counter + 1)])  # scipy.stats.entropy()
                if time_entropy is None or time_entropy_i < time_entropy:
                    time_entropy = time_entropy_i
                logging.info("Check entropy:")

                small_interval_between_tweets_count_i = calculate_small_intervals(
                    tweets[20 * array_counter:20 * (array_counter + 1)])

                if small_interval_between_tweets_count is None or small_interval_between_tweets_count_i < small_interval_between_tweets_count:
                    small_interval_between_tweets_count = small_interval_between_tweets_count_i

            if len(tweets[20 * array_counter:20 * (array_counter + 1)]) > 10:
                retweet_tweet_ratio_i, url_tweet_ratio_i, user_mentions_tweet_ratio_i, hashtag_tweet_ratio_i, average_favorite_count_i, average_retweet_count_i, is_sensitive_count_i = calculate_tweet_parameters(
                    tweets[20 * array_counter:20 * (array_counter + 1)])

                if retweet_tweet_ratio is None or retweet_tweet_ratio_i > retweet_tweet_ratio:
                    retweet_tweet_ratio = retweet_tweet_ratio_i

                if url_tweet_ratio is None or url_tweet_ratio_i > url_tweet_ratio:
                    url_tweet_ratio = url_tweet_ratio_i

                if user_mentions_tweet_ratio is None or user_mentions_tweet_ratio_i > user_mentions_tweet_ratio:
                    user_mentions_tweet_ratio = user_mentions_tweet_ratio_i

                if hashtag_tweet_ratio is None or hashtag_tweet_ratio_i > hashtag_tweet_ratio:
                    hashtag_tweet_ratio = hashtag_tweet_ratio_i

                if average_favorite_count is None or average_favorite_count_i < average_favorite_count:
                    average_favorite_count = average_favorite_count_i

                if average_retweet_count is None or average_retweet_count_i < average_retweet_count:
                    average_retweet_count = average_retweet_count_i

                if is_sensitive_count is None or is_sensitive_count_i < is_sensitive_count:
                    is_sensitive_count = is_sensitive_count_i

            array_counter += 1

        if len(tweets) > int(float(os.environ["MULTIPLIER_LEN_TWEETS"])):
            tweets = tweets[:int(float(os.environ["MULTIPLIER_LEN_TWEETS"]))]

        if avg_tweet_similarity is not None:
            self.increase_pamp(min(determine_signal_strength(avg_tweet_similarity, ">",
                                                             float(os.environ["PAMP_THRESHOLD_AVG_TWEET_SIMILARITY"]),
                                                             float(os.environ["PAMP_INTERVAL_AVG_TWEET_SIMILARITY"])),
                                   float(os.environ["PAMP_UPPER_BOUND_AVG_TWEET_SIMILARITY"]) * len(tweets)),
                               True, False, "avg_tweet_similarity")

            self.increase_safe_signal(determine_signal_strength(avg_tweet_similarity, "<",
                                                                float(os.environ["SS_THRESHOLD_AVG_TWEET_SIMILARITY"]),
                                                                float(os.environ["SS_INTERVAL_AVG_TWEET_SIMILARITY"])),
                                      True, False, "avg_tweet_similarity")

            self.increase_pamp(float(os.environ["PAMP_MULTIPLIER_SMALL_INTERVAL"]) * determine_signal_strength(
                small_interval_between_tweets_count, ">",
                float(os.environ["PAMP_THRESHOLD_SMALL_INTERVAL"]),
                float(os.environ["PAMP_INTERVAL_SMALL_INTERVAL"])),
                               True, False, "small_interval_between_tweets_count")

        if time_entropy is not None:
            self.increase_pamp(
                min(float(os.environ["PAMP_MULTIPLIER_TIME_ENTROPY"]) * determine_signal_strength(time_entropy, "<",
                                                                                                  float(os.environ[
                                                                                                            "PAMP_THRESHOLD_TIME_ENTROPY"]) + len(
                                                                                                      tweets) / 20,
                                                                                                  float(os.environ[
                                                                                                            "PAMP_INTERVAL_TIME_ENTROPY"])),
                    float(os.environ["PAMP_UPPER_BOUND_TIME_ENTROPY"]) * len(tweets)),
                True, False, "time_entropy")

            self.increase_safe_signal(
                min(float(os.environ["SS_MULTIPLIER_TIME_ENTROPY"]) * determine_signal_strength(time_entropy, ">",
                                                                                                float(os.environ[
                                                                                                          "SS_THRESHOLD_TIME_ENTROPY"]) + len(
                                                                                                    tweets) / 20,
                                                                                                float(os.environ[
                                                                                                          "SS_INTERVAL_TIME_ENTROPY"])),
                    float(os.environ["SS_UPPER_BOUND_TIME_ENTROPY"]) * len(tweets)),
                True, False, "time_entropy")

        if retweet_tweet_ratio is not None:
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

            self.increase_safe_signal(min(determine_signal_strength(average_retweet_count, ">=",
                                                                    float(os.environ[
                                                                              "SS_THRESHOLD_AVERAGE_RETWEET_COUNT"]),
                                                                    float(os.environ[
                                                                              "SS_INTERVAL_AVERAGE_RETWEET_COUNT"])),
                                          float(os.environ["SS_UPPER_BOUND_BASIC_RATIO"]) * len(tweets)),
                                      False, True, "average_retweet_count")

            self.increase_danger_signal(
                min(determine_signal_strength(average_favorite_count, "<=",
                                              float(os.environ["DS_THRESHOLD_AVERAGE_FAVORITE_COUNT"]),
                                              float(os.environ["DS_INTERVAL_AVERAGE_FAVORITE_COUNT"])),
                    float(os.environ["DS_UPPER_BOUND_BASIC_RATIO"]) * len(tweets)),
                False, True, "average_retweet_count")

            self.increase_safe_signal(min(determine_signal_strength(average_favorite_count, ">=",
                                                                    float(os.environ[
                                                                              "SS_THRESHOLD_AVERAGE_FAVORITE_COUNT"]),
                                                                    float(os.environ[
                                                                              "SS_INTERVAL_AVERAGE_FAVORITE_COUNT"])),
                                          float(os.environ["SS_UPPER_BOUND_BASIC_RATIO"]) * len(tweets)),
                                      False, True, "average_retweet_count")

            self.increase_pamp(float(os.environ["PAMP_MULTIPLIER_IS_SENSITIVE_COUNT"]) * is_sensitive_count,
                               False, True, "malicious links")

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
        self.update_parameters("average_favorite_count", average_favorite_count)
        self.update_parameters("average_retweet_count", average_retweet_count)
        self.update_parameters("is_sensitive_count", is_sensitive_count)
        self.update_parameters("name_screen_name_similarity", name_screen_name_similarity)
        self.update_parameters("screen_name_length", screen_name_length)
        self.update_parameters("identifies_itself_as_bot", identifies_itself_as_bot)
        self.update_parameters("followers_friends_ratio", followers_friends_ratio)
        self.update_parameters("statuses_growth_rate", statuses_growth_rate)
        self.update_parameters("friends_growth_rate", friends_growth_rate)

    #######################################################################################
    #######################################################################################
    #######################################################################################

    def generate_signals_avg(self, friends_count,
                             statuses_count,
                             followers_count,
                             verified,
                             default_profile,
                             default_profile_image,
                             created_at,
                             name,
                             screen_name,
                             description,
                             tweets,
                             crawled_at = "2014-12-31 23:59:59"):
        """
        if len(tweets) > 40:
            tweets = tweets[:40]
        """
        logging.info("Check default_profile")
        self.increase_danger_signal(float(os.environ["DEFAULT_PROFILE_DS_MULTIPLIER"]) * float(default_profile), True,
                                    False,
                                    "default_profile")
        self.increase_safe_signal(float(os.environ["DEFAULT_PROFILE_SS_MULTIPLIER"]) * (1 - float(default_profile)),
                                  True,
                                  False,
                                  "default_profile")

        logging.info("Check default_profile_image")
        self.increase_danger_signal(
            float(os.environ["DEFAULT_PROFILE_IMAGE_DS_MULTIPLIER"]) * float(default_profile_image),
            True, False, "default_profile_image")
        self.increase_safe_signal(
            float(os.environ["DEFAULT_PROFILE_IMAGE_SS_MULTIPLIER"]) * (1 - float(default_profile_image)),
            True, False, "default_profile_image")

        self.increase_safe_signal(float(os.environ['VERIFIED_SS_MULTIPLIER']) * float(verified), False, True,
                                  "verified")

        name_screen_name_similarity = similarity(name, screen_name)
        # self.increase_danger_signal(determine_signal_strength(name_screen_name_similarity, ">=", 0.9, 0.05))

        screen_name_length = len(screen_name)
        # self.increase_danger_signal(determine_signal_strength(screen_name_length, ">=", 13, 2))

        identifies_itself_as_bot = contains_bot_info(description)
        self.increase_safe_signal(
            float(os.environ["SS_MULTIPLIER_IDENTIFIES_ITSELF_AS_BOT"]) * float(identifies_itself_as_bot),
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

        user_age = (datetime.strptime(crawled_at.replace(" +0000", ""), '%Y-%m-%d %X') - datetime.strptime(created_at.replace(" +0000", ""), '%c')).days

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

        array_counter = 0

        avg_tweet_similarity = None
        small_interval_between_tweets_count = None
        time_entropy = None
        retweet_tweet_ratio, url_tweet_ratio, user_mentions_tweet_ratio, hashtag_tweet_ratio, average_favorite_count, average_retweet_count, is_sensitive_count = None, None, None, None, None, None, None
        avg_tweet_similarity_array = []
        small_interval_between_tweets_count_array = []
        time_entropy_array = []
        retweet_tweet_ratio_array, url_tweet_ratio_array, user_mentions_tweet_ratio_array, hashtag_tweet_ratio_array, average_favorite_count_array, average_retweet_count_array, is_sensitive_count_array = [], [], [], [], [], [], []

        if len(tweets) > int(float(os.environ["TWEETS_ARRAYS_LIMIT"])):
            tweets = tweets[:int(float(os.environ["TWEETS_ARRAYS_LIMIT"]))]

        while len(tweets) / 20 >= array_counter:
            # print(array_counter)

            if len(tweets[20 * array_counter:20 * (array_counter + 1)]) > 10:
                avg_tweet_similarity_i = average_tweet_similarity(
                    tweets[20 * array_counter:20 * (array_counter + 1)])  # nltk.edit_distance()

                avg_tweet_similarity_array[array_counter] = avg_tweet_similarity_i
                logging.info("Check avg_tweet_similarity")

            if len(tweets[20 * array_counter:20 * (array_counter + 1)]) > 10:
                time_entropy_i = tweeting_time_entropy(
                    tweets[20 * array_counter:20 * (array_counter + 1)])  # scipy.stats.entropy()

                time_entropy_array[array_counter] = time_entropy_i
                logging.info("Check entropy:")

                small_interval_between_tweets_count_i = calculate_small_intervals(
                    tweets[20 * array_counter:20 * (array_counter + 1)])
                small_interval_between_tweets_count_array[array_counter] = small_interval_between_tweets_count_i

            if len(tweets[20 * array_counter:20 * (array_counter + 1)]) > 10:
                retweet_tweet_ratio_i, url_tweet_ratio_i, user_mentions_tweet_ratio_i, hashtag_tweet_ratio_i, average_favorite_count_i, average_retweet_count_i, is_sensitive_count_i = calculate_tweet_parameters(
                    tweets[20 * array_counter:20 * (array_counter + 1)])

                retweet_tweet_ratio_array[array_counter] = retweet_tweet_ratio_i

                url_tweet_ratio_array[array_counter] = url_tweet_ratio_i

                user_mentions_tweet_ratio_array[array_counter] = user_mentions_tweet_ratio_i

                hashtag_tweet_ratio_array[array_counter] = hashtag_tweet_ratio_i

                average_favorite_count_array[array_counter] = average_favorite_count_i

                average_retweet_count_array[array_counter] = average_retweet_count_i

                is_sensitive_count_array[array_counter] = is_sensitive_count_i

            array_counter += 1

        if time_entropy_array is not None:

            time_entropy = sum(time_entropy_array) / len(time_entropy_array)

        if small_interval_between_tweets_count_array is not None:

            small_interval_between_tweets_count = sum(small_interval_between_tweets_count_array) / len(
                small_interval_between_tweets_count_array)

        if avg_tweet_similarity_array is not None:

            avg_tweet_similarity = sum(avg_tweet_similarity_array) / len(avg_tweet_similarity_array)

        if retweet_tweet_ratio_array is not None:

            retweet_tweet_ratio = sum(retweet_tweet_ratio_array) / len(retweet_tweet_ratio_array)

        if url_tweet_ratio_array is not None:

            url_tweet_ratio = sum(url_tweet_ratio_array) / len(url_tweet_ratio_array)

        if user_mentions_tweet_ratio_array is not None:

            user_mentions_tweet_ratio = sum(user_mentions_tweet_ratio_array) / len(user_mentions_tweet_ratio_array)

        if hashtag_tweet_ratio_array is not None:

            hashtag_tweet_ratio = sum(hashtag_tweet_ratio_array) / len(hashtag_tweet_ratio_array)

        if average_favorite_count_array is not None:

            average_favorite_count = sum(average_favorite_count_array) / len(average_favorite_count_array)

        if average_retweet_count_array is not None:

            average_retweet_count = sum(average_retweet_count_array) / len(average_retweet_count_array)

        if is_sensitive_count_array is not None:

            is_sensitive_count = sum(is_sensitive_count_array) / len(is_sensitive_count_array)

        if len(tweets) > int(float(os.environ["MULTIPLIER_LEN_TWEETS"])):
            tweets = tweets[:int(float(os.environ["MULTIPLIER_LEN_TWEETS"]))]

        if avg_tweet_similarity is not None:
            self.increase_pamp(min(determine_signal_strength(avg_tweet_similarity, ">",
                                                             float(os.environ["PAMP_THRESHOLD_AVG_TWEET_SIMILARITY"]),
                                                             float(os.environ["PAMP_INTERVAL_AVG_TWEET_SIMILARITY"])),
                                   float(os.environ["PAMP_UPPER_BOUND_AVG_TWEET_SIMILARITY"]) * len(tweets)),
                               True, False, "avg_tweet_similarity")

            self.increase_safe_signal(determine_signal_strength(avg_tweet_similarity, "<",
                                                                float(os.environ["SS_THRESHOLD_AVG_TWEET_SIMILARITY"]),
                                                                float(os.environ["SS_INTERVAL_AVG_TWEET_SIMILARITY"])),
                                      True, False, "avg_tweet_similarity")

            self.increase_pamp(float(os.environ["PAMP_MULTIPLIER_SMALL_INTERVAL"]) * determine_signal_strength(
                small_interval_between_tweets_count, ">",
                float(os.environ["PAMP_THRESHOLD_SMALL_INTERVAL"]),
                float(os.environ["PAMP_INTERVAL_SMALL_INTERVAL"])),
                               True, False, "small_interval_between_tweets_count")

        if time_entropy is not None:
            self.increase_pamp(
                min(float(os.environ["PAMP_MULTIPLIER_TIME_ENTROPY"]) * determine_signal_strength(time_entropy, "<",
                                                                                                  float(os.environ[
                                                                                                            "PAMP_THRESHOLD_TIME_ENTROPY"]) + len(
                                                                                                      tweets) / 20,
                                                                                                  float(os.environ[
                                                                                                            "PAMP_INTERVAL_TIME_ENTROPY"])),
                    float(os.environ["PAMP_UPPER_BOUND_TIME_ENTROPY"]) * len(tweets)),
                True, False, "time_entropy")

            self.increase_safe_signal(
                min(float(os.environ["SS_MULTIPLIER_TIME_ENTROPY"]) * determine_signal_strength(time_entropy, ">",
                                                                                                float(os.environ[
                                                                                                          "SS_THRESHOLD_TIME_ENTROPY"]) + len(
                                                                                                    tweets) / 20,
                                                                                                float(os.environ[
                                                                                                          "SS_INTERVAL_TIME_ENTROPY"])),
                    float(os.environ["SS_UPPER_BOUND_TIME_ENTROPY"]) * len(tweets)),
                True, False, "time_entropy")

        if retweet_tweet_ratio is not None:
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

            self.increase_safe_signal(min(determine_signal_strength(average_retweet_count, ">=",
                                                                    float(os.environ[
                                                                              "SS_THRESHOLD_AVERAGE_RETWEET_COUNT"]),
                                                                    float(os.environ[
                                                                              "SS_INTERVAL_AVERAGE_RETWEET_COUNT"])),
                                          float(os.environ["SS_UPPER_BOUND_BASIC_RATIO"]) * len(tweets)),
                                      False, True, "average_retweet_count")

            self.increase_danger_signal(
                min(determine_signal_strength(average_favorite_count, "<=",
                                              float(os.environ["DS_THRESHOLD_AVERAGE_FAVORITE_COUNT"]),
                                              float(os.environ["DS_INTERVAL_AVERAGE_FAVORITE_COUNT"])),
                    float(os.environ["DS_UPPER_BOUND_BASIC_RATIO"]) * len(tweets)),
                False, True, "average_retweet_count")

            self.increase_safe_signal(min(determine_signal_strength(average_favorite_count, ">=",
                                                                    float(os.environ[
                                                                              "SS_THRESHOLD_AVERAGE_FAVORITE_COUNT"]),
                                                                    float(os.environ[
                                                                              "SS_INTERVAL_AVERAGE_FAVORITE_COUNT"])),
                                          float(os.environ["SS_UPPER_BOUND_BASIC_RATIO"]) * len(tweets)),
                                      False, True, "average_retweet_count")

            self.increase_pamp(float(os.environ["PAMP_MULTIPLIER_IS_SENSITIVE_COUNT"]) * is_sensitive_count,
                               False, True, "malicious links")

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
        self.update_parameters("average_favorite_count", average_favorite_count)
        self.update_parameters("average_retweet_count", average_retweet_count)
        self.update_parameters("is_sensitive_count", is_sensitive_count)
        self.update_parameters("name_screen_name_similarity", name_screen_name_similarity)
        self.update_parameters("screen_name_length", screen_name_length)
        self.update_parameters("identifies_itself_as_bot", identifies_itself_as_bot)
        self.update_parameters("followers_friends_ratio", followers_friends_ratio)
        self.update_parameters("statuses_growth_rate", statuses_growth_rate)
        self.update_parameters("friends_growth_rate", friends_growth_rate)

    #######################################################################################
    #######################################################################################
    #######################################################################################

    def generate_signals_k(self, friends_count,
                           statuses_count,
                           followers_count,
                           verified,
                           default_profile,
                           default_profile_image,
                           created_at,
                           name,
                           screen_name,
                           description,
                           tweets,
                           k,
                           crawled_at = "2014-12-31 23:59:59"):
        if len(tweets) > k:
            tweets = tweets[:k]
        #print(len(tweets))
        logging.info("Check default_profile")
        self.increase_danger_signal(float(os.environ["DEFAULT_PROFILE_DS_MULTIPLIER"]) * float(default_profile), True,
                                    False,
                                    "default_profile")
        self.increase_safe_signal(float(os.environ["DEFAULT_PROFILE_SS_MULTIPLIER"]) * (1 - float(default_profile)),
                                  True,
                                  False,
                                  "default_profile")

        logging.info("Check default_profile_image")
        self.increase_danger_signal(
            float(os.environ["DEFAULT_PROFILE_IMAGE_DS_MULTIPLIER"]) * float(default_profile_image),
            True, False, "default_profile_image")
        self.increase_safe_signal(
            float(os.environ["DEFAULT_PROFILE_IMAGE_SS_MULTIPLIER"]) * (1 - float(default_profile_image)),
            True, False, "default_profile_image")

        self.increase_safe_signal(float(os.environ['VERIFIED_SS_MULTIPLIER']) * float(verified), False, True,
                                  "verified")

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

            small_interval_between_tweets_count = calculate_small_intervals(tweets)

            self.increase_pamp(float(os.environ["PAMP_MULTIPLIER_SMALL_INTERVAL"]) * determine_signal_strength(
                small_interval_between_tweets_count, ">",
                float(os.environ["PAMP_THRESHOLD_SMALL_INTERVAL"]),
                float(os.environ["PAMP_INTERVAL_SMALL_INTERVAL"])),
                               True, False, "small_interval_between_tweets_count")

        else:
            avg_tweet_similarity = None
            small_interval_between_tweets_count = None

        if len(tweets) > 5:
            time_entropy = tweeting_time_entropy(tweets)  # scipy.stats.entropy()
            logging.info("Check entropy:")

            self.increase_pamp(
                min(float(os.environ["PAMP_MULTIPLIER_TIME_ENTROPY"]) * determine_signal_strength(time_entropy, "<",
                                                                                                  float(os.environ[
                                                                                                            "PAMP_THRESHOLD_TIME_ENTROPY"]) + len(
                                                                                                      tweets) / 20,
                                                                                                  float(os.environ[
                                                                                                            "PAMP_INTERVAL_TIME_ENTROPY"])),
                    float(os.environ["PAMP_UPPER_BOUND_TIME_ENTROPY"]) * len(tweets)),
                True, False, "time_entropy")

            self.increase_safe_signal(
                min(float(os.environ["SS_MULTIPLIER_TIME_ENTROPY"]) * determine_signal_strength(time_entropy, ">",
                                                                                                float(os.environ[
                                                                                                          "SS_THRESHOLD_TIME_ENTROPY"]) + len(
                                                                                                    tweets) / 20,
                                                                                                float(os.environ[
                                                                                                          "SS_INTERVAL_TIME_ENTROPY"])),
                    float(os.environ["SS_UPPER_BOUND_TIME_ENTROPY"]) * len(tweets)),
                True, False, "time_entropy")

        else:
            time_entropy = None

        if len(tweets) > 3:
            retweet_tweet_ratio, url_tweet_ratio, user_mentions_tweet_ratio, hashtag_tweet_ratio, average_favorite_count, average_retweet_count, is_sensitive_count = calculate_tweet_parameters(
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

            self.increase_safe_signal(min(determine_signal_strength(average_retweet_count, ">=",
                                                                    float(os.environ[
                                                                              "SS_THRESHOLD_AVERAGE_RETWEET_COUNT"]),
                                                                    float(os.environ[
                                                                              "SS_INTERVAL_AVERAGE_RETWEET_COUNT"])),
                                          float(os.environ["SS_UPPER_BOUND_BASIC_RATIO"]) * len(tweets)),
                                      False, True, "average_retweet_count")

            self.increase_danger_signal(
                min(determine_signal_strength(average_favorite_count, "<=",
                                              float(os.environ["DS_THRESHOLD_AVERAGE_FAVORITE_COUNT"]),
                                              float(os.environ["DS_INTERVAL_AVERAGE_FAVORITE_COUNT"])),
                    float(os.environ["DS_UPPER_BOUND_BASIC_RATIO"]) * len(tweets)),
                False, True, "average_retweet_count")

            self.increase_safe_signal(min(determine_signal_strength(average_favorite_count, ">=",
                                                                    float(os.environ[
                                                                              "SS_THRESHOLD_AVERAGE_FAVORITE_COUNT"]),
                                                                    float(os.environ[
                                                                              "SS_INTERVAL_AVERAGE_FAVORITE_COUNT"])),
                                          float(os.environ["SS_UPPER_BOUND_BASIC_RATIO"]) * len(tweets)),
                                      False, True, "average_retweet_count")

            self.increase_pamp(float(os.environ["PAMP_MULTIPLIER_IS_SENSITIVE_COUNT"]) * is_sensitive_count,
                               False, True, "malicious links")

        else:
            retweet_tweet_ratio, url_tweet_ratio, user_mentions_tweet_ratio, hashtag_tweet_ratio, average_favorite_count, average_retweet_count, is_sensitive_count = None, None, None, None, None, None, None

        name_screen_name_similarity = similarity(name, screen_name)
        # self.increase_danger_signal(determine_signal_strength(name_screen_name_similarity, ">=", 0.9, 0.05))

        screen_name_length = len(screen_name)
        # self.increase_danger_signal(determine_signal_strength(screen_name_length, ">=", 13, 2))

        identifies_itself_as_bot = contains_bot_info(description)
        self.increase_safe_signal(
            float(os.environ["SS_MULTIPLIER_IDENTIFIES_ITSELF_AS_BOT"]) * float(identifies_itself_as_bot),
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

        user_age = (datetime.strptime(crawled_at.replace(" +0000", ""), '%Y-%m-%d %X') - datetime.strptime(created_at.replace(" +0000", ""), '%c')).days

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
        self.update_parameters("average_favorite_count", average_favorite_count)
        self.update_parameters("average_retweet_count", average_retweet_count)
        self.update_parameters("is_sensitive_count", is_sensitive_count)
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
                tweet_similarity = similarity(tweets[i]["text"], tweets[j]["text"])
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
    logging.info(f"average tweet similarity: {avg_tweet_similarity}")
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
    levenshtein_distance = distance(string1, string2)
    if max_length > 0:
        similarity_metric = ((max_length - levenshtein_distance) / max_length)
    else:
        similarity_metric = 1
    return similarity_metric


def tweeting_time_entropy(tweets):
    created_at = []
    for tweet in tweets:
        try:
            time = datetime.strptime(tweet["created_at"].replace(" +0000", ""),
                                     '%a %b %d %H:%M:%S %Y')  # Mon Dec 13 04:16:58 +0000 2021
        except:
            try:
                time = datetime.strptime(tweet["created_at"].replace(" +0000", ""),
                                         '%Y-%m-%d %H:%M:%S')  # 2014-07-29 21:49:47
            except:
                time = "not given"
                print(tweet["created_at"])

        if time != "not given":
            created_at.append(time)
    res = scipy.stats.entropy(calculate_probability(created_at, 1), base=2)
    logging.info(f"entropy: {res}")
    return float(res)


def calculate_small_intervals(tweets):
    created_at = []
    for tweet in tweets:
        # datetime.strptime(tweet["timestamp"].replace(" +0000", ""),
        #                  '%Y-%m-%d %X'))  # Mon Dec 13 04:16:58 +0000 2021
        try:
            time = datetime.strptime(tweet["created_at"].replace(" +0000", ""),
                                     '%a %b %d %H:%M:%S %Y')  # Mon Dec 13 04:16:58 +0000 2021
        except:
            try:
                time = datetime.strptime(tweet["created_at"].replace(" +0000", ""),
                                         '%Y-%m-%d %H:%M:%S')  # 2014-07-29 21:49:47
            except:
                time = "not given"
                print(tweet["created_at"])

        if time != "not given":
            created_at.append(time)

    created_at.sort(reverse=True)
    small_intervals_count = 0
    i = 0
    while i < len(created_at) - 1:
        if (created_at[i] - created_at[i + 1]).total_seconds() < 10:
            small_intervals_count += 1
        i += 1

    logging.info(f"small_intervals_count: {small_intervals_count}")
    return small_intervals_count


def calculate_probability(created_at, measuring_interval):
    created_at.sort(reverse=True)
    intervals = []
    # intervals_seconds = []
    i = 0
    while i < len(created_at) - 1:
        intervals.append(int((created_at[i] - created_at[i + 1]).total_seconds() / 60))
        # intervals_seconds.append(int((created_at[i] - created_at[i + 1]).total_seconds()))
        i += 1
    logging.info(intervals)
    # logging.info(intervals_seconds)
    max_interval = max(intervals)
    min_interval = min(intervals)
    if max_interval == min_interval:
        logging.info("max=min")
        return [1]
    start = int(math.floor(min_interval / measuring_interval) * measuring_interval)
    logging.info("start")
    logging.info(start)
    end = int(math.ceil(max_interval / measuring_interval) * measuring_interval)
    logging.info("end")
    logging.info(end)
    count = int((end - start) / measuring_interval) + 1
    if count == 0:
        logging.info("count=0")
        return [1]
    logging.info("count")
    logging.info(count)
    probability = [0] * count
    for time in intervals:
        logging.info(f'probability[{int((time - start) / measuring_interval)}]')
        probability[int((time - start) / measuring_interval)] += 1
        logging.info(f'OK! probability[{int((time - start) / measuring_interval)}]')

    logging.info([i / len(intervals) for i in probability if i != 0])
    return [i / len(intervals) for i in probability if i != 0]


def determine_signal_strength(value, comparison_sign, threshold, interval):
    ops = {'>': operator.gt,
           '<': operator.lt,
           '>=': operator.ge,
           '<=': operator.le,
           '==': operator.eq}
    signal = 0
    if ops[comparison_sign](value, threshold):
        if interval == 0:
            signal = 1
        else:
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
        if "retweeted_status" in tweet:
            if tweet["retweeted_status"]:
                if tweet["retweeted_status"] != '0':
                    is_retweet_count += 1

        urls_count += tweet["text"].count("http")
        user_mentions_count += tweet["text"].count("@")
        hashtag_count += tweet["text"].count("#")

        try:
            favorite_count += int(tweet["favorite_count"])
            retweet_count += int(tweet["retweet_count"])
        except:
            favorite_count += 0
            retweet_count += 0

        if "possibly_sensitive" in tweet:
            if tweet["possibly_sensitive"]:
                if tweet["possibly_sensitive"] != "NULL":
                    is_sensitive_count += 1

    return is_retweet_count / count, urls_count / count, user_mentions_count / count, hashtag_count / count, favorite_count / count, retweet_count / count, is_sensitive_count


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
