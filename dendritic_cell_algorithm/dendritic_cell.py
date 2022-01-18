class DendriticCell:
    def __init__(self, id):
        self.id = id
        self.k = 0.0
        self.cms = 0.0
        self.migration_threshold = 350
        self.antigens = {}
        self.class_label = ""

    def can_cell_migrate(self):
        return self.cms >= self.migration_threshold

    def expose_cell(self, antigen):
        self.cms += antigen.cms
        self.k += antigen.k
        self.antigens.setdefault(antigen.id, {"antigen": antigen, "count": 0})
        self.antigens[antigen.id]["count"] += 1

        antigen.collected_by.setdefault(self.id, {"cell": self, "count": 0})
        antigen.collected_by[self.id]["count"] += 1

        if self.can_cell_migrate():
            self.class_label = "Anomaly" if (self.k > 0) else "Normal"
            for id in self.antigens:
                self.antigens[id]["antigen"].update_number_of_migrated_cells(self.antigens[id]["count"])
            print("migrate!")
            return self, 1

        else:
            return self, 0

    def __str__(self):
        return "{  DC id: % s, k: % s, cms: % s, migration_threshold: % s, " \
               "antigens: % s, class_label: % s  }" % (self.id, self.k,
                                                                        self.cms, self.migration_threshold,
                                                                        self.antigens, self.class_label)
