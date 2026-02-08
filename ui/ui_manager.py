class UIManager:
    def __init__(self):
        self.elements = []

    def add(self, element):
        self.elements.append(element)

    def handle_input(self, events):
        for event in events:
            for element in self.elements:
                if element and hasattr(element, 'visible') and element.visible:
                    if hasattr(element, 'handle_event'):
                        element.handle_event(event)

    def draw(self):
        for e in self.elements:
            if e is not None and hasattr(e, 'visible') and e.visible:
                e.draw()
