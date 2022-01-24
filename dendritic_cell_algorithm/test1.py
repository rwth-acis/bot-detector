import json
import logging
import random
import time
import pprint
from dotenv import load_dotenv
from dendritic_cell import DendriticCell
from antigen import Antigen
from signal_generator_twibot_2020 import Signals


def random_in_bounds(min_value, max_value):
    rd = random.random()
    return min_value + (max_value - min_value) * rd


if __name__ == "__main__":
    start = time.time()
    logging.getLogger().setLevel(logging.INFO)
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

    pp = pprint.PrettyPrinter(indent=4, sort_dicts=False)

    # JSON file
    f = open('../datasets/twibot-2020/data_sample.json', "r", encoding="cp850")
    # f = open('../datasets/cresci-2017/traditional_spambots1_sample.json', "r", encoding="cp850")

    # Reading from file
    data = json.loads(f.read())

    # Iterating through the json
    # list
    for user in data:
        logging.info(user)
        if user["tweet"] is None:
            user["tweet"] = []
        if len(user["tweet"]) >= 0:
            s = Signals()
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
                new_antigen = Antigen(user["ID"], user["profile"]["screen_name"], s.get_k(), s.get_csm(), 10,
                                      antigen_array, result, class_label="Anomaly")
            else:
                new_antigen = Antigen(user["ID"], user["profile"]["screen_name"], s.get_k(), s.get_csm(), 10,
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

    with open('../datasets/twibot-2020/result-dev.json', 'w') as outfile:
        outfile.write(jsonStr)

    # Closing file
    f.close()
