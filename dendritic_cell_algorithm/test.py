import os
import sys
import json
import csv

from data_preprocessor import cresci_csv_to_json
from data_preprocessor import collect_from_twitter

#cresci_csv_to_json('../datasets/cresci-2017.csv/traditional_spambots_1.csv/')
collect_from_twitter("covid19", 5, 5)
