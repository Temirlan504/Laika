"""
Inventory system for managing player items.
"""
from items import get_item

class InventorySlot:
    """Represents a single inventory slot"""
    def __init__(self, item_id=None, quantity=0):
        self.item_id = item_id
        self.quantity = quantity
    
    def is_empty(self):
        return self.item_id is None or self.quantity <= 0
    
    def clear(self):
        self.item_id = None
        self.quantity = 0
    
    def can_add(self, item_id, amount=1):
        """Check if we can add items to this slot"""
        if self.is_empty():
            return True
        
        if self.item_id != item_id:
            return False
        
        item_def = get_item(item_id)
        if not item_def:
            return False
        
        return self.quantity + amount <= item_def.max_stack
    
    def add(self, item_id, amount=1):
        """Add items to this slot. Returns remaining amount that couldn't fit."""
        if self.is_empty():
            self.item_id = item_id
            item_def = get_item(item_id)
            self.quantity = min(amount, item_def.max_stack)
            return max(0, amount - item_def.max_stack)
        
        if self.item_id != item_id:
            return amount
        
        item_def = get_item(item_id)
        space_left = item_def.max_stack - self.quantity
        added = min(amount, space_left)
        self.quantity += added
        return amount - added
    
    def remove(self, amount=1):
        """Remove items from this slot. Returns actual amount removed."""
        if self.is_empty():
            return 0
        
        removed = min(amount, self.quantity)
        self.quantity -= removed
        
        if self.quantity <= 0:
            self.clear()
        
        return removed


class Inventory:
    """Main inventory system"""
    def __init__(self, size=30):
        self.size = size
        self.slots = [InventorySlot() for _ in range(size)]
    
    def add_item(self, item_id, amount=1):
        """
        Add items to inventory.
        Returns True if all items were added, False if inventory was full.
        """
        item_def = get_item(item_id)
        if not item_def:
            print(f"Warning: Unknown item '{item_id}'")
            return False
        
        remaining = amount
        
        # First, try to add to existing stacks
        for slot in self.slots:
            if slot.item_id == item_id and not slot.is_empty():
                remaining = slot.add(item_id, remaining)
                if remaining <= 0:
                    print(f"Added {amount}x {item_def.name} (Total: {self.count_item(item_id)})")
                    return True
        
        # Then, try to add to empty slots
        for slot in self.slots:
            if slot.is_empty():
                remaining = slot.add(item_id, remaining)
                if remaining <= 0:
                    print(f"Added {amount}x {item_def.name} (Total: {self.count_item(item_id)})")
                    return True
        
        # If there's still remaining, inventory is full
        if remaining > 0:
            added = amount - remaining
            if added > 0:
                print(f"Added {added}x {item_def.name} (Inventory full, {remaining} lost)")
            else:
                print(f"Inventory full! Could not add {item_def.name}")
            return False
        
        return True
    
    def remove_item(self, item_id, amount=1):
        """
        Remove items from inventory.
        Returns True if all items were removed, False if not enough items.
        """
        if not self.has_item(item_id, amount):
            return False
        
        remaining = amount
        
        for slot in self.slots:
            if slot.item_id == item_id:
                removed = slot.remove(remaining)
                remaining -= removed
                if remaining <= 0:
                    break
        
        item_def = get_item(item_id)
        print(f"Removed {amount}x {item_def.name} (Remaining: {self.count_item(item_id)})")
        return True
    
    def has_item(self, item_id, amount=1):
        """Check if inventory has at least 'amount' of item_id"""
        return self.count_item(item_id) >= amount
    
    def count_item(self, item_id):
        """Count total amount of item_id in inventory"""
        total = 0
        for slot in self.slots:
            if slot.item_id == item_id:
                total += slot.quantity
        return total
    
    def get_slot(self, index):
        """Get slot at index"""
        if 0 <= index < self.size:
            return self.slots[index]
        return None
    
    def find_item_slot(self, item_id):
        """Find first slot containing item_id, returns index or -1"""
        for i, slot in enumerate(self.slots):
            if slot.item_id == item_id and not slot.is_empty():
                return i
        return -1
    
    def get_all_items(self):
        """Returns a list of (item_id, quantity) tuples for all non-empty slots"""
        items = []
        for slot in self.slots:
            if not slot.is_empty():
                items.append((slot.item_id, slot.quantity))
        return items
    
    def clear(self):
        """Clear all inventory slots"""
        for slot in self.slots:
            slot.clear()
    
    def is_full(self):
        """Check if inventory is completely full"""
        return all(not slot.is_empty() for slot in self.slots)
    
    def get_free_slots(self):
        """Count number of completely empty slots"""
        return sum(1 for slot in self.slots if slot.is_empty())
