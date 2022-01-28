import os
import sys
import json
import csv
import pprint
import time
import logging

from dotenv import load_dotenv

from signal_generator_cresci_2017 import Signals

from data_preprocessor import cresci_csv_to_json
from data_preprocessor import collect_from_twitter
from dendritic_cell_algorithm import dc_algorithm_cresci_2017

from dendritic_cell_algorithm import dc_algorithm_twibot_2020

import numpy as np
from geneticalgorithm import geneticalgorithm as ga
from dendritic_cell_algorithm import dc_algorithm_cresci_2017 as dca17
from dendritic_cell_algorithm import dc_algorithm_twibot_2020 as dca20


def f(X):
    # 27-8=19
    os.environ['W_PAMP_CSM'] = str(X[0])
    os.environ['W_DS_CSM'] = str(X[1])
    os.environ['W_SS_CSM'] = str(X[2])

    os.environ['W_PAMP_MDC'] = str(X[3])
    os.environ['W_DS_MDC'] = str(X[4])
    os.environ['W_SS_SMDC'] = str(X[5])

    os.environ['DEFAULT_PROFILE_IMAGE_SS_MULTIPLIER'] = str(X[6])
    os.environ['DEFAULT_PROFILE_SS_MULTIPLIER'] = str(X[7])
    os.environ['DEFAULT_PROFILE_DS_MULTIPLIER'] = str(X[8])
    # os.environ['PAMP_MULTIPLIER_SMALL_INTERVAL'] = str(X[9])
    # os.environ['PAMP_MULTIPLIER_TIME_ENTROPY'] = str(X[10])
    # os.environ['SS_MULTIPLIER_TIME_ENTROPY'] = str(X[11])
    os.environ['DS_MULTIPLIER_FRIENDS_GROWTH_RATE'] = str(X[9])
    os.environ['DS_MULTIPLIER_STATUSES_GROWTH_RATE'] = str(X[10])

    os.environ['DS_UPPER_BOUND_FRIENDS_GROWTH_RATE'] = str(X[11])
    # os.environ['SS_UPPER_BOUND_TIME_ENTROPY'] = str(X[15])
    # os.environ['PAMP_UPPER_BOUND_TIME_ENTROPY'] = str(X[16])
    os.environ['PAMP_UPPER_BOUND_AVG_TWEET_SIMILARITY'] = str(X[12])
    os.environ['DS_UPPER_BOUND_BASIC_RATIO'] = str(X[13])
    os.environ['SS_UPPER_BOUND_BASIC_RATIO'] = str(X[14])

    # os.environ['DS_THRESHOLD_HASHTAG_TWEET_RATIO'] = str(X[20])
    os.environ['SS_THRESHOLD_FOLLOWERS_FRIENDS_RATIO'] = str(X[25])
    # os.environ['SS_THRESHOLD_AVERAGE_RETWEET_COUNT'] = str(X[22])
    # os.environ['PAMP_THRESHOLD_SMALL_INTERVAL'] = str(X[23])

    os.environ['SS_INTERVAL_FOLLOWERS_FRIENDS_RATIO'] = str(X[16])
    os.environ['DS_INTERVAL_FRIENDS_GROWTH_RATE'] = str(X[17])
    os.environ['DS_INTERVAL_STATUSES_GROWTH_RATE'] = str(X[18])
    # 9-5=4
    os.environ['SS_UPPER_BOUND_FOLLOWERS_FRIENDS_RATIO'] = str(X[19])

    # os.environ['VERIFIED_SS_MULTIPLIER'] = str(X[28])
    os.environ['DEFAULT_PROFILE_IMAGE_DS_MULTIPLIER'] = str(X[20])
    # os.environ['PAMP_MULTIPLIER_IS_SENSITIVE_COUNT'] = str(X[30])

    os.environ['DS_THRESHOLD_FRIENDS_GROWTH_RATE'] = str(X[21])
    os.environ['DS_THRESHOLD_STATUSES_GROWTH_RATE'] = str(X[22])
    # os.environ['SS_THRESHOLD_AVERAGE_FAVORITE_COUNT'] = str(X[33])

    # os.environ['SS_INTERVAL_AVERAGE_RETWEET_COUNT'] = str(X[34])
    # os.environ['SS_INTERVAL_AVERAGE_FAVORITE_COUNT'] = str(X[35])
    # 1
    # os.environ['SS_MULTIPLIER_IDENTIFIES_ITSELF_AS_BOT'] = str(X[36])
    # 1
    os.environ['W_SS_MDC'] = str(X[23])
    # 2
    # os.environ['W_PAMP_SMDC'] = str(X[38])
    # os.environ['W_DS_SMDC'] = str(X[39])
    # 1
    # os.environ['SS_UPPER_BOUND_AVG_TWEET_SIMILARITY'] = str(X[40])
    # 2
    # os.environ['PAMP_THRESHOLD_TIME_ENTROPY'] = str(X[41])
    # os.environ['SS_THRESHOLD_TIME_ENTROPY'] = str(X[42])

    # 16 - 8 =8
    os.environ['PAMP_THRESHOLD_AVG_TWEET_SIMILARITY'] = str(X[24])
    os.environ['PAMP_INTERVAL_AVG_TWEET_SIMILARITY'] = str(X[25])
    os.environ['SS_THRESHOLD_AVG_TWEET_SIMILARITY'] = str(X[26])
    os.environ['SS_INTERVAL_AVG_TWEET_SIMILARITY'] = str(X[27])
    # os.environ['PAMP_INTERVAL_SMALL_INTERVAL'] = str(X[47])
    # os.environ['PAMP_INTERVAL_TIME_ENTROPY'] = str(X[48])
    # os.environ['SS_INTERVAL_TIME_ENTROPY'] = str(X[49])
    os.environ['DS_THRESHOLD_BASIC_RATIO'] = str(X[28])
    os.environ['DS_INTERVAL_BASIC_RATIO'] = str(X[29])
    os.environ['SS_THRESHOLD_BASIC_RATIO'] = str(X[30])
    os.environ['SS_INTERVAL_BASIC_RATIO'] = str(X[31])
    # os.environ['DS_INTERVAL_HASHTAG_TWEET_RATIO'] = str(X[54])
    # os.environ['SS_THRESHOLD_HASHTAG_TWEET_RATIO'] = str(X[55])
    # os.environ['SS_INTERVAL_HASHTAG_TWEET_RATIO'] = str(X[56])
    # os.environ['DS_THRESHOLD_AVERAGE_FAVORITE_COUNT'] = str(X[57])
    # os.environ['DS_INTERVAL_AVERAGE_FAVORITE_COUNT'] = str(X[58])

    print(str(os.environ)[2912:])
    result = dca20("../datasets/twibot-2020/test.json")
    res = json.loads(result)

    classified_count = res.pop("classified_count")
    classified_correctly_count = res.pop("classified_correctly_count")
    accuracy = classified_correctly_count / classified_count
    print("\nAccuracy = {0}/{1} = {2} \n".format(classified_correctly_count, classified_count, accuracy))
    print(1 - accuracy)
    time = res.pop("time")
    print("Time: {0} \n".format(time))
    return 1 - accuracy


