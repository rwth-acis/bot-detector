import json
import logging
import os


class Antigen:
    def __init__(self, id, value, k, cms, number_of_copies, array=[], result={}, send_info_to_mongodb=None, class_label="unknown"):
        self.id = id
        self.value = value
        self.k = k
        self.cms = cms
        self.class_label = class_label
        self.number_of_copies = number_of_copies
        self.number_of_migrated_cells = 0
        self.collected_by = {}
        self.array = array
        self.result = result
        self.send_info_to_mongodb = send_info_to_mongodb

    def can_be_classified(self):
        if self.number_of_copies == self.number_of_migrated_cells:
            return True
        else:
            return False

    def classify_antigen(self):
        number_of_mdc = 0
        for id in self.collected_by:
            if self.collected_by[id]["cell"].class_label == "Anomaly":
                number_of_mdc += self.collected_by[id]["count"]
        mcav = 0 if number_of_mdc == 0 else number_of_mdc / self.number_of_migrated_cells
        ans = "Anomaly" if (mcav >= float(os.environ["MCAV"])) else "Normal"
        logging.info('{0} / {1} = {2} -> {3} :: Antigen {4}'.format(number_of_mdc, self.number_of_migrated_cells,
                                                                    mcav, ans, self.id))
        self.result.setdefault("classified_count", 0)
        self.result["classified_count"] += 1
        classified_correctly = None
        if self.send_info_to_mongodb is not None:
            self.send_info_to_mongodb.insert_one(self.value)
            print("BotDetector: Send " + str(self.value))
        if self.class_label != "unknown":
            classified_correctly = (self.class_label == ans)
            logging.info("_______________________CORRECT?!_______________________")
            logging.info(classified_correctly)
            if classified_correctly:
                self.result.setdefault("classified_correctly_count", 0)
                self.result["classified_correctly_count"] += 1
                if self.class_label == "Anomaly":
                    self.result.setdefault("anomaly_classified_correctly_count", 0)
                    self.result["anomaly_classified_correctly_count"] += 1
                else:
                    self.result.setdefault("normal_classified_correctly_count", 0)
                    self.result["normal_classified_correctly_count"] += 1
            else:
                if self.class_label == "Anomaly":
                    self.result.setdefault("anomaly_classified_UNcorrectly_count", 0)
                    self.result["anomaly_classified_UNcorrectly_count"] += 1
                else:
                    self.result.setdefault("normal_classified_UNcorrectly_count", 0)
                    self.result["normal_classified_UNcorrectly_count"] += 1

            self.result[self.id] = {
                "id": self.id,
                "mature_rate": '{0} / {1} = {2}'.format(number_of_mdc,
                                                        self.number_of_migrated_cells,
                                                        mcav),
                "classification_result": ans,
                "classified_correctly": classified_correctly,
                "label_from_dataset": self.class_label,
                "parameters": self.value["parameters"],
                "screen_name": self.value["screen_name"]}

        try:
            self.array.remove(self)
            logging.info("remove")
        except Exception as e:
            logging.info("did not remove")

        logging.info(self)
        return ans, classified_correctly

    def update_number_of_migrated_cells(self, count):
        self.number_of_migrated_cells += count
        if self.can_be_classified():
            self.classify_antigen()

    def __str__(self):
        """
        return "{  Antigen id: % s, class_label: % s, " \
               "number_of_migrated_cells: % s, collected_by: % s  }" % (
                   self.id,
                   self.class_label,
                   self.number_of_migrated_cells, self.collected_by)
"""

        return "{Antigen id: % s, value: % s, k: % s, cms: % s, class_label: % s, number_of_copies: % s, " \
               "number_of_migrated_cells: % s, collected_by: % s}              " % (
               self.id, self.value, self.k, self.cms,
               self.class_label, self.number_of_copies,
               self.number_of_migrated_cells, self.collected_by)

