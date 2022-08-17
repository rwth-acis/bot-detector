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
from dendritic_cell_algorithm import dc_algorithm_cresci_2017_test as dca17
from dendritic_cell_algorithm import dc_algorithm_cresci_2017_random_test as dca17_random
from dendritic_cell_algorithm import dc_algorithm_cresci_2017 as dca
from dendritic_cell_algorithm import dc_algorithm_twibot_2020 as dca20

load_dotenv()

logging.getLogger().setLevel(logging.INFO)

""""""
f1 = open("../datasets/cresci-2017/genuine_accounts.csv/genuine_accounts-1.json", "r", encoding="cp850")

# Reading from file
data_normal = json.loads(f1.read())

f2 = open("../datasets/cresci-2017/genuine_accounts.csv/genuine_accounts-2.json", "r", encoding="cp850")

# Reading from file
data_normal_1 = json.loads(f2.read())

""""""

for user in data_normal_1['users']:
    data_normal['users'].append(user)





""""""
f1 = open("../datasets/cresci-2017/social_spambots_1.csv/social_spambots_1.json", "r", encoding="cp850")

# Reading from file
data_anomaly = json.loads(f1.read())

f2 = open("../datasets/cresci-2017/social_spambots_2.csv/social_spambots_2.json", "r", encoding="cp850")

# Reading from file
data_anomaly1 = json.loads(f2.read())

f3 = open("../datasets/cresci-2017/social_spambots_3.csv/social_spambots_3.json", "r", encoding="cp850")

# Reading from file
data_anomaly2 = json.loads(f3.read())

for user in data_anomaly1['users']:
    data_anomaly['users'].append(user)

for user in data_anomaly2['users']:
    data_anomaly['users'].append(user)

""""""



print(str(os.environ)[2912:])
# result = dca17(data1, "Normal", 1, data2, "Normal", 1)
# result = dca17(data1, "Anomaly", 1, data3, "Anomaly", 1)

result = dca17(data_normal, "Normal", 1, data_anomaly, "Anomaly", 1)

# result = dca("../datasets/cresci-2017/social_spambots_3.csv/social_spambots_3.json", "Anomaly")
# result = dca("../datasets/cresci-2017/traditional_spambots_1.csv/traditional_spambots_1.json", "Anomaly")
# result = dca("../datasets/cresci-2017/genuine_accounts.csv/genuine_accounts-2.json", "Normal")


res = json.loads(result)
with open('../datasets/twibot-2020/result-test-all-mix-end-table10.json', 'w') as outfile:
    outfile.write(result)

classified_count = res.pop("classified_count")
classified_correctly_count = res.pop("classified_correctly_count")
accuracy = classified_correctly_count / classified_count
print("\nAccuracy = {0}/{1} = {2} \n".format(classified_correctly_count, classified_count, accuracy))
print(1 - accuracy)
time = res.pop("time")
print("Time: {0} \n".format(time))