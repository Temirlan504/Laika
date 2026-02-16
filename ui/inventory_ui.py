import pygame
import os
from items import get_item
from ui.ui_config import ui_config

class InventoryUI:
    def __init__(self, screen, inventory, hotbar):
        self.screen = screen
        self.inventory = inventory
        self.hotbar = hotbar  # Add hotbar reference
        self.visible = False

        # Load background image
        self.bg_image = ui_config.get_image('inventory_bg')
        self.bg_image = pygame.transform.scale(self.bg_image, (600, 600)) if self.bg_image else None
        
        self.panel_width = 600
        self.panel_height = 600

        self.slot_size = 64
        self.slot_gap = 13

        self.grid_start_x = 75
        self.grid_start_y = 75
        self.cols = 6
        self.rows = 6
        
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
        
        # Add hotbar slot rendering (MUST be after grid_start_y and rows are defined)
        self.hotbar_start_y = self.grid_start_y + self.rows * (self.slot_size + self.slot_gap) + 30

    def get_hotbar_slot_rect(self, slot_index):
        """Get the rect for a hotbar slot in the inventory screen"""
        panel_x = (self.screen.get_width() - self.panel_width) // 2
        panel_y = (self.screen.get_height() - self.panel_height) // 2
        
        # Center the hotbar row
        hotbar_width = self.hotbar.num_slots * (self.slot_size + self.slot_gap) - self.slot_gap
        hotbar_start_x = (self.panel_width - hotbar_width) // 2
        
        slot_x = panel_x + hotbar_start_x + slot_index * (self.slot_size + self.slot_gap)
        slot_y = panel_y + self.hotbar_start_y
        
        return pygame.Rect(slot_x, slot_y, self.slot_size, self.slot_size)

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
        """Get the slot index at the given mouse position
        Returns: ('inventory', index) or ('hotbar', index) or None"""
        if not self.visible:
            return None
        
        # Check inventory slots
        for i in range(self.inventory.size):
            rect = self.get_slot_rect(i)
            if rect.collidepoint(pos):
                return ('inventory', i)
        
        # Check hotbar slots
        for i in range(self.hotbar.num_slots):
            rect = self.get_hotbar_slot_rect(i)
            if rect.collidepoint(pos):
                return ('hotbar', i)
        
        return None
    
    def handle_mouse_down(self, pos, button):
        """Handle mouse button down event"""
        if not self.visible:
            return None
        
        if button == 1:  # Left click
            slot_info = self.get_slot_at_pos(pos)
            if slot_info:
                storage_type, slot_index = slot_info
                
                # Get the slot data
                if storage_type == 'inventory':
                    slot = self.inventory.get_slot(slot_index)
                    rect = self.get_slot_rect(slot_index)
                else:  # hotbar
                    slot = self.hotbar.get_slot(slot_index)
                    rect = self.get_hotbar_slot_rect(slot_index)
                
                if slot:
                    # Start dragging
                    self.dragging = True
                    self.dragged_slot = (storage_type, slot_index)
                    self.drag_offset = (pos[0] - rect.centerx, pos[1] - rect.centery)
                    return slot_info
        
        elif button == 3:  # Right click
            slot_info = self.get_slot_at_pos(pos)
            if slot_info:
                return slot_info
        
        return None

    def handle_mouse_up(self, pos, button):
        """Handle mouse button up event"""
        if not self.visible:
            return None
        
        if button == 1 and self.dragging:  # Left click release
            from_info = self.dragged_slot
            to_info = self.get_slot_at_pos(pos)
            
            self.cancel_drag()
            
            if from_info and to_info:
                return (from_info, to_info, 'swap')
        
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
        slot_info = self.get_slot_at_pos(mouse_pos)
        self.hovered_slot = slot_info
        
        # Show tooltip if hovering over a slot with an item (and not dragging)
        if slot_info and not self.dragging:
            storage_type, slot_index = slot_info
            slot = self.inventory.get_slot(slot_index) if storage_type == 'inventory' else self.hotbar.get_slot(slot_index)
            
            if slot:
                self.tooltip_slot = slot_info
                self.show_tooltip = True
            else:
                self.show_tooltip = False
        else:
            self.show_tooltip = False

    def swap_slots(self, from_info, to_info):
        """Swap items between two slots (can be inventory or hotbar)"""
        from_type, from_index = from_info
        to_type, to_index = to_info
        
        # Get slot data
        if from_type == 'inventory':
            from_slot = self.inventory.get_slot(from_index)
        else:
            from_slot = self.hotbar.get_slot(from_index)
        
        if to_type == 'inventory':
            to_slot = self.inventory.get_slot(to_index)
        else:
            to_slot = self.hotbar.get_slot(to_index)
        
        # Swap
        if from_type == 'inventory':
            self.inventory.set_slot(from_index, to_slot)
        else:
            self.hotbar.set_slot(from_index, to_slot)
        
        if to_type == 'inventory':
            self.inventory.set_slot(to_index, from_slot)
        else:
            self.hotbar.set_slot(to_index, from_slot)
        
        return True

    def stack_items(self, from_info, to_info):
        """Try to stack items from one slot to another"""
        from_type, from_index = from_info
        to_type, to_index = to_info
        
        # Get slots
        if from_type == 'inventory':
            from_slot = self.inventory.get_slot(from_index)
        else:
            from_slot = self.hotbar.get_slot(from_index)
        
        if to_type == 'inventory':
            to_slot = self.inventory.get_slot(to_index)
        else:
            to_slot = self.hotbar.get_slot(to_index)
        
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
            if from_type == 'inventory':
                self.inventory.set_slot(from_index, None)
            else:
                self.hotbar.set_slot(from_index, None)
        
        return True

    def draw_tooltip(self, slot_info):
        """Draw tooltip for an item"""
        storage_type, slot_index = slot_info
        
        if storage_type == 'inventory':
            slot = self.inventory.get_slot(slot_index)
        else:
            slot = self.hotbar.get_slot(slot_index)
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

        # Draw inventory items in slots
        for i in range(self.inventory.size):
            # Skip the dragged slot
            if self.dragging and self.dragged_slot == ('inventory', i):
                continue
            
            slot = self.inventory.get_slot(i)
            if slot:
                rect = self.get_slot_rect(i)
                self.draw_item_in_slot(slot, rect)
        
        # Draw hotbar section label
        panel_x = (self.screen.get_width() - self.panel_width) // 2
        panel_y = (self.screen.get_height() - self.panel_height) // 2
        
        hotbar_label = self.title_font.render("HOTBAR", True, ui_config.LIGHT_ORANGE)
        hotbar_label_rect = hotbar_label.get_rect(
            centerx=panel_x + self.panel_width // 2,
            bottom=panel_y + self.hotbar_start_y - 10
        )
        self.screen.blit(hotbar_label, hotbar_label_rect)
        
        # Draw hotbar slots
        for i in range(self.hotbar.num_slots):
            rect = self.get_hotbar_slot_rect(i)
            
            # Draw slot background
            pygame.draw.rect(self.screen, (60, 60, 60), rect)
            pygame.draw.rect(self.screen, (100, 100, 100), rect, 2)
            
            # Skip the dragged slot
            if self.dragging and self.dragged_slot == ('hotbar', i):
                continue
            
            slot = self.hotbar.get_slot(i)
            if slot:
                self.draw_item_in_slot(slot, rect)

        # Draw dragged item (if dragging)
        if self.dragging and self.dragged_slot:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            drag_rect = pygame.Rect(0, 0, self.slot_size, self.slot_size)
            drag_rect.center = (mouse_x - self.drag_offset[0], 
                               mouse_y - self.drag_offset[1])
            
            storage_type, slot_index = self.dragged_slot
            if storage_type == 'inventory':
                slot = self.inventory.get_slot(slot_index)
            else:
                slot = self.hotbar.get_slot(slot_index)
            
            if slot:
                self.draw_item_in_slot(slot, drag_rect, alpha=200)

        # Draw tooltip
        if self.show_tooltip and self.tooltip_slot:
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
