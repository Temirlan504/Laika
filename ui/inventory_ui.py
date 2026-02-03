import pygame
from items import get_item

class InventoryUI:
    def __init__(self, screen, inventory):
        self.screen = screen
        self.inventory = inventory
        self.visible = False

        self.cols = 6
        self.slot_size = int(self.screen.get_width() * 0.06)
        self.padding = int(self.slot_size * 0.15)

        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)

        # Colors
        self.bg_color = (30, 30, 40, 240)  # Semi-transparent background
        self.slot_color = (60, 60, 80)
        self.slot_hover = (90, 90, 120)
        self.slot_selected = (120, 120, 160)

        # Hover and interaction state
        self.hovered_slot = None
        
        # Drag and drop state
        self.dragging = False
        self.dragged_slot = None
        self.drag_offset = (0, 0)
        
        # Tooltip
        self.show_tooltip = False
        self.tooltip_slot = None

    def toggle(self):
        self.visible = not self.visible
        if not self.visible:
            # Cancel any drag operation when closing
            self.cancel_drag()

    def hide(self):
        self.visible = False
        self.cancel_drag()

    def cancel_drag(self):
        """Cancel current drag operation"""
        self.dragging = False
        self.dragged_slot = None
        self.drag_offset = (0, 0)

    def get_slot_rect(self, slot_index):
        """Get the rect for a specific inventory slot"""
        rows = (self.inventory.size + self.cols - 1) // self.cols
        panel_height = rows * self.slot_size + self.padding * 2
        
        # Center the inventory on screen
        start_x = (self.screen.get_width() - self.cols * self.slot_size) // 2
        start_y = (self.screen.get_height() - panel_height) // 2

        row = slot_index // self.cols
        col = slot_index % self.cols

        return pygame.Rect(
            start_x + col * self.slot_size,
            start_y + row * self.slot_size + self.padding,
            self.slot_size,
            self.slot_size
        )

    def get_slot_at_pos(self, pos):
        """Get the slot index at the given mouse position, or None"""
        if not self.visible:
            return None
        
        for i in range(self.inventory.size):
            rect = self.get_slot_rect(i)
            if rect.collidepoint(pos):
                return i
        return None

    def handle_mouse_down(self, pos, button):
        """Handle mouse button down event"""
        if not self.visible:
            return None
        
        if button == 1:  # Left click
            slot_index = self.get_slot_at_pos(pos)
            if slot_index is not None:
                slot = self.inventory.get_slot(slot_index)
                if slot:
                    # Start dragging
                    self.dragging = True
                    self.dragged_slot = slot_index
                    rect = self.get_slot_rect(slot_index)
                    self.drag_offset = (pos[0] - rect.centerx, pos[1] - rect.centery)
                    return slot_index
        
        elif button == 3:  # Right click
            slot_index = self.get_slot_at_pos(pos)
            if slot_index is not None:
                return slot_index
        
        return None

    def handle_mouse_up(self, pos, button):
        """Handle mouse button up event - returns (from_slot, to_slot, action_type)"""
        if not self.visible:
            return None
        
        if button == 1 and self.dragging:  # Left click release
            from_slot = self.dragged_slot
            to_slot = self.get_slot_at_pos(pos)
            
            self.cancel_drag()
            
            if from_slot is not None and to_slot is not None:
                return (from_slot, to_slot, 'swap')
        
        return None

    def handle_click(self, mouse_pos):
        """Handle mouse clicks - returns clicked slot index or None (for compatibility)"""
        if not self.visible:
            return None
        
        if self.hovered_slot is not None:
            return self.hovered_slot
        return None

    def handle_hover(self, mouse_pos):
        """Alias for update() - for compatibility with greenhouse.py"""
        self.update()

    def update(self):
        """Update hover state and tooltip"""
        if not self.visible:
            self.hovered_slot = None
            self.tooltip_slot = None
            self.show_tooltip = False
            return

        mouse_pos = pygame.mouse.get_pos()
        self.hovered_slot = self.get_slot_at_pos(mouse_pos)
        
        # Show tooltip if hovering over a slot with an item (and not dragging)
        if self.hovered_slot is not None and not self.dragging:
            slot = self.inventory.get_slot(self.hovered_slot)
            if slot:
                self.tooltip_slot = self.hovered_slot
                self.show_tooltip = True
            else:
                self.show_tooltip = False
        else:
            self.show_tooltip = False

    def swap_slots(self, from_index, to_index):
        """Swap items between two inventory slots"""
        if from_index == to_index:
            return True
        
        from_slot = self.inventory.get_slot(from_index)
        to_slot = self.inventory.get_slot(to_index)
        
        # Simple swap
        self.inventory.set_slot(from_index, to_slot)
        self.inventory.set_slot(to_index, from_slot)
        
        return True

    def stack_items(self, from_index, to_index):
        """Try to stack items from one slot to another"""
        from_slot = self.inventory.get_slot(from_index)
        to_slot = self.inventory.get_slot(to_index)
        
        if not from_slot or not to_slot:
            return False
        
        # Can only stack same items
        if from_slot["item_id"] != to_slot["item_id"]:
            return False
        
        item_def = get_item(from_slot["item_id"])
        if not item_def:
            return False
        
        # Calculate how much can be stacked
        space_available = item_def.max_stack - to_slot["quantity"]
        if space_available <= 0:
            return False
        
        # Stack items
        amount_to_move = min(from_slot["quantity"], space_available)
        to_slot["quantity"] += amount_to_move
        from_slot["quantity"] -= amount_to_move
        
        # If source slot is empty, clear it
        if from_slot["quantity"] <= 0:
            self.inventory.set_slot(from_index, None)
        
        return True

    def split_stack(self, slot_index):
        """Split a stack in half (for future shift+click functionality)"""
        slot = self.inventory.get_slot(slot_index)
        if not slot or slot["quantity"] <= 1:
            return False
        
        half = slot["quantity"] // 2
        remaining = slot["quantity"] - half
        
        # Find empty slot
        for i in range(self.inventory.size):
            if self.inventory.get_slot(i) is None:
                self.inventory.set_slot(i, {
                    "item_id": slot["item_id"],
                    "quantity": half
                })
                slot["quantity"] = remaining
                return True
        
        return False

    def draw_tooltip(self, slot_index):
        """Draw tooltip for an item"""
        slot = self.inventory.get_slot(slot_index)
        if not slot:
            return
        
        item = get_item(slot["item_id"])
        if not item:
            return
        
        mouse_x, mouse_y = pygame.mouse.get_pos()
        
        # Tooltip content
        lines = [
            item.name,
            f"Quantity: {slot['quantity']}",
            item.description
        ]
        
        # Calculate tooltip size
        padding = 8
        line_height = 20
        max_width = max(self.font.render(line, True, (255, 255, 255)).get_width() for line in lines)
        tooltip_width = max_width + padding * 2
        tooltip_height = len(lines) * line_height + padding * 2
        
        # Position tooltip (offset from mouse)
        tooltip_x = mouse_x + 15
        tooltip_y = mouse_y + 15
        
        # Keep tooltip on screen
        if tooltip_x + tooltip_width > self.screen.get_width():
            tooltip_x = mouse_x - tooltip_width - 15
        if tooltip_y + tooltip_height > self.screen.get_height():
            tooltip_y = mouse_y - tooltip_height - 15
        
        # Draw tooltip background
        tooltip_rect = pygame.Rect(tooltip_x, tooltip_y, tooltip_width, tooltip_height)
        pygame.draw.rect(self.screen, (20, 20, 30), tooltip_rect)
        pygame.draw.rect(self.screen, (100, 100, 120), tooltip_rect, 2)
        
        # Draw text
        y_offset = tooltip_y + padding
        for i, line in enumerate(lines):
            color = (255, 255, 100) if i == 0 else (220, 220, 220)  # Title in yellow
            text = self.font.render(line, True, color)
            self.screen.blit(text, (tooltip_x + padding, y_offset))
            y_offset += line_height

    def draw(self):
        if not self.visible:
            return

        # Calculate panel dimensions
        rows = (self.inventory.size + self.cols - 1) // self.cols
        panel_width = self.cols * self.slot_size + self.padding * 2
        panel_height = rows * self.slot_size + self.padding * 2 + 30  # +30 for title
        
        # Center panel on screen
        panel_x = (self.screen.get_width() - panel_width) // 2
        panel_y = (self.screen.get_height() - panel_height) // 2
        
        # Draw semi-transparent background panel
        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel_surface.fill(self.bg_color)
        self.screen.blit(panel_surface, (panel_x, panel_y))
        
        # Draw title
        title = self.font.render("Inventory", True, (255, 255, 255))
        title_rect = title.get_rect(centerx=self.screen.get_width() // 2, 
                                     y=panel_y + 5)
        self.screen.blit(title, title_rect)

        # Draw inventory slots
        for i in range(self.inventory.size):
            # Skip the dragged slot (we'll draw it separately)
            if self.dragging and i == self.dragged_slot:
                continue
            
            rect = self.get_slot_rect(i)
            
            # Determine slot color
            if i == self.hovered_slot and not self.dragging:
                color = self.slot_hover
            elif i == self.dragged_slot:
                color = self.slot_selected
            else:
                color = self.slot_color
            
            # Draw slot background
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, (0, 0, 0), rect, 2)
            
            # Draw item if present
            slot = self.inventory.get_slot(i)
            if slot:
                self.draw_item_in_slot(slot, rect)

        # Draw dragged item (if dragging)
        if self.dragging and self.dragged_slot is not None:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            drag_rect = pygame.Rect(0, 0, self.slot_size, self.slot_size)
            drag_rect.center = (mouse_x - self.drag_offset[0], 
                               mouse_y - self.drag_offset[1])
            
            # Draw with transparency
            drag_surface = pygame.Surface((self.slot_size, self.slot_size), pygame.SRCALPHA)
            pygame.draw.rect(drag_surface, (*self.slot_selected, 180), 
                           (0, 0, self.slot_size, self.slot_size))
            pygame.draw.rect(drag_surface, (255, 255, 255, 200), 
                           (0, 0, self.slot_size, self.slot_size), 2)
            
            self.screen.blit(drag_surface, drag_rect)
            
            # Draw item
            slot = self.inventory.get_slot(self.dragged_slot)
            if slot:
                self.draw_item_in_slot(slot, drag_rect, alpha=200)

        # Draw tooltip
        if self.show_tooltip and self.tooltip_slot is not None:
            self.draw_tooltip(self.tooltip_slot)

    def draw_item_in_slot(self, slot, rect, alpha=255):
        """Draw an item inside a slot"""
        item = get_item(slot["item_id"])
        if not item:
            return
        
        # Draw item name (truncated if needed)
        name_text = item.name
        if len(name_text) > 10:
            name_text = name_text[:8] + ".."
        
        if alpha < 255:
            # Create a surface for transparency
            text_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            name = self.small_font.render(name_text, True, (220, 220, 220, alpha))
            qty = self.font.render(str(slot["quantity"]), True, (255, 255, 255, alpha))
            text_surface.blit(name, (4, 4))
            text_surface.blit(qty, (rect.width - 20, rect.height - 24))
            self.screen.blit(text_surface, rect)
        else:
            name = self.small_font.render(name_text, True, (220, 220, 220))
            qty = self.font.render(str(slot["quantity"]), True, (255, 255, 255))
            self.screen.blit(name, (rect.x + 4, rect.y + 4))
            self.screen.blit(qty, (rect.right - 20, rect.bottom - 24))
