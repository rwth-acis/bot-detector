class DendriticCell:
    def __init__(self, id):
        self.id = id
        self.lifespan = 400
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
        self.lifespan -= antigen.cms
        self.antigens.setdefault(antigen.id, {"antigen": antigen, "count": 0})
        self.antigens[antigen.id]["count"] += 1
        if self.can_cell_migrate():
            self.class_label = "Anomaly" if (self.k > 0) else "Normal"
            for ag in self.antigens:
                self.antigens[ag]["antigen"].update_number_of_migrated_cells(self.antigens[ag]["count"])
            print("migrate!")
            return self, 2

        else:
            if self.lifespan <= 0:
                print("lifespan<0!")
                self.lifespan = 200
                self.k = 0.0
                self.cms = 0.0
                self.migration_threshold = 150
                self.antigens = {}
                return self, 1
        return self, 0

    def __str__(self):
        return "{  DC id: % s, lifespan: % s, k: % s, cms: % s, migration_threshold: % s, " \
               "antigens: % s, class_label: % s  }" % (self.id, self.lifespan, self.k,
                                                                        self.cms, self.migration_threshold,
                                                                        self.antigens, self.class_label)
