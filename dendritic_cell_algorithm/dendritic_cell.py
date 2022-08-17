import copy
import json
import logging


class DendriticCell:
    def __init__(self, id):
        self.id = id
        self.k = 0.0
        self.cms = 0.0
        self.migration_threshold = 1000
        self.antigens = {}
        self.antigen_count = 0
        self.class_label = ""
        self.avg_values = {}

    def can_cell_migrate(self):
        return self.cms >= self.migration_threshold


    def calculate_difference(self, antigen):
        logging.info("calculate_difference")

        if self.antigen_count == 0:
            logging.info("no antigens collected")
            return 0
        else:
            result = 0
            for key in self.avg_values:

                logging.info(key)

                logging.info(str(self.avg_values[key]) + " - " + str(antigen.value["parameters"][key]))

                if self.avg_values[key] is None or antigen.value["parameters"][key] is None:
                    continue

                if max(self.avg_values[key], antigen.value["parameters"][key]) == 0:
                    continue

                result += abs(self.avg_values[key] - antigen.value["parameters"][key])/max(self.avg_values[key], antigen.value["parameters"][key])

            logging.info("distance: " + str(result))

            if antigen.id in self.antigens:
                result += 10*self.antigens[antigen.id]["count"]
                logging.info("already collected by this dc: " + str(self.antigens[antigen.id]["count"]) + " times")

        return result


    def update_avg_values(self, antigen):

        logging.info("avg values of dc before: " + json.dumps(self.avg_values))

        if not self.avg_values:
            if antigen.value != "last":
                self.avg_values = copy.copy(antigen.value["parameters"])
                logging.info("avg values of dc before: " + json.dumps(self.avg_values))
                for key in ["cms", "mDC", "smDC", "k", "cms_bot", "mDC_bot", "smDC_bot", "k_bot", "cms_bad_intentions", "mDC_bad_intentions", "smDC_bad_intentions", "k_bad_intentions", "is_bot_probability", "intentions_are_bad_probability"]:
                    self.avg_values.pop(key)
        else:
            for key in self.avg_values:

                if antigen.value == "last":
                    continue

                if self.avg_values[key] is None or antigen.value["parameters"][key] is None:
                    continue

                self.avg_values[key] = (self.avg_values[key] * (self.antigen_count - 1) + antigen.value["parameters"][key])/self.antigen_count

        logging.info("avg values of dc after: " + json.dumps(self.avg_values))


    def expose_cell(self, antigen):
        self.cms += antigen.cms
        self.k += antigen.k

        self.antigens.setdefault(antigen.id, {"antigen": antigen, "count": 0})
        self.antigens[antigen.id]["count"] += 1

        self.antigen_count += 1
        self.update_avg_values(antigen)


        antigen.collected_by.setdefault(self.id, {"cell": self, "count": 0})
        antigen.collected_by[self.id]["count"] += 1

        if self.can_cell_migrate():
            self.class_label = "Anomaly" if (self.k > 0) else "Normal"
            for id in self.antigens:
                self.antigens[id]["antigen"].update_number_of_migrated_cells(self.antigens[id]["count"])
            logging.info("migrate!")
            return self, 1

        else:
            return self, 0

    def __str__(self):
        return "{  DC id: % s, k: % s, cms: % s, migration_threshold: % s, " \
               "antigens: % s, class_label: % s  }" % (self.id, self.k,
                                                                        self.cms, self.migration_threshold,
                                                                        self.antigens, self.class_label)
