import pygame
import os
from items import get_item
from ui.ui_config import ui_config

class ChestUI:
    def __init__(self, screen, player_inventory, chest_inventory):
        self.screen = screen
        self.player_inventory = player_inventory
        self.chest_inventory = chest_inventory
        self.visible = True

        self.slot_size = 72  # Match InventoryUI
        self.padding = 8
        self.cols = 6

        self.dragging = False
        self.drag_source_inventory = None
        self.drag_source_slot = None

        self.font = ui_config.get_font(16)
        self.title_font = ui_config.get_font(24)
        self.item_font = ui_config.get_font(12)
        self.qty_font = ui_config.get_font(16)

        # Panel dimensions
        self.panel_width = 500
        self.panel_height = 400
        
        # Calculate centered positions
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        
        # Center both panels vertically, space them horizontally
        spacing = 40
        total_width = self.panel_width * 2 + spacing
        start_x = (screen_width - total_width) // 2
        center_y = (screen_height - self.panel_height) // 2
        
        self.player_panel = pygame.Rect(start_x, center_y, self.panel_width, self.panel_height)
        self.chest_panel = pygame.Rect(start_x + self.panel_width + spacing, center_y, self.panel_width, self.panel_height)

    def close(self):
        self.visible = False

    # ----------------- SLOT HELPERS -----------------

    def get_slot_at_pos(self, pos, panel, inventory):
        for i in range(inventory.size):
            rect = self.get_slot_rect(panel, i)
            if rect.collidepoint(pos):
                return i
        return None

    def get_slot_rect(self, panel, index):
        row = index // self.cols
        col = index % self.cols

        x = panel.x + 20 + col * (self.slot_size + self.padding)
        y = panel.y + 60 + row * (self.slot_size + self.padding)

        return pygame.Rect(x, y, self.slot_size, self.slot_size)
    
    
    # ----------------- DRAG & DROP -----------------
    def handle_mouse_down(self, pos):
        if not self.visible:
            return

        # Player inventory
        slot = self.get_slot_at_pos(pos, self.player_panel, self.player_inventory)
        if slot is not None:
            if self.player_inventory.get_slot(slot):
                self.start_drag(self.player_inventory, slot)
                return

        # Chest inventory
        slot = self.get_slot_at_pos(pos, self.chest_panel, self.chest_inventory)
        if slot is not None:
            if self.chest_inventory.get_slot(slot):
                self.start_drag(self.chest_inventory, slot)

    def start_drag(self, inventory, slot_index):
        self.dragging = True
        self.drag_source_inventory = inventory
        self.drag_source_slot = slot_index

    def handle_mouse_up(self, pos):
        if not self.dragging:
            return

        source = self.drag_source_inventory
        source_slot = self.drag_source_slot
        slot_data = source.get_slot(source_slot)

        if not slot_data:
            self.cancel_drag()
            return

        # Drop onto player inventory
        target_slot = self.get_slot_at_pos(pos, self.player_panel, self.player_inventory)
        if target_slot is not None:
            self.try_drop(source, self.player_inventory, source_slot, target_slot)
            self.cancel_drag()
            return

        # Drop onto chest inventory
        target_slot = self.get_slot_at_pos(pos, self.chest_panel, self.chest_inventory)
        if target_slot is not None:
            self.try_drop(source, self.chest_inventory, source_slot, target_slot)
            self.cancel_drag()
            return

        # Dropped nowhere → cancel
        self.cancel_drag()

    def try_drop(self, source, target, from_slot, to_slot):
        from_data = source.get_slot(from_slot)
        to_data = target.get_slot(to_slot)

        # Empty target → move
        if to_data is None:
            target.set_slot(to_slot, from_data)
            source.set_slot(from_slot, None)
            return

        # Same item → stack
        if from_data["item_id"] == to_data["item_id"]:
            item = get_item(from_data["item_id"])
            space = item.max_stack - to_data["quantity"]
            if space > 0:
                moved = min(space, from_data["quantity"])
                to_data["quantity"] += moved
                from_data["quantity"] -= moved
                if from_data["quantity"] <= 0:
                    source.set_slot(from_slot, None)
                return

        # Otherwise → swap
        source.set_slot(from_slot, to_data)
        target.set_slot(to_slot, from_data)

    def cancel_drag(self):
        self.dragging = False
        self.drag_source_inventory = None
        self.drag_source_slot = None

    # ----------------- DRAW -----------------

    def draw_item_in_slot(self, slot, rect, alpha=255):
        """Draw an item inside a slot with image (like InventoryUI)"""
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
                    print(f"[CHEST_UI] Error loading {path}: {e}")
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

    def draw_panel(self, panel, title, inventory):
        # Draw panel background
        pygame.draw.rect(self.screen, ui_config.BLACK, panel)
        pygame.draw.rect(self.screen, ui_config.WHITE, panel, 2)

        # Draw title
        title_surf = self.title_font.render(title, True, ui_config.WHITE)
        title_rect = title_surf.get_rect(centerx=panel.centerx, y=panel.y + 15)
        self.screen.blit(title_surf, title_rect)

        # Draw slots
        for i in range(inventory.size):
            # Skip the dragged slot (we'll draw it separately)
            if self.dragging and self.drag_source_inventory == inventory and i == self.drag_source_slot:
                continue
                
            rect = self.get_slot_rect(panel, i)
            pygame.draw.rect(self.screen, ui_config.DARK_GRAY, rect)
            pygame.draw.rect(self.screen, ui_config.WHITE, rect, 1)

            slot = inventory.get_slot(i)
            if slot:
                self.draw_item_in_slot(slot, rect)

    def draw(self):
        if not self.visible:
            return

        self.draw_panel(self.player_panel, "INVENTORY", self.player_inventory)
        self.draw_panel(self.chest_panel, "CHEST", self.chest_inventory)

        # Draw dragged item following mouse
        if self.dragging and self.drag_source_slot is not None:
            slot = self.drag_source_inventory.get_slot(self.drag_source_slot)
            if slot:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                drag_rect = pygame.Rect(0, 0, self.slot_size, self.slot_size)
                drag_rect.center = (mouse_x, mouse_y)
                
                # Draw with transparency
                self.draw_item_in_slot(slot, drag_rect, alpha=200)
