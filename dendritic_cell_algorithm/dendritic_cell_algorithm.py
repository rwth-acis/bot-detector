import json
import logging
import random
import time
import pprint
from dotenv import load_dotenv
from dendritic_cell import DendriticCell
from antigen import Antigen
from signal_generator_cresci_2017 import Signals


def random_in_bounds(min_value, max_value):
    rd = random.random()
    return min_value + (max_value - min_value) * rd


if __name__ == "__main__":
    start = time.time()
    load_dotenv()
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

    print("antigen_array")
    print([str(item) for item in antigen_array])
    """
    antigen_array = []
    result = {"classified_count": 0, "classified_correctly_count": 0, "time": 0}

    pp = pprint.PrettyPrinter(indent=4, sort_dicts=False)

    # JSON file
    f = open('../datasets/cresci-2017/traditional_spambots_1.csv/result.json', "r", encoding="cp850")
    # f = open('../datasets/cresci-2017/traditional_spambots1_sample.json', "r", encoding="cp850")

    # Reading from file
    data = json.loads(f.read())

    # Iterating through the json
    # list
    for user in data['users']:
        if len(user["tweets"]) >= 0:
            s = Signals()
            s.generate_signals(int(user["friends_count"]), int(user["statuses_count"]), int(user["followers_count"]),
                               user["verified"] if (
                                           str(user["verified"]) == "NULL" and str(user["verified"]) == "") else False,
                               user["default_profile"] if (str(user["default_profile"]) != "NULL" and str(
                                   user["default_profile"]) != "") else False,
                               user["default_profile_image"] if (str(user["default_profile_image"]) != "NULL" and str(
                                   user["default_profile_image"]) != "") else False,
                               user["timestamp"], user["name"],
                               user["screen_name"], user["description"], user["tweets"])

            print(user["id"])
            print(s.get_k())
            new_antigen = Antigen(user["id"], user["screen_name"], s.get_k(), s.get_csm(), 5,
                                  antigen_array, result, class_label="Anomaly")
            antigen_array.append(new_antigen)
        else:
            print(user["id"])
            print("not enough tweets")

    # =========================== INITIALIZE DCs ====================================

    dc_array = []
    for i in range(100):
        dc = DendriticCell(str(i))
        dc_array.append(dc)

    print("dc_array")
    print([str(item) for item in dc_array])

    # =========================== DC ALGORITHM =======================================

    dc_count = len(dc_array)
    for antigen in antigen_array[:]:
        print(antigen)
        for i in range(antigen.number_of_copies):
            cell_random = int(random_in_bounds(0, (len(dc_array) - 1)))
            print("expose cell {0} to antigen {1}".format(int(dc_array[cell_random].id), int(antigen.id)))
            cell, status = dc_array[cell_random].expose_cell(antigen)

            if status == 1:
                dc_count += 1
                dc_array.remove(cell)
                dc = DendriticCell(str(dc_count))
                dc_array.append(dc)

    print("antigens: ")
    print([str(item) for item in antigen_array])
    print("DCells: ")
    print([str(item) for item in dc_array])

    # ======================= END: Force all cells to migrate ==================================
    last_antigen = Antigen(str("last"), "last", 0, 400, 20, antigen_array, {})
    for dcell in dc_array[:]:
        print("expose cell {0} to antigen {1}".format(dcell.id, last_antigen.id))
        cell, status = dcell.expose_cell(last_antigen)
        if status == 1:
            dc_count += 1
            dc_array.remove(cell)
            dc = DendriticCell(str(dc_count))
            dc_array.append(dc)

    print("antigens: ")
    print([str(item) for item in antigen_array])
    print("DCells: ")
    print([str(item) for item in dc_array])

    # ======================= END: Save results to file ==================================
    end = time.time()
    print(end - start)
    result["time"] = str(int((end - start)/60)) + ":" + str(int((end - start) - 60*int((end - start)/60)))
    jsonStr = json.dumps(result, indent=4)
    print(jsonStr)

    with open('../datasets/cresci-2017/traditional_spambots_1.csv/result-DCA-all.json', 'w') as outfile:
        outfile.write(jsonStr)

    # Closing file
    f.close()
