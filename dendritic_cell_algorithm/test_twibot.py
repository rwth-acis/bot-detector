import os
import sys
import json
import csv
import pprint
import time
import logging

import matplotlib
from dotenv import load_dotenv
import logging

from signal_generator_cresci_2017 import Signals

from data_preprocessor import cresci_csv_to_json
from data_preprocessor import collect_from_twitter
from dendritic_cell_algorithm import dc_algorithm_cresci_2017

from dendritic_cell_algorithm import dc_algorithm_twibot_2020

import numpy as np
from geneticalgorithm import geneticalgorithm as ga
from dendritic_cell_algorithm import dc_algorithm_cresci_2017 as dca17
from dendritic_cell_algorithm import dc_algorithm_twibot_2020_test as dca20

load_dotenv()


logging.getLogger().setLevel(logging.INFO)

""""""

f = open("../datasets/twibot-2020/train.json", "r", encoding="cp850")

# Reading from file
data = json.loads(f.read())
""""""

print(str(os.environ))

"""

f1 = open("../datasets/twibot-2020/test.json", "r", encoding="cp850")

# Reading from file
data1 = json.loads(f1.read())

f2 = open("../datasets/twibot-2020/dev.json", "r", encoding="cp850")

# Reading from file
data2 = json.loads(f2.read())

f3 = open("../datasets/twibot-2020/train.json", "r", encoding="cp850")

# Reading from file
data3 = json.loads(f3.read())

for user in data2:
    data1.append(user)

for user in data3:
    data1.append(user)
"""
result = dca20(data, 5)
res = json.loads(result)
with open('../datasets/twibot-2020/result-trained-my_for_auc_test.json', 'w') as outfile:
    outfile.write(result)
classified_count = res.pop("classified_count")
classified_correctly_count = res.pop("classified_correctly_count")
accuracy = classified_correctly_count / classified_count
print("\nAccuracy = {0}/{1} = {2} \n".format(classified_correctly_count, classified_count, accuracy))
print(1 - accuracy)
time = res.pop("time")
print("Time: {0} \n".format(time))
