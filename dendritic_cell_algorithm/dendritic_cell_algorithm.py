import json
import logging
import random
import time
import pprint
from dotenv import load_dotenv
from dendritic_cell import DendriticCell
from antigen import Antigen
from signal_generator_cresci_2017 import Signals as Signals_cresci_2017
from signal_generator_twibot_2020 import Signals as Signals_twibot_2020


def random_in_bounds(min_value, max_value):
    rd = random.random()
    return min_value + (max_value - min_value) * rd


def dc_algorithm_cresci_2017(path, label):
    start = time.time()
    load_dotenv()
    # =========================== INITIALIZE ANTIGENS ====================================
    """    
    random.seed(time.time())
    antigen_array = []
    result = {"classified_count": 0, "classified_correctly_count": 0}
    for i in range(10):
        new_antigen = Antigen(str(i), i, random_in_bounds(-100, 0), random_in_bounds(30, 100), 20,
                              antigen_array, result, class_label="Normal")
        antigen_array.append(new_antigen)

    for i in range(100, 110):
        new_antigen = Antigen(str(i), i, random_in_bounds(1, 100), random_in_bounds(30, 100), 20,
                              antigen_array, result, class_label="Anomaly")
        antigen_array.append(new_antigen)

    logging.info("antigen_array")
    logging.info([str(item) for item in antigen_array])
    """
    antigen_array = []
    result = {"classified_count": 0, "classified_correctly_count": 0, "time": 0}

    # JSON file
    f = open(path, "r", encoding="cp850")

    # Reading from file
    data = json.loads(f.read())

    # Iterating through the json
    for user in data['users']:
        logging.info(user)
        if len(user["tweets"]) >= 0:
            s = Signals_cresci_2017()
            s.generate_signals(int(user["friends_count"]), int(user["statuses_count"]), int(user["followers_count"]),
                               int(user["verified"]) if (str(user["verified"]) != "NULL" and str(user["verified"]) != "") else False,
                               int(user["default_profile"]) if (str(user["default_profile"]) != "NULL" and str(user["default_profile"]) != "") else False,
                               int(user["default_profile_image"]) if (str(user["default_profile_image"]) != "NULL" and str(user["default_profile_image"]) != "") else False,
                               user["timestamp"], user["name"],
                               user["screen_name"], user["description"], user["tweets"])

            logging.info(user["id"])
            logging.info(s.get_k())
            new_antigen = Antigen(user["id"], {"screen_name": user["screen_name"], "parameters": s.get_parameters()}, s.get_k(), s.get_csm(), 5,
                                  antigen_array, result, class_label=label)
            antigen_array.append(new_antigen)
        else:
            logging.info(user["id"])
            logging.info("not enough tweets")

    # =========================== INITIALIZE DCs ====================================

    dc_array = []
    for i in range(100):
        dc = DendriticCell(str(i))
        dc_array.append(dc)

    logging.info("dc_array")
    logging.info([str(item) for item in dc_array])

    # =========================== DC ALGORITHM =======================================

    dc_count = len(dc_array)
    for antigen in antigen_array[:]:
        logging.info(antigen)
        for i in range(antigen.number_of_copies):
            cell_random = int(random_in_bounds(0, (len(dc_array) - 1)))
            logging.info("expose cell {0} to antigen {1}".format(int(dc_array[cell_random].id), int(antigen.id)))
            cell, status = dc_array[cell_random].expose_cell(antigen)

            if status == 1:
                dc_count += 1
                dc_array.remove(cell)
                dc = DendriticCell(str(dc_count))
                dc_array.append(dc)

    logging.info("antigens: ")
    logging.info([str(item) for item in antigen_array])
    logging.info("DCells: ")
    logging.info([str(item) for item in dc_array])

    # ======================= END: Force all cells to migrate ==================================
    last_antigen = Antigen(str("last"), "last", 0, 400, 20, antigen_array, {})
    for dcell in dc_array[:]:
        logging.info("expose cell {0} to antigen {1}".format(dcell.id, last_antigen.id))
        cell, status = dcell.expose_cell(last_antigen)
        if status == 1:
            dc_count += 1
            dc_array.remove(cell)
            dc = DendriticCell(str(dc_count))
            dc_array.append(dc)

    logging.info("antigens: ")
    logging.info([str(item) for item in antigen_array])
    logging.info("DCells: ")
    logging.info([str(item) for item in dc_array])

    # ======================= END: Save results to file ==================================
    end = time.time()
    logging.info(end - start)
    result["time"] = str(int((end - start)/60)) + ":" + str(int((end - start) - 60*int((end - start)/60)))
    jsonStr = json.dumps(result, indent=4)
    logging.info(jsonStr)

    """with open('result1.json', 'w') as outfile:
            outfile.write(jsonStr)"""

    """with open('../datasets/cresci-2017/genuine_accounts.csv/result-DCA-of-1.json', 'w') as outfile:
        outfile.write(jsonStr)"""

    # Closing file
    f.close()
    return jsonStr


