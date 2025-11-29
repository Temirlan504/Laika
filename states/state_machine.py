class StateMachine:
    def __init__(self, game):
        self.game = game
        self.states = {}
        self.current_state = None

    def add_state(self, name, state_class):
        self.states[name] = state_class

    def change_state(self, name):
        state_class = self.states[name]
        self.current_state = state_class(self, self.game)

    def run(self, dt):
        if self.current_state:
            self.current_state.run(dt)
