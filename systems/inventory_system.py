from items import get_item

class Inventory:
    def __init__(self, size=36):
        self.size = size
        self.slots = [None] * size
        self.on_item_added = None  # Callback for when an item is added

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
                        if self.on_item_added:
                            self.on_item_added(item_id, amount)
                        return True

        for i in range(self.size):
            if self.slots[i] is None:
                added = min(item_def.max_stack, remaining)
                self.slots[i] = {"item_id": item_id, "quantity": added}
                remaining -= added
                if remaining == 0:
                    if self.on_item_added:
                        self.on_item_added(item_id, amount)
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


class Hotbar:
    """Independent hotbar system with its own slots"""
    def __init__(self, num_slots=9):
        self.num_slots = num_slots
        self.selected_slot = 0  # Currently selected hotbar slot (0-8)
        self.slots = [None] * num_slots  # Independent hotbar slots
    
    def get_slot(self, hotbar_index):
        """Get the item data in a hotbar slot"""
        if 0 <= hotbar_index < self.num_slots:
            return self.slots[hotbar_index]
        return None
    
    def set_slot(self, hotbar_index, data):
        """Set the item data in a hotbar slot"""
        if 0 <= hotbar_index < self.num_slots:
            self.slots[hotbar_index] = data
    
    def get_selected_slot(self):
        """Get the currently selected hotbar slot data"""
        return self.get_slot(self.selected_slot)
    
    def get_selected_item_id(self):
        """Get the item_id of the currently selected slot, or None"""
        slot = self.get_selected_slot()
        return slot["item_id"] if slot else None
    
    def select_slot(self, index):
        """Select a hotbar slot (0-8)"""
        if 0 <= index < self.num_slots:
            self.selected_slot = index
    
    def select_next(self):
        """Select the next hotbar slot (wraps around)"""
        self.selected_slot = (self.selected_slot + 1) % self.num_slots
    
    def select_previous(self):
        """Select the previous hotbar slot (wraps around)"""
        self.selected_slot = (self.selected_slot - 1) % self.num_slots
    
    def has_item(self, item_id, amount=1):
        """Check if hotbar has an item"""
        count = 0
        for slot in self.slots:
            if slot and slot["item_id"] == item_id:
                count += slot["quantity"]
                if count >= amount:
                    return True
        return False
    
    def remove_item(self, item_id, amount=1):
        """Remove item from hotbar (for using tools/seeds)"""
        remaining = amount
        
        for i in range(self.num_slots):
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
    
    def serialize(self):
        """Serialize hotbar for saving"""
        return self.slots
    
    def deserialize(self, data):
        """Deserialize hotbar from save data"""
        if len(data) == self.num_slots:
            self.slots = data
        else:
            # Handle mismatched sizes
            self.slots = [None] * self.num_slots
            for i in range(min(len(data), self.num_slots)):
                self.slots[i] = data[i]