def dc_algorithm_twibot_2020(path):
    start = time.time()
    # =========================== INITIALIZE ANTIGENS ====================================
    """    
    random.seed(time.time())
    antigen_array = []
    result = {"classified_count": 0, "classified_correctly_count": 0}
    for i in range(10):
        new_antigen = Antigen(str(i), i, random_in_bounds(-100, 0), random_in_bounds(30, 100), 20,
                              antigen_array, result, class_label="Normal")
        antigen_array.append(new_antigen)

    for i in range(100, 110):
        new_antigen = Antigen(str(i), i, random_in_bounds(1, 100), random_in_bounds(30, 100), 20,
                              antigen_array, result, class_label="Anomaly")
        antigen_array.append(new_antigen)

    logging.info("antigen_array")
    logging.info([str(item) for item in antigen_array])
    """
    antigen_array = []
    result = {"classified_count": 0, "classified_correctly_count": 0, "time": 0}

    # JSON file
    f = open(path, "r", encoding="cp850")

    # Reading from file
    data = json.loads(f.read())

    # Iterating through the json
    for user in data:
        logging.info(user)
        if user["tweet"] is None:
            user["tweet"] = []
        if len(user["tweet"]) >= 0:
            s = Signals_twibot_2020()
            s.generate_signals(int(user["profile"]["friends_count"][:-1]), int(user["profile"]["statuses_count"][:-1]),
                               int(user["profile"]["followers_count"][:-1]),
                               True if (user["profile"]["verified"] == "True ") else False,
                               True if (user["profile"]["default_profile"] == "True ") else False,
                               True if (user["profile"]["default_profile_image"] == "True ") else False,
                               user["profile"]["created_at"][:-1], user["profile"]["name"][:-1],
                               user["profile"]["screen_name"][:-1], user["profile"]["description"][:-1], user["tweet"])

            logging.info(user["ID"])
            logging.info(s.get_k())
            if user["label"] == "1":
                new_antigen = Antigen(user["ID"], {"screen_name": user["profile"]["screen_name"][:-1], "parameters": s.get_parameters()}, s.get_k(), s.get_csm(), 10,
                                      antigen_array, result, class_label="Anomaly")
            else:
                new_antigen = Antigen(user["ID"], {"screen_name": user["profile"]["screen_name"][:-1], "parameters": s.get_parameters()}, s.get_k(), s.get_csm(), 10,
                                      antigen_array, result, class_label="Normal")
            antigen_array.append(new_antigen)
        else:
            logging.info(user["ID"])
            logging.info("not enough tweets")

    # =========================== INITIALIZE DCs ====================================

    dc_array = []
    for i in range(200):
        dc = DendriticCell(str(i))
        dc_array.append(dc)

    logging.info("dc_array")
    logging.info([str(item) for item in dc_array])

    # =========================== DC ALGORITHM =======================================

    dc_count = len(dc_array)
    for antigen in antigen_array[:]:
        logging.info(antigen)
        for i in range(antigen.number_of_copies):
            cell_random = int(random_in_bounds(0, (len(dc_array) - 1)))
            logging.info("expose cell {0} to antigen {1}".format(int(dc_array[cell_random].id), int(antigen.id)))
            cell, status = dc_array[cell_random].expose_cell(antigen)

            if status == 1:
                dc_count += 1
                dc_array.remove(cell)
                dc = DendriticCell(str(dc_count))
                dc_array.append(dc)

    logging.info("antigens: ")
    logging.info([str(item) for item in antigen_array])
    logging.info("DCells: ")
    logging.info([str(item) for item in dc_array])

    # ======================= END: Force all cells to migrate ==================================
    last_antigen = Antigen(str("last"), "last", 0, 400, 20, antigen_array, {})
    for dcell in dc_array[:]:
        logging.info("expose cell {0} to antigen {1}".format(dcell.id, last_antigen.id))
        cell, status = dcell.expose_cell(last_antigen)
        if status == 1:
            dc_count += 1
            dc_array.remove(cell)
            dc = DendriticCell(str(dc_count))
            dc_array.append(dc)

    logging.info("antigens: ")
    logging.info([str(item) for item in antigen_array])
    logging.info("DCells: ")
    logging.info([str(item) for item in dc_array])

    # ======================= END: Save results to file ==================================
    end = time.time()
    logging.info(end - start)
    result["time"] = str(int((end - start)/60)) + ":" + str(int((end - start) - 60*int((end - start)/60)))
    jsonStr = json.dumps(result, indent=4)
    logging.info(jsonStr)

    """with open('result1.json', 'w') as outfile:
            outfile.write(jsonStr)"""

    """with open('../datasets/twibot-2020/result-dev.json', 'w') as outfile:
        outfile.write(jsonStr)"""

    # Closing file
    f.close()
    return jsonStr
