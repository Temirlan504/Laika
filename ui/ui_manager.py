class UIManager:
    def __init__(self):
        self.elements = []

    def add(self, element):
        self.elements.append(element)

    def handle_input(self, events):
        for e in self.elements:
            if e.visible:
                e.handle_input(events)

    def draw(self):
        for e in self.elements:
            if e.visible:
                e.draw()
