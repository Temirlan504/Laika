import pygame
import os
from items import get_item
from ui.ui_config import ui_config

class InventoryUI:
    def __init__(self, screen, inventory):
        self.screen = screen
        self.inventory = inventory
        self.visible = False

        # Load background image
        self.bg_image = ui_config.get_image('inventory_bg')
        
        # DEBUG: Check if image loaded
        if self.bg_image:
            print(f"[INVENTORY] Background image loaded: {self.bg_image.get_width()}x{self.bg_image.get_height()}")
        else:
            print("[INVENTORY] WARNING: No background image loaded!")
        
        # Inventory layout settings based on design
        # Background: 540x505px
        # Title area: 58px from top
        # Side decorations: 15px left and right
        # Bottom decoration: 16px
        # Inventory area: 510x430px
        # Slot size: 72x72px
        # Padding: 20px sides, 16px top, 25px bottom
        # Gap between slots: 6px
        
        self.panel_width = 540
        self.panel_height = 505
        
        self.slot_size = 72
        self.slot_gap = 6  # Space between slots
        
        # Grid positioning (from top-left of panel)
        # Left decoration (15px) + left padding (20px) = 35px from left edge
        self.grid_start_x = 35
        # Title (58px) + top padding (16px) = 74px from top edge
        self.grid_start_y = 74
        
        # Calculate cols and rows based on inventory area and slot size
        # Available width: 510px - 40px (left+right padding) = 470px
        # Available height: 430px - 41px (top+bottom padding) = 389px
        # With 6px gaps: (72 + 6) * cols - 6 = 470 → cols = 6
        # With 6px gaps: (72 + 6) * rows - 6 = 389 → rows = 5
        self.cols = 6
        self.rows = 5
        
        # Fonts
        self.title_font = ui_config.get_font(24)
        self.item_font = ui_config.get_font(12)
        self.qty_font = ui_config.get_font(16)

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
        # Calculate panel position (centered on screen)
        panel_x = (self.screen.get_width() - self.panel_width) // 2
        panel_y = (self.screen.get_height() - self.panel_height) // 2
        
        # Calculate slot position within grid
        row = slot_index // self.cols
        col = slot_index % self.cols
        
        # Account for gaps between slots
        slot_x = panel_x + self.grid_start_x + col * (self.slot_size + self.slot_gap)
        slot_y = panel_y + self.grid_start_y + row * (self.slot_size + self.slot_gap)

        return pygame.Rect(slot_x, slot_y, self.slot_size, self.slot_size)

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
    
    def handle_event(self, event):
        """Handle pygame events for inventory interaction"""
        if not self.visible:
            return
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                slot_index = self.get_slot_at_pos(event.pos)
                if slot_index is not None:
                    slot = self.inventory.get_slot(slot_index)
                    if slot:
                        # Start dragging
                        self.dragging = True
                        self.dragged_slot = slot_index
                        rect = self.get_slot_rect(slot_index)
                        self.drag_offset = (event.pos[0] - rect.centerx, 
                                          event.pos[1] - rect.centery)
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.dragging:  # Left click release
                from_slot = self.dragged_slot
                to_slot = self.get_slot_at_pos(event.pos)
                
                if from_slot is not None and to_slot is not None:
                    # Try to stack first, then swap if stacking fails
                    if not self.stack_items(from_slot, to_slot):
                        self.swap_slots(from_slot, to_slot)
                
                self.cancel_drag()

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
            f"Qty: {slot['quantity']}",
            item.description
        ]
        
        # Calculate tooltip size
        padding = 10
        line_height = 22
        tooltip_font = ui_config.get_font(14)
        max_width = max(tooltip_font.render(line, True, ui_config.WHITE).get_width() for line in lines)
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
        tooltip_surface = pygame.Surface((tooltip_width, tooltip_height))
        tooltip_surface.fill(ui_config.DARK_GRAY)
        self.screen.blit(tooltip_surface, (tooltip_x, tooltip_y))
        
        # Draw border
        pygame.draw.rect(self.screen, ui_config.LIGHT_GRAY, 
                        (tooltip_x, tooltip_y, tooltip_width, tooltip_height), 2)
        
        # Draw text
        y_offset = tooltip_y + padding
        for i, line in enumerate(lines):
            color = ui_config.LIGHT_ORANGE if i == 0 else ui_config.WHITE
            text = tooltip_font.render(line, True, color)
            self.screen.blit(text, (tooltip_x + padding, y_offset))
            y_offset += line_height

    def draw(self):
        if not self.visible:
            return

        # Calculate panel position (centered on screen)
        panel_x = (self.screen.get_width() - self.panel_width) // 2
        panel_y = (self.screen.get_height() - self.panel_height) // 2
        
        # Draw background image or fallback
        if self.bg_image:
            self.screen.blit(self.bg_image, (panel_x, panel_y))
        else:
            # Fallback: simple gray panel
            panel_surface = pygame.Surface((self.panel_width, self.panel_height))
            panel_surface.fill(ui_config.DARK_GRAY)
            self.screen.blit(panel_surface, (panel_x, panel_y))
            
            # Draw title on fallback
            title_text = self.title_font.render("INVENTORY", True, ui_config.WHITE)
            title_rect = title_text.get_rect(centerx=panel_x + self.panel_width // 2, 
                                            y=panel_y + 15)
            self.screen.blit(title_text, title_rect)

        # Draw items in slots
        for i in range(self.inventory.size):
            # Skip the dragged slot (we'll draw it separately)
            if self.dragging and i == self.dragged_slot:
                continue
            
            slot = self.inventory.get_slot(i)
            if slot:
                rect = self.get_slot_rect(i)
                self.draw_item_in_slot(slot, rect)

        # Draw dragged item (if dragging)
        if self.dragging and self.dragged_slot is not None:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            drag_rect = pygame.Rect(0, 0, self.slot_size, self.slot_size)
            drag_rect.center = (mouse_x - self.drag_offset[0], 
                               mouse_y - self.drag_offset[1])
            
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
        
        # Try to load item sprite/texture from multiple possible paths
        item_image = None
        item_id = slot['item_id']
        
        # Try different paths (in order of preference)
        possible_paths = [
            f"assets/items/{item_id}.png",              # Flat structure
            f"assets/items/tools/{item_id}.png",        # Tools subfolder
            f"assets/items/seeds/{item_id}.png",        # Seeds subfolder
            f"assets/items/crops/{item_id}.png",        # Crops subfolder
            f"assets/items/resources/{item_id}.png",    # Resources subfolder
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    item_image = pygame.image.load(path).convert_alpha()
                    # Scale to fit slot (leave some padding)
                    image_size = int(self.slot_size * 0.7)  # 70% of slot size
                    item_image = pygame.transform.smoothscale(item_image, (image_size, image_size))
                    break
                except Exception as e:
                    print(f"[INVENTORY] Error loading {path}: {e}")
                    item_image = None
        
        if item_image:
            # Draw item image centered in slot
            image_rect = item_image.get_rect(center=rect.center)
            
            if alpha < 255:
                # Apply transparency
                temp_surface = item_image.copy()
                temp_surface.set_alpha(alpha)
                self.screen.blit(temp_surface, image_rect)
            else:
                self.screen.blit(item_image, image_rect)
        else:
            # Fallback: draw item name as text
            name_text = item.name
            if len(name_text) > 8:
                name_text = name_text[:6] + ".."
            
            if alpha < 255:
                text_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                name = self.item_font.render(name_text, True, (*ui_config.WHITE, alpha))
                text_surface.blit(name, (4, 4))
                self.screen.blit(text_surface, rect)
            else:
                name = self.item_font.render(name_text, True, ui_config.WHITE)
                self.screen.blit(name, (rect.x + 4, rect.y + 4))
        
        # Draw quantity in bottom-right corner
        qty_text = str(slot["quantity"])
        
        if alpha < 255:
            text_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            qty = self.qty_font.render(qty_text, True, (*ui_config.WHITE, alpha))
            text_surface.blit(qty, (rect.width - 22, rect.height - 22))
            self.screen.blit(text_surface, rect)
        else:
            qty = self.qty_font.render(qty_text, True, ui_config.WHITE)
            self.screen.blit(qty, (rect.right - 22, rect.bottom - 22))
