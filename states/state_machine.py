class StateMachine:
    def __init__(self, game):
        self.game = game
        self.states = {}
        self.current_state = None

    def add_state(self, name, state_class):
        self.states[name] = state_class

    def change_state(self, name):
        state_class = self.states[name]
        new_state = state_class(self, self.game)
        
        # Subscribe new state to day cycle if it has on_new_day method
        if hasattr(new_state, "on_new_day"):
            self.game.day_cycle.subscribe(new_state)
        
        self.current_state = new_state

    def run(self, dt):
        if self.current_state:
            self.current_state.run(dt)
