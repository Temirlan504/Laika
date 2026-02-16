import os
import pygame
from items import get_item
from ui.ui_element import UIElement
from ui.ui_config import ui_config

class DayUI(UIElement):
    def __init__(self, day_cycle, clock, screen):
        super().__init__()
        self.day_cycle = day_cycle
        self.clock = clock
        self.screen = screen
        
        # Fonts - customize sizes here
        self.day_font = ui_config.get_font(20)
        self.time_font = ui_config.get_font(15)
        
        # Panel size
        self.panel_width = 150
        self.panel_height = 70
        
        self.day = day_cycle.day
        day_cycle.subscribe(self)

    def on_new_day(self, day):
        self.day = day

    def draw(self):
        # Create dark gray background surface
        bg_surface = pygame.Surface((self.panel_width, self.panel_height))
        bg_surface.fill(ui_config.BLACK)
        
        # Position in top-right corner
        bg_x = self.screen.get_width() - self.panel_width - 20
        bg_y = 20
        
        # Draw background
        self.screen.blit(bg_surface, (bg_x, bg_y))
        
        # Draw text on top of the background
        day_text = f"SOL {self.day}"
        time_text = self.clock.time_string()
        
        day_surface = self.day_font.render(day_text, True, ui_config.LIGHT_ORANGE)
        time_surface = self.time_font.render(time_text, True, ui_config.WHITE)
        
        # Center text on the background panel
        panel_center_x = bg_x + self.panel_width // 2
        panel_center_y = bg_y + self.panel_height // 2
        
        # Day on top, time on bottom
        day_rect = day_surface.get_rect(center=(panel_center_x, panel_center_y - 15))
        time_rect = time_surface.get_rect(center=(panel_center_x, panel_center_y + 15))
        
        self.screen.blit(day_surface, day_rect)
        self.screen.blit(time_surface, time_rect)


class HotbarUI:
    def __init__(self, screen, hotbar):
        self.screen = screen
        self.hotbar = hotbar
        self.visible = True
        
        # Visual settings
        self.slot_size = 64
        self.slot_gap = 8
        self.hotbar_width = (self.slot_size + self.slot_gap) * self.hotbar.num_slots - self.slot_gap
        self.hotbar_height = self.slot_size + 20  # Extra space for slot numbers
        
        # Position at bottom center of screen
        self.padding_bottom = 20
        
        # Colors
        self.bg_color = (40, 40, 40, 200)  # Semi-transparent dark gray
        self.slot_color = (60, 60, 60)
        self.selected_color = (255, 200, 100)  # Orange/gold highlight
        self.border_color = (100, 100, 100)
        
        # Fonts
        self.number_font = ui_config.get_font(16)
        self.qty_font = ui_config.get_font(14)
    
    def get_position(self):
        """Calculate hotbar position (bottom center)"""
        x = (self.screen.get_width() - self.hotbar_width) // 2
        y = self.screen.get_height() - self.hotbar_height - self.padding_bottom
        return x, y
    
    def draw(self):
        if not self.visible:
            return
        
        x, y = self.get_position()
        
        # Draw background panel
        bg_surface = pygame.Surface((self.hotbar_width, self.hotbar_height), pygame.SRCALPHA)
        bg_surface.fill(self.bg_color)
        self.screen.blit(bg_surface, (x, y))
        
        # Draw each hotbar slot
        for i in range(self.hotbar.num_slots):
            slot_x = x + i * (self.slot_size + self.slot_gap)
            slot_y = y + 10  # Offset for number at top
            
            slot_rect = pygame.Rect(slot_x, slot_y, self.slot_size, self.slot_size)
            
            # Draw slot background
            pygame.draw.rect(self.screen, self.slot_color, slot_rect)
            
            # Highlight selected slot
            if i == self.hotbar.selected_slot:
                pygame.draw.rect(self.screen, self.selected_color, slot_rect, 3)
            else:
                pygame.draw.rect(self.screen, self.border_color, slot_rect, 2)
            
            # Draw slot number (1-8)
            number_text = self.number_font.render(str(i + 1), True, ui_config.WHITE)
            number_rect = number_text.get_rect(centerx=slot_rect.centerx, bottom=slot_rect.top - 2)
            self.screen.blit(number_text, number_rect)
            
            # Draw item in slot
            slot_data = self.hotbar.get_slot(i)
            if slot_data:
                self.draw_item_in_slot(slot_data, slot_rect)
    
    def draw_item_in_slot(self, slot, rect):
        """Draw an item inside a hotbar slot"""
        item = get_item(slot["item_id"])
        if not item:
            return
        
        # Try to load item sprite
        item_image = None
        item_id = slot['item_id']
        
        possible_paths = [
            f"assets/items/{item_id}.png",
            f"assets/items/tools/{item_id}.png",
            f"assets/items/seeds/{item_id}.png",
            f"assets/items/crops/{item_id}.png",
            f"assets/items/resources/{item_id}.png",
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    item_image = pygame.image.load(path).convert_alpha()
                    image_size = int(self.slot_size * 0.65)
                    item_image = pygame.transform.smoothscale(item_image, (image_size, image_size))
                    break
                except Exception as e:
                    print(f"[HOTBAR] Error loading {path}: {e}")
        
        if item_image:
            # Draw item image centered
            image_rect = item_image.get_rect(center=rect.center)
            self.screen.blit(item_image, image_rect)
        else:
            # Fallback: draw item name
            name_font = ui_config.get_font(10)
            name_text = item.name[:6]  # Truncate long names
            name = name_font.render(name_text, True, ui_config.WHITE)
            name_rect = name.get_rect(center=rect.center)
            self.screen.blit(name, name_rect)
        
        # Draw quantity in bottom-right corner
        if slot["quantity"] > 1:
            qty_text = str(slot["quantity"])
            qty = self.qty_font.render(qty_text, True, ui_config.WHITE)
            qty_shadow = self.qty_font.render(qty_text, True, (0, 0, 0))
            
            # Draw shadow for better visibility
            self.screen.blit(qty_shadow, (rect.right - 18, rect.bottom - 18))
            self.screen.blit(qty, (rect.right - 19, rect.bottom - 19))
