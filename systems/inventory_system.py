from items import get_item

class Inventory:
    def __init__(self, size=30):
        self.size = size
        self.slots = [None] * size

    # ---------- Queries ----------

    def has_item(self, item_id, amount=1):
        count = 0
        for slot in self.slots:
            if slot and slot["item_id"] == item_id:
                count += slot["quantity"]
                if count >= amount:
                    return True
        return False

    def get_total(self, item_id):
        return sum(
            slot["quantity"]
            for slot in self.slots
            if slot and slot["item_id"] == item_id
        )

    # ---------- Add / Remove ----------

    def add_item(self, item_id, amount=1):
        item_def = get_item(item_id)
        if not item_def:
            return False

        remaining = amount

        for slot in self.slots:
            if slot and slot["item_id"] == item_id:
                space = item_def.max_stack - slot["quantity"]
                if space > 0:
                    added = min(space, remaining)
                    slot["quantity"] += added
                    remaining -= added
                    if remaining == 0:
                        return True

        for i in range(self.size):
            if self.slots[i] is None:
                added = min(item_def.max_stack, remaining)
                self.slots[i] = {
                    "item_id": item_id,
                    "quantity": added
                }
                remaining -= added
                if remaining == 0:
                    return True

        return False  # Inventory full

    def remove_item(self, item_id, amount=1):
        remaining = amount

        for i in range(self.size):
            slot = self.slots[i]
            if slot and slot["item_id"] == item_id:
                if slot["quantity"] > remaining:
                    slot["quantity"] -= remaining
                    return True
                else:
                    remaining -= slot["quantity"]
                    self.slots[i] = None
                    if remaining == 0:
                        return True

        return False

    # ---------- Slot-level helpers (for UI & chests later) ----------

    def get_slot(self, index):
        if 0 <= index < self.size:
            return self.slots[index]
        return None

    def set_slot(self, index, data):
        if 0 <= index < self.size:
            self.slots[index] = data

    def serialize(self):
        return self.slots

    def deserialize(self, data):
        self.slots = data
