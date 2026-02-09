from systems.inventory_system import Inventory

class Chest:
    def __init__(self, chest_id, size=12):
        self.id = chest_id
        self.inventory = Inventory(size)
        self.opened = False

    def open(self):
        self.opened = True

    def close(self):
        self.opened = False

    def serialize(self):
        return self.inventory.serialize()

    def load(self, data):
        if data:
            self.inventory.deserialize(data)
