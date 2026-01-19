class StateMachine:
    def __init__(self, game):
        self.game = game
        self.state_classes = {}  # Store state classes
        self.state_instances = {}  # Store actual state instances
        self.current_state = None

    def add_state(self, name, state_class):
        """Register a state class"""
        self.state_classes[name] = state_class

    def change_state(self, name, **kwargs):
        """Change to a state, creating it only if it doesn't exist"""
        # Create state instance if it doesn't exist yet
        if name not in self.state_instances:
            state_class = self.state_classes[name]
            new_state = state_class(self, self.game)
            self.state_instances[name] = new_state
            
            # Subscribe to day cycle if it has on_new_day method
            if hasattr(new_state, "on_new_day"):
                self.game.day_cycle.subscribe(new_state)
        
        # Switch to the existing state instance
        self.current_state = self.state_instances[name]
        
        # Call on_enter if state has it (useful for setup when entering)
        if hasattr(self.current_state, "on_enter"):
            self.current_state.on_enter(**kwargs)

    def run(self, dt):
        if self.current_state:
            self.current_state.run(dt)
