class Antigen:
    def __init__(self, id, value, k, cms, number_of_copies, array=[], result={}, class_label="unknown"):
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
        ans = "Anomaly" if (mcav >= 0.4) else "Normal"
        print('{0} / {1} = {2} -> {3} :: Antigen {4}'.format(number_of_mdc, self.number_of_migrated_cells,
                                                             mcav, ans, self.id))
        self.result.setdefault("classified_count", 0)
        self.result["classified_count"] += 1
        classified_correctly = None
        if self.class_label != "unknown":
            classified_correctly = (self.class_label == ans)
            print("_______________________CORRECT?!_______________________")
            print(classified_correctly)
            if classified_correctly:
                self.result.setdefault("classified_correctly_count", 0)
                self.result["classified_correctly_count"] += 1
            self.result[self.id] = 'Antigen {5} :: {0} / {1} = {2} -> {3} ' \
                                   ':: correct: {4} '.format(number_of_mdc,
                                                             self.number_of_migrated_cells,
                                                             mcav, ans,
                                                             classified_correctly,
                                                             self.id)

        try:
            self.array.remove(self)
            print("remove")
        except Exception as e:
            print("did not remove")

        print(self)
        return ans, classified_correctly

    def update_number_of_migrated_cells(self, count):
        self.number_of_migrated_cells += count
        if self.can_be_classified():
            self.classify_antigen()

    def __str__(self):
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
        """
