import pygame
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
