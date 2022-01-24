import os
import sys
import json
import csv
import pprint
import time
import logging
from signal_generator_cresci_2017 import Signals

from data_preprocessor import cresci_csv_to_json
from data_preprocessor import collect_from_twitter

cresci_csv_to_json('../datasets/cresci-2017/genuine_accounts.csv/')
# collect_from_twitter("covid19", 5, 5)



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