"""varbound = np.concatenate((np.full((27, 2), [1, 10]), np.full((9, 2), [5, 40]), np.full((1, 2), [0, 60]),
                           np.full((1, 2), [-10, -1]), np.full((2, 2), [0, 0]), np.full((1, 2), [1000, 1000]),
                           np.full((1, 2), [1, 2]), np.full((1, 2), [2, 3]), np.full((16, 2), [0, 1])),
                          axis=0)

vartype = np.concatenate((np.full((41, 1), 'int'), np.full((18, 1), 'real')),
                         axis=0)"""
load_dotenv()

varbound = np.concatenate((np.full((19, 2), [1, 10]), np.full((4, 2), [5, 40]),
                           np.full((1, 2), [-10, -1]),
                           np.full((8, 2), [0, 1])),
                          axis=0)

vartype = np.concatenate((np.full((24, 1), 'int'), np.full((8, 1), 'real')),
                         axis=0)

model = ga(function=f, dimension=32, variable_type_mixed=vartype, variable_boundaries=varbound, function_timeout=36000)

model.run()

"""logging.getLogger().setLevel(logging.INFO)
dc_algorithm_twibot_2020("../datasets/twibot-2020/data_sample.json")"""

"""cresci_csv_to_json('../datasets/cresci-2017/genuine_accounts.csv/')
# collect_from_twitter("covid19", 5, 5)"""

"""csvfile = open('../datasets/cresci-2017/social_spambots_1.csv/tweets.csv', 'r', errors="replace").readlines()
filename = 1
for i in range(len(csvfile)):
    if i % 50000 == 0:
        open(str(filename) + '.csv', 'w+').writelines(csvfile[i:i + 50000])
        filename += 1"""

"""
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()
sentence = "The food was bad!"
sentiment = analyzer.polarity_scores(sentence)
logging.info(sentence)
logging.info(sentiment['compound'])

if sentiment['compound'] >= 0.05:
    logging.info("Positive")

elif sentiment['compound'] <= - 0.05:
    logging.info("Negative")

else:
    logging.info("Neutral")
    """

"""pp = pprint.PrettyPrinter(indent=4, sort_dicts=False)

f = open('../datasets/cresci-2017/traditional_spambots_1.csv/result.json', 'r', encoding="cp850")

# Reading from file
data = json.loads(f.read())"""

# Iterating through the json
# list
"""for user in data['users']:
    logging.info(user["default_profile"])
    s = Signals()
    s.generate_signals(int(user["friends_count"]), int(user["statuses_count"]), int(user["followers_count"]),
                       user["verified"] if (str(user["verified"]) == "NULL" and str(user["verified"]) == "") else False,
                       user["default_profile"] if (str(user["default_profile"]) != "NULL" and str(user["default_profile"]) != "") else False,
                       user["default_profile_image"] if (str(user["default_profile_image"]) != "NULL" and str(user["default_profile_image"]) != "") else False,
                       user["timestamp"], user["name"],
                       user["screen_name"], user["description"], user["tweets"])

    pp.pprint(s.get_k())
    pp.pprint(user["id"])"""
"""start = time.time()
time.sleep(1)
end = time.time()
logging.getLogger().setLevel(logging.DEBUG)
logging.info('%s sec', str(int((end - start)/60)) + ":" + str(int((end - start) - int((end - start)/60))))

os.environ['AAA'] = 'aaa'
logging.info(os.environ['AAA'])
os.environ['AAA'] = 'bbb'
logging.info(os.environ['AAA'])
"""
