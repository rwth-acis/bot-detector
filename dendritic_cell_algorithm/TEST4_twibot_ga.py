import os
import sys
import json
import csv
import pprint
import time
import logging

import matplotlib
from dotenv import load_dotenv

from signal_generator_cresci_2017 import Signals

from data_preprocessor import cresci_csv_to_json
from data_preprocessor import collect_from_twitter
from dendritic_cell_algorithm import dc_algorithm_cresci_2017

from dendritic_cell_algorithm import dc_algorithm_twibot_2020

import numpy as np
from geneticalgorithm import geneticalgorithm as ga
from dendritic_cell_algorithm import dc_algorithm_cresci_2017 as dca17
from dendritic_cell_algorithm import dc_algorithm_twibot_2020_test as dca20

# JSON file
f = open("../datasets/twibot-2020/train.json", "r", encoding="cp850")

# Reading from file
data = json.loads(f.read())


def f(X):
    # 28-7=21
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

    os.environ['SS_THRESHOLD_HASHTAG_TWEET_RATIO'] = str(X[15])
    os.environ['DS_THRESHOLD_HASHTAG_TWEET_RATIO'] = str(float(int(X[15])+int(X[16])))
    os.environ['SS_THRESHOLD_FOLLOWERS_FRIENDS_RATIO'] = str(X[17])
    # os.environ['SS_THRESHOLD_AVERAGE_RETWEET_COUNT'] = str(X[23])
    # os.environ['PAMP_THRESHOLD_SMALL_INTERVAL'] = str(X[24])

    os.environ['SS_INTERVAL_FOLLOWERS_FRIENDS_RATIO'] = str(X[18])
    os.environ['DS_INTERVAL_FRIENDS_GROWTH_RATE'] = str(X[19])
    os.environ['DS_INTERVAL_STATUSES_GROWTH_RATE'] = str(X[20])

    # 9-5=4
    os.environ['SS_UPPER_BOUND_FOLLOWERS_FRIENDS_RATIO'] = str(X[21])

    os.environ['VERIFIED_SS_MULTIPLIER'] = str(X[22])
    os.environ['DEFAULT_PROFILE_IMAGE_DS_MULTIPLIER'] = str(X[23])
    # os.environ['PAMP_MULTIPLIER_IS_SENSITIVE_COUNT'] = str(X[31])

    os.environ['DS_THRESHOLD_FRIENDS_GROWTH_RATE'] = str(X[24])
    os.environ['DS_THRESHOLD_STATUSES_GROWTH_RATE'] = str(X[25])
    # os.environ['SS_THRESHOLD_AVERAGE_FAVORITE_COUNT'] = str(X[34])

    # os.environ['SS_INTERVAL_AVERAGE_RETWEET_COUNT'] = str(X[35])
    # os.environ['SS_INTERVAL_AVERAGE_FAVORITE_COUNT'] = str(X[36])
    # 1
    os.environ['SS_MULTIPLIER_IDENTIFIES_ITSELF_AS_BOT'] = str(X[26])
    # 1
    os.environ['W_SS_MDC'] = str(X[27])
    # 2
    os.environ['W_PAMP_SMDC'] = str(X[28])
    os.environ['W_DS_SMDC'] = str(X[29])
    # 1
    os.environ['SS_UPPER_BOUND_AVG_TWEET_SIMILARITY'] = str(X[30])
    # 2
    # os.environ['SS_THRESHOLD_TIME_ENTROPY'] = str(int(X[42]))+"."+str(int(X[43]))+str(int(X[44]))
    # os.environ['PAMP_THRESHOLD_TIME_ENTROPY'] = str(float(os.environ['SS_THRESHOLD_TIME_ENTROPY'])-float("0."+str(int(X[45]))+str(int(X[46]))))


    # 16 - 8 =8
    os.environ['SS_THRESHOLD_AVG_TWEET_SIMILARITY'] = "0."+str(int(X[47]))+str(int(X[48]))
    if (float(os.environ['SS_THRESHOLD_AVG_TWEET_SIMILARITY']) + float("0."+str(int(X[49]))+str(int(X[50])))) > 1:
         os.environ['PAMP_THRESHOLD_AVG_TWEET_SIMILARITY'] = "1.0"
    else:
         os.environ['PAMP_THRESHOLD_AVG_TWEET_SIMILARITY'] = str((float(os.environ['SS_THRESHOLD_AVG_TWEET_SIMILARITY']) + float("0."+str(int(X[49]))+str(int(X[50])))))

    os.environ['SS_THRESHOLD_BASIC_RATIO'] = "0."+str(int(X[31]))+str(int(X[32]))
    if (float(os.environ['SS_THRESHOLD_BASIC_RATIO']) + float("0."+str(int(X[33]))+str(int(X[34])))) > 1:
        os.environ['DS_THRESHOLD_BASIC_RATIO'] = "1.0"
    else:
        os.environ['DS_THRESHOLD_BASIC_RATIO'] = str((float(os.environ['SS_THRESHOLD_BASIC_RATIO']) + float("0."+str(int(X[33]))+str(int(X[34])))))


    os.environ['PAMP_INTERVAL_AVG_TWEET_SIMILARITY'] = "0."+str(int(X[35]))+str(int(X[36]))
    os.environ['SS_INTERVAL_AVG_TWEET_SIMILARITY'] = "0."+str(int(X[37]))+str(int(X[38]))
    # os.environ['PAMP_INTERVAL_SMALL_INTERVAL'] = "0."+str(int(X[59]))+str(int(X[60]))
    # os.environ['PAMP_INTERVAL_TIME_ENTROPY'] = "0."+str(int(X[61]))+str(int(X[62]))
    # os.environ['SS_INTERVAL_TIME_ENTROPY'] = "0."+str(int(X[63]))+str(int(X[64]))

    os.environ['DS_INTERVAL_BASIC_RATIO'] = "0."+str(int(X[39]))+str(int(X[40]))

    os.environ['SS_INTERVAL_BASIC_RATIO'] = "0."+str(int(X[41]))+str(int(X[42]))
    os.environ['DS_INTERVAL_HASHTAG_TWEET_RATIO'] = "0."+str(int(X[43]))+str(int(X[44]))

    os.environ['SS_INTERVAL_HASHTAG_TWEET_RATIO'] = "0."+str(int(X[45]))+str(int(X[46]))
    # os.environ['DS_THRESHOLD_AVERAGE_FAVORITE_COUNT'] = "0."+str(int(X[73]))+str(int(X[74]))
    # os.environ['DS_INTERVAL_AVERAGE_FAVORITE_COUNT'] = "0."+str(int(X[75]))+str(int(X[76]))

    os.environ['MCAV'] = "0." + str(int(X[51]))


    result = dca20(data,4)
    res = json.loads(result)

    classified_count = res.pop("classified_count")
    classified_correctly_count = res.pop("classified_correctly_count")
    accuracy = classified_correctly_count / classified_count
    if accuracy >= 0.7:
        print(str(os.environ)[2912:])
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

varbound = np.concatenate((np.full((21, 2), [0, 15]), np.full((5, 2), [5, 50]), np.full((1, 2), [0, 100]),
                           np.full((1, 2), [-15, -1]), np.full((2, 2), [0, 0]), np.full((1, 2), [5, 150]),
                           np.full((20, 2), [0, 9]), np.full((1, 2), [3, 7])),
                          axis=0)

vartype = np.concatenate((np.full((31, 1), 'int'), np.full((21, 1), 'int')),
                         axis=0)

algorithm_param = {'max_num_iteration': 250,
                   'population_size': 20,
                   'mutation_probability': 0.3,
                   'elit_ratio': 0.1,
                   'crossover_probability': 0.4,
                   'parents_portion': 0.3,
                   'crossover_type': 'two_point',
                   'max_iteration_without_improv': 25}

model = ga(function=f, dimension=52, variable_type_mixed=vartype, variable_boundaries=varbound, function_timeout=36000,
           algorithm_parameters=algorithm_param)

model.run()



