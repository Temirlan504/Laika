from utils.timer import Timer

class Plant:
    def __init__(self, plant_type):
        self.plant_type = plant_type

        # Growth stages
        self.growth_stage = 0
        self.max_stage = 3

        # Growth timing configuration (in milliseconds)
        self.growth_config = {
            'potato': 15000,   # 15 seconds total to grow
            'tomato': 20000,   # 20 seconds total to grow
            'carrot': 10000    # 10 seconds total to grow
        }
        
        # Get milliseconds per stage for this plant type
        total_time = self.growth_config.get(plant_type, 15000)
        self.ms_per_stage = total_time / self.max_stage
        
        # Plant owns its own growth timer
        self.growth_timer = None

    def start_growth_timer(self):
        """Start the timer for the next growth stage"""
        if not self.is_fully_grown:
            self.growth_timer = Timer(self.ms_per_stage, self.on_growth_complete)
            self.growth_timer.activate()
    
    def on_growth_complete(self):
        """Called when a growth stage completes"""
        self.grow()
        
        # Start next stage if not fully grown
        if not self.is_fully_grown:
            self.start_growth_timer()

    def grow(self):
        """Advance plant growth by one stage"""
        if self.growth_stage < self.max_stage:
            self.growth_stage += 1
            print(f"[PLANT] {self.plant_type} grew to stage {self.growth_stage}/{self.max_stage}")

    def grow_to_final(self):
        """Instantly grow plant to final stage (used when sleeping)"""
        self.growth_stage = self.max_stage
        
        # Stop any active timer
        if self.growth_timer:
            self.growth_timer.deactivate()
            self.growth_timer = None

    def update(self):
        """Update the growth timer"""
        if self.growth_timer:
            self.growth_timer.update()

    @property
    def is_fully_grown(self):
        return self.growth_stage >= self.max_stage
