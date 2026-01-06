import pygame
from ui.ui_element import UIElement

class InteractionPrompt(UIElement):
    def __init__(self, screen):
        super().__init__()
        self.screen = screen
        self.font = pygame.font.Font(None, 36)
        self.text = ""
        self.visible = False

    def show(self, text):
        self.text = text
        self.visible = True

    def hide(self):
        self.visible = False

    def draw(self):
        surface = self.font.render(self.text, True, (255, 255, 255))
        rect = surface.get_rect(center=(self.screen.get_width() // 2, 50))

        bg = rect.inflate(20, 10)
        pygame.draw.rect(self.screen, (0, 0, 0), bg)
        pygame.draw.rect(self.screen, (255, 255, 255), bg, 2)

        self.screen.blit(surface, rect)
