import copy
import math
import re
from math import log2

import nltk
import json
import scipy.stats
from datetime import date, datetime
import operator


class Signals:
    def __init__(self):
        self._is_bot_probability = 0
        self._intentions_are_bad_probability = 0
        self._pamp = 0
        self._danger_signal = 0
        self._safe_signal = 0
        self._cms = 0
        self._mDC = 0
        self._smDC = 0
        self._k = 0
        self._parameters = {}

    def get_pamp(self):
        return self._pamp

    def increase_pamp(self, x):
        self._pamp += x
        print(f"PAMP + {x}")

    def get_danger_signal(self):
        return self._danger_signal

    def increase_danger_signal(self, x):
        self._danger_signal += x
        print(f"Danger Signal + {x}")

    def get_is_bot_probability(self):
        return self._is_bot_probability

    def increase_is_bot_probability(self, x):
        self._is_bot_probability += x
        print(f"Is bot probability + {x}")

    def get_intentions_are_bad_probability(self):
        return self._intentions_are_bad_probability

    def increase_intentions_are_bad_probability(self, x):
        self._intentions_are_bad_probability += x
        print(f"Intentions are bad probability + {x}")

    def recalculate_probabilities(self):
        self._intentions_are_bad_probability = min(100, self._intentions_are_bad_probability)
        self._is_bot_probability = min(100, self._is_bot_probability)
        print(f"recalculate probabilities + {self._intentions_are_bad_probability}")
        print(f"recalculate probabilities + {self._is_bot_probability}")

    def get_safe_signal(self):
        return self._safe_signal

    def increase_safe_signal(self, x):
        self._safe_signal += x
        print(f"Safe Signal + {x}")

    def get_cms(self):
        return self._cms

    def update_cms(self):
        self._cms = 2 * self._pamp + 1 * self._danger_signal + 2 * self._safe_signal
        print(f"CMS + {self._cms}")

    def get_mDC(self):
        return self._mDC

    def update_mDC(self):
        self._mDC = 2 * self._pamp + 1 * self._danger_signal - 3 * self._safe_signal
        print(f"mDC + {self._mDC}")

    def get_smDC(self):
        return self._smDC

    def update_smDC(self):
        self._smDC = 3 * self._safe_signal
        print(f"smDC + {self._smDC}")

    def get_k(self):
        return self._k

    def update_k(self):
        self._k = self._mDC - self._smDC
        print(f"K + {self._k}")

    def get_parameters(self):
        return self._parameters

    def update_parameters(self, key, value):
        self._parameters[key] = value
        print(f"{key}: {value}")

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
        self.increase_danger_signal(int(default_profile))
        self.increase_danger_signal(int(default_profile_image))

        self.increase_safe_signal(1 - int(default_profile))
        self.increase_safe_signal(1 - int(default_profile_image))
        self.increase_safe_signal(int(verified))

        self.increase_is_bot_probability(int(default_profile))
        self.increase_is_bot_probability(int(default_profile_image))

        self.increase_intentions_are_bad_probability(-20 * int(verified))

        if len(tweets) > 1:
            avg_tweet_similarity = average_tweet_similarity(tweets)  # nltk.edit_distance()
            print("avg_tweet_similarity")
            self.increase_pamp(
                min(4 * determine_signal_strength(avg_tweet_similarity, ">", 0.3, 0.05), 3 * len(tweets)))
            self.increase_safe_signal(determine_signal_strength(avg_tweet_similarity, "<", 0.3, 0.01))

            self.increase_is_bot_probability(
                2*min(4 * determine_signal_strength(avg_tweet_similarity, ">", 0.3, 0.05), 3 * len(tweets)))
            self.increase_is_bot_probability(
                -3 * determine_signal_strength(avg_tweet_similarity, "<", 0.3, 0.01))

        else:
            avg_tweet_similarity = None

        if len(tweets) > 5:
            time_entropy = tweeting_time_entropy(tweets)  # scipy.stats.entropy()
            print("entropy")
            self.increase_pamp(min(4 * determine_signal_strength(time_entropy, "<", 2, 0.1), 3 * len(tweets)))
            self.increase_safe_signal(min(4 * determine_signal_strength(time_entropy, ">", 2.7, 0.01), 3 * len(tweets)))

            self.increase_is_bot_probability(
                2 * min(4 * determine_signal_strength(time_entropy, "<", 2, 0.1), 3 * len(tweets)))
            self.increase_is_bot_probability(
                -3 * min(4 * determine_signal_strength(time_entropy, ">", 2.7, 0.01), 3 * len(tweets)))
        else:
            time_entropy = None

        if len(tweets) > 3:
            retweet_tweet_ratio, quote_tweet_ratio, url_tweet_ratio, user_mentions_tweet_ratio, hashtag_tweet_ratio, average_favorite_count, average_retweet_count, is_sensitive_count = calculate_tweet_parameters(
                tweets)
            self.increase_danger_signal(
                min(determine_signal_strength(max(retweet_tweet_ratio, quote_tweet_ratio), ">", 0.7, 0.01),
                    len(tweets)))
            self.increase_safe_signal(
                determine_signal_strength(max(retweet_tweet_ratio, quote_tweet_ratio), "<", 0.3, 0.2))

            self.increase_danger_signal(min(determine_signal_strength(url_tweet_ratio, ">", 0.7, 0.01), len(tweets)))
            self.increase_safe_signal(determine_signal_strength(url_tweet_ratio, "<", 0.3, 0.2))
            self.increase_danger_signal(
                min(determine_signal_strength(user_mentions_tweet_ratio, ">", 0.7, 0.01), len(tweets)))
            self.increase_safe_signal(determine_signal_strength(user_mentions_tweet_ratio, "<", 0.3, 0.2))
            self.increase_danger_signal(min(determine_signal_strength(hashtag_tweet_ratio, ">=", 3, 0.1), len(tweets)))
            self.increase_safe_signal(determine_signal_strength(hashtag_tweet_ratio, "<=", 0.5, 0.2))
            self.increase_danger_signal(
                min(determine_signal_strength(average_retweet_count, "<=", 0.1, 0.01), len(tweets)))
            self.increase_safe_signal(min(determine_signal_strength(average_retweet_count, ">=", 5, 10), len(tweets)))
            self.increase_danger_signal(
                min(determine_signal_strength(average_favorite_count, "<=", 0.1, 0.01), len(tweets)))
            self.increase_safe_signal(min(determine_signal_strength(average_favorite_count, ">=", 10, 20), len(tweets)))
            self.increase_pamp(5 * is_sensitive_count)

            self.increase_is_bot_probability(
                min(determine_signal_strength(max(retweet_tweet_ratio, quote_tweet_ratio), ">", 0.7, 0.01),
                    len(tweets)))

            self.increase_intentions_are_bad_probability(
                min(determine_signal_strength(url_tweet_ratio, ">", 0.7, 0.05), len(tweets)))
            self.increase_intentions_are_bad_probability(
                -1*determine_signal_strength(url_tweet_ratio, "<", 0.3, 0.2))
            self.increase_intentions_are_bad_probability(
                min(determine_signal_strength(user_mentions_tweet_ratio, ">", 0.7, 0.05), len(tweets)))
            self.increase_intentions_are_bad_probability(
                min(determine_signal_strength(hashtag_tweet_ratio, ">=", 3, 0.1), len(tweets)))

            self.increase_intentions_are_bad_probability(
                min(determine_signal_strength(average_retweet_count, "<=", 0.1, 0.01), len(tweets)))
            self.increase_intentions_are_bad_probability(
                -1*min(determine_signal_strength(average_retweet_count, ">=", 5, 10), len(tweets)))
            self.increase_intentions_are_bad_probability(
                min(determine_signal_strength(average_favorite_count, "<=", 0.1, 0.01), len(tweets)))
            self.increase_intentions_are_bad_probability(
                -1*min(determine_signal_strength(average_favorite_count, ">=", 10, 20), len(tweets)))
            self.increase_intentions_are_bad_probability(5 * is_sensitive_count)

        else:
            retweet_tweet_ratio, quote_tweet_ratio, url_tweet_ratio, user_mentions_tweet_ratio, hashtag_tweet_ratio, average_favorite_count, average_retweet_count, is_sensitive_count = None, None, None, None, None, None, None, None

        name_screen_name_similarity = similarity(name, screen_name)
        self.increase_danger_signal(determine_signal_strength(name_screen_name_similarity, ">=", 0.9, 0.05))

        screen_name_length = len(screen_name)
        self.increase_danger_signal(determine_signal_strength(screen_name_length, ">=", 13, 2))

        identifies_itself_as_bot = contains_bot_info(description)
        self.increase_safe_signal(50 * int(identifies_itself_as_bot))
        self.increase_intentions_are_bad_probability(-50 * int(identifies_itself_as_bot))
        if friends_count > 0:
            followers_friends_ratio = followers_count / friends_count
            self.increase_safe_signal(
                min(determine_signal_strength(followers_friends_ratio, ">=", 5, 5), 5))
            self.increase_is_bot_probability(
                min(determine_signal_strength(followers_friends_ratio, ">=", 5, 5), 5))
        else:
            followers_friends_ratio = None

        user_age = (datetime.now() - datetime.strptime(created_at.replace(" +0000", ""), '%c')).days
        if user_age > 0:
            friends_growth_rate = friends_count / user_age
            statuses_growth_rate = statuses_count / user_age
            print("friends_growth_rate")
            self.increase_danger_signal(
                min(4 * determine_signal_strength(friends_growth_rate, ">=", 10, 2), user_age * 3))
            self.increase_is_bot_probability(
                min(4 * determine_signal_strength(friends_growth_rate, ">=", 10, 2), user_age * 3))
            print("statuses_growth_rate")
            self.increase_danger_signal(2 * determine_signal_strength(statuses_growth_rate, ">=", 20, 5))
            self.increase_is_bot_probability(2 * determine_signal_strength(statuses_growth_rate, ">=", 20, 5))
        else:
            friends_growth_rate = None
            statuses_growth_rate = None
        self.update_cms()
        self.update_mDC()
        self.update_smDC()
        self.update_k()
        self.recalculate_probabilities()
        self.update_parameters("cms", self._cms)
        self.update_parameters("mDC", self._mDC)
        self.update_parameters("smDC", self._smDC)
        self.update_parameters("k", self._k)
        self.update_parameters("is_bot_probability", self._is_bot_probability)
        self.update_parameters("intentions_are_bad_probability", self._intentions_are_bad_probability)
        self.update_parameters("avg_tweet_similarity", avg_tweet_similarity)
        self.update_parameters("time_entropy", time_entropy)
        self.update_parameters("retweet_tweet_ratio", retweet_tweet_ratio)
        self.update_parameters("quote_tweet_ratio", quote_tweet_ratio)
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
    print(f"average tweet similarity: {avg_tweet_similarity}")
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
    created_at = []
    for tweet in tweets:
        created_at.append(
            datetime.strptime(tweet["created_at"].replace(" +0000", ""), '%c'))  # Mon Dec 13 04:16:58 +0000 2021
    res = scipy.stats.entropy(calculate_probability(created_at, 2), base=2)
    print(f"entropy: {res}")
    return float(res)


def calculate_probability(created_at, measuring_interval):
    intervals = []
    i = 0
    while i < len(created_at) - 1:
        intervals.append((created_at[i] - created_at[i + 1]).total_seconds() / 60)
        i += 1
    print(intervals)
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
    is_quote_count = 0
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
                is_retweet_count += 1

        if tweet["is_quote_status"]:
            is_quote_count += 1
        urls_count += len(tweet["entities"]["urls"])
        user_mentions_count += len(tweet["entities"]["user_mentions"])
        hashtag_count += len(tweet["entities"]["hashtags"])
        favorite_count += tweet["favorite_count"]
        retweet_count += tweet["retweet_count"]
        if "possibly_sensitive" in tweet:
            if tweet["possibly_sensitive"]:
                is_sensitive_count += 1

    return is_retweet_count / count, is_quote_count / count, urls_count / count, user_mentions_count / count, hashtag_count / count, favorite_count / count, retweet_count / count, is_sensitive_count


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
