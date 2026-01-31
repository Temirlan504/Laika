"""
Inventory UI - Visual display of the player's inventory
"""
import pygame
from items import get_item

class InventoryUI:
    def __init__(self, screen, inventory):
        self.screen = screen
        self.inventory = inventory
        self.visible = False
        
        # UI Settings
        self.slot_size = 64
        self.padding = 8
        self.columns = 6
        self.rows = (inventory.size + self.columns - 1) // self.columns
        
        # Colors
        self.bg_color = (40, 40, 50, 220)
        self.slot_color = (60, 60, 70)
        self.slot_hover_color = (80, 80, 90)
        self.slot_selected_color = (100, 120, 140)
        self.border_color = (200, 200, 200)
        self.text_color = (255, 255, 255)
        
        # Calculate panel size and position
        self.width = self.columns * (self.slot_size + self.padding) + self.padding
        self.height = self.rows * (self.slot_size + self.padding) + self.padding + 60  # +60 for title
        self.x = (screen.get_width() - self.width) // 2
        self.y = (screen.get_height() - self.height) // 2
        
        # Fonts
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 20)
        
        # Selection
        self.selected_slot = None
        self.hovered_slot = None
        
        # Item icons (placeholder - you can replace with actual images)
        self.item_icons = {}
        self.load_placeholder_icons()
    
    def load_placeholder_icons(self):
        """Create simple colored squares as placeholder icons"""
        # You can replace this with actual image loading later
        colors = {
            "iron_ore": (150, 150, 150),
            "ice": (150, 200, 255),
            "regolith": (139, 69, 19),
            "potato_seed": (200, 180, 100),
            "tomato_seed": (200, 50, 50),
            "corn_seed": (255, 220, 100),
            "potato": (200, 150, 100),
            "tomato": (255, 100, 100),
            "corn": (255, 220, 150),
            "hoe": (100, 100, 100),
            "pickaxe": (120, 120, 120),
            "watering_can": (100, 150, 200),
            "iron_ingot": (180, 180, 200),
        }
        
        for item_id, color in colors.items():
            surface = pygame.Surface((48, 48))
            surface.fill(color)
            pygame.draw.rect(surface, (0, 0, 0), surface.get_rect(), 2)
            self.item_icons[item_id] = surface
    
    def toggle(self):
        """Toggle inventory visibility"""
        self.visible = not self.visible
    
    def show(self):
        self.visible = True
    
    def hide(self):
        self.visible = False
    
    def get_slot_at_mouse(self, mouse_pos):
        """Get slot index at mouse position, or None"""
        if not self.visible:
            return None
        
        mx, my = mouse_pos
        
        # Check if mouse is within inventory panel
        if not (self.x <= mx <= self.x + self.width and 
                self.y + 60 <= my <= self.y + self.height):
            return None
        
        # Calculate slot position
        rel_x = mx - self.x - self.padding
        rel_y = my - self.y - 60 - self.padding
        
        col = rel_x // (self.slot_size + self.padding)
        row = rel_y // (self.slot_size + self.padding)
        
        if 0 <= col < self.columns and 0 <= row < self.rows:
            slot_index = int(row * self.columns + col)
            if slot_index < self.inventory.size:
                return slot_index
        
        return None
    
    def handle_click(self, mouse_pos):
        """Handle mouse click on inventory"""
        if not self.visible:
            return
        
        slot_index = self.get_slot_at_mouse(mouse_pos)
        if slot_index is not None:
            self.selected_slot = slot_index
            slot = self.inventory.get_slot(slot_index)
            if not slot.is_empty():
                item_def = get_item(slot.item_id)
                print(f"Selected: {item_def.name} x{slot.quantity}")
    
    def handle_hover(self, mouse_pos):
        """Update hovered slot"""
        if not self.visible:
            self.hovered_slot = None
            return
        
        self.hovered_slot = self.get_slot_at_mouse(mouse_pos)
    
    def draw(self):
        """Draw the inventory UI"""
        if not self.visible:
            return
        
        # Create semi-transparent background
        bg_surface = pygame.Surface((self.width, self.height))
        bg_surface.set_alpha(220)
        bg_surface.fill(self.bg_color)
        self.screen.blit(bg_surface, (self.x, self.y))
        
        # Draw border
        pygame.draw.rect(self.screen, self.border_color, 
                        (self.x, self.y, self.width, self.height), 3)
        
        # Draw title
        title_text = self.title_font.render("Inventory", True, self.text_color)
        title_rect = title_text.get_rect(center=(self.x + self.width // 2, self.y + 30))
        self.screen.blit(title_text, title_rect)
        
        # Draw slots
        for i in range(self.inventory.size):
            self.draw_slot(i)
        
        # Draw tooltip for hovered slot
        if self.hovered_slot is not None:
            self.draw_tooltip(self.hovered_slot)
    
    def draw_slot(self, slot_index):
        """Draw a single inventory slot"""
        row = slot_index // self.columns
        col = slot_index % self.columns
        
        x = self.x + self.padding + col * (self.slot_size + self.padding)
        y = self.y + 60 + self.padding + row * (self.slot_size + self.padding)
        
        # Determine slot color
        slot_color = self.slot_color
        if slot_index == self.selected_slot:
            slot_color = self.slot_selected_color
        elif slot_index == self.hovered_slot:
            slot_color = self.slot_hover_color
        
        # Draw slot background
        pygame.draw.rect(self.screen, slot_color, (x, y, self.slot_size, self.slot_size))
        pygame.draw.rect(self.screen, self.border_color, 
                        (x, y, self.slot_size, self.slot_size), 2)
        
        # Draw item if slot is not empty
        slot = self.inventory.get_slot(slot_index)
        if not slot.is_empty():
            item_def = get_item(slot.item_id)
            
            # Draw item icon
            if slot.item_id in self.item_icons:
                icon = self.item_icons[slot.item_id]
                icon_rect = icon.get_rect(center=(x + self.slot_size // 2, 
                                                   y + self.slot_size // 2))
                self.screen.blit(icon, icon_rect)
            
            # Draw quantity
            if slot.quantity > 1:
                qty_text = self.small_font.render(str(slot.quantity), True, self.text_color)
                qty_rect = qty_text.get_rect(bottomright=(x + self.slot_size - 4, 
                                                           y + self.slot_size - 4))
                # Draw shadow
                shadow_rect = qty_rect.copy()
                shadow_rect.x += 1
                shadow_rect.y += 1
                shadow_text = self.small_font.render(str(slot.quantity), True, (0, 0, 0))
                self.screen.blit(shadow_text, shadow_rect)
                self.screen.blit(qty_text, qty_rect)
    
    def draw_tooltip(self, slot_index):
        """Draw tooltip for hovered slot"""
        slot = self.inventory.get_slot(slot_index)
        if slot.is_empty():
            return
        
        item_def = get_item(slot.item_id)
        if not item_def:
            return
        
        # Prepare tooltip text
        lines = [
            item_def.name,
            f"Quantity: {slot.quantity}/{item_def.max_stack}",
            item_def.description
        ]
        
        # Calculate tooltip size
        line_height = 24
        tooltip_padding = 10
        tooltip_width = max(self.font.render(line, True, self.text_color).get_width() for line in lines) + tooltip_padding * 2
        tooltip_height = len(lines) * line_height + tooltip_padding * 2
        
        # Position tooltip near mouse
        mouse_x, mouse_y = pygame.mouse.get_pos()
        tooltip_x = mouse_x + 15
        tooltip_y = mouse_y + 15
        
        # Keep tooltip on screen
        if tooltip_x + tooltip_width > self.screen.get_width():
            tooltip_x = mouse_x - tooltip_width - 15
        if tooltip_y + tooltip_height > self.screen.get_height():
            tooltip_y = mouse_y - tooltip_height - 15
        
        # Draw tooltip background
        tooltip_surface = pygame.Surface((tooltip_width, tooltip_height))
        tooltip_surface.fill((30, 30, 40))
        tooltip_surface.set_alpha(240)
        self.screen.blit(tooltip_surface, (tooltip_x, tooltip_y))
        
        # Draw tooltip border
        pygame.draw.rect(self.screen, self.border_color,
                        (tooltip_x, tooltip_y, tooltip_width, tooltip_height), 2)
        
        # Draw text lines
        for i, line in enumerate(lines):
            text_surface = self.font.render(line, True, self.text_color)
            text_y = tooltip_y + tooltip_padding + i * line_height
            self.screen.blit(text_surface, (tooltip_x + tooltip_padding, text_y))
