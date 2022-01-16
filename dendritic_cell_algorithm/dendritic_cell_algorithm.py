import random
import time

from dendritic_cell import DendriticCell
from antigen import Antigen


def random_in_bounds(min_value, max_value):
    rd = random.random()
    return min_value + (max_value - min_value) * rd


if __name__ == "__main__":
    random.seed(time.time())
    antigen_array = []
    result = {"classified_count": 0, "classified_correctly_count": 0}
    for i in range(50):
        new_antigen = Antigen(str(i), i, random_in_bounds(-100, 0), random_in_bounds(30, 100), 20,
                              antigen_array, result, class_label="Normal")
        antigen_array.append(new_antigen)

    for i in range(100, 150):
        new_antigen = Antigen(str(i), i, random_in_bounds(1, 100), random_in_bounds(30, 100), 20,
                              antigen_array, result, class_label="Anomaly")
        antigen_array.append(new_antigen)

    print("antigen_array")
    print([str(item) for item in antigen_array])

    dc_array = []
    for i in range(10):
        dc = DendriticCell(str(i))
        dc_array.append(dc)

    print("dc_array")
    print([str(item) for item in dc_array])
    dc_count = len(dc_array)
    for antigen in antigen_array[:]:
        print(antigen)
        for i in range(antigen.number_of_copies):

            cell_random = int(random_in_bounds(0, (len(dc_array) - 1)))
            print("expose cell {0} to antigen {1}".format(int(dc_array[cell_random].id), int(antigen.id)))
            cell, status = antigen.expose_to_cell(dc_array[cell_random])

            if status == 2:
                dc_count += 1
                dc_array.remove(cell)
                dc = DendriticCell(str(dc_count))
                dc_array.append(dc)

            if status == 1:
                dc_count += 1
                dc_array.remove(cell)
                dc = DendriticCell(str(dc_count))
                dc_array.append(dc)

    print("antigens: ")
    print([str(item) for item in antigen_array])
    print("DCells: ")
    print([str(item) for item in dc_array])

    last_antigen = Antigen(str("last"), "last", 0, 400, 20, {}, antigen_array)
    for dcell in dc_array[:]:
        cell, status = last_antigen.expose_to_cell(dcell)
        if status == 2:
            dc_count += 1
            dc_array.remove(cell)
            dc = DendriticCell(str(dc_count))
            dc_array.append(dc)

        if status == 1:
            dc_count += 1
            dc_array.remove(cell)
            dc = DendriticCell(str(dc_count))
            dc_array.append(dc)

    print("antigens: ")
    print([str(item) for item in antigen_array])
    print("DCells: ")
    print([str(item) for item in dc_array])
    for i in result:
        print(i)
        print(result[i])
