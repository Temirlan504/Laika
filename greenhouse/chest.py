from systems.inventory_system import Inventory

class Chest:
    def __init__(self, chest_id, size=36):
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

    @classmethod
    def from_player_inventory(cls, chest_id, player):
        """Create a chest pre-filled with everything from the player's inventory and hotbar."""
        chest = cls(chest_id)

        # Transfer inventory slots
        for i, slot in enumerate(player.inventory.slots):
            if slot:
                chest.inventory.set_slot(i, dict(slot))
                player.inventory.set_slot(i, None)

        # Transfer hotbar slots into remaining chest space
        for slot in player.hotbar.slots:
            if slot:
                chest.inventory.add_item(slot["item_id"], slot["quantity"])

        # Clear hotbar
        for i in range(player.hotbar.num_slots):
            player.hotbar.set_slot(i, None)

        return chest
