import pygame
from ui.ui_element import UIElement

class DayUI(UIElement):
    def __init__(self, day_cycle, clock, screen):
        super().__init__()
        self.day_cycle = day_cycle
        self.clock = clock
        self.screen = screen
        self.font = pygame.font.Font(None, 26)

        self.day = day_cycle.day
        day_cycle.subscribe(self)

    def on_new_day(self, day):
        self.day = day

    def draw(self):
        text = f"SOL {self.day} | {self.clock.time_string()}"
        surface = self.font.render(text, True, (255, 255, 255))
        rect = surface.get_rect(topright=(self.screen.get_width() - 20, 20))

        bg = rect.inflate(14, 8)
        pygame.draw.rect(self.screen, (0, 0, 0), bg)
        pygame.draw.rect(self.screen, (255, 255, 255), bg, 2)

        self.screen.blit(surface, rect)
