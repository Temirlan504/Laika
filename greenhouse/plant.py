class Plant:
    def __init__(self, plant_type):
        self.plant_type = plant_type

        # Growth
        self.growth_stage = 0
        self.max_stage = 3

        # Timing (will connect later)
        self.days_grown = 0
        self.days_per_stage = 1  # simple for now

    def grow(self):
        """Advance plant growth by one step"""
        if self.growth_stage < self.max_stage:
            self.days_grown += 1

            if self.days_grown >= self.days_per_stage:
                self.days_grown = 0
                self.growth_stage += 1

    @property
    def is_fully_grown(self):
        return self.growth_stage >= self.max_stage
