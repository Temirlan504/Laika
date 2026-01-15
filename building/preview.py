import pygame

class DomePreview:
    def __init__(self, image):
        self.image = image.copy()
        self.image.set_alpha(120)  # transparent
        self.pos = pygame.Vector2(0, 0)

    def set_position(self, pos):
        self.pos = pygame.Vector2(pos)

    def draw(self, surface, camera_offset):
        rect = self.image.get_rect(center=self.pos)
        rect.topleft -= camera_offset
        surface.blit(self.image, rect)
