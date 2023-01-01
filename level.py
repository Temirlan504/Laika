import pygame

class Level:
    def __init__(self, display_surface):
        self.display_surface = display_surface
        # Sprite groups
        self.all_sprites = pygame.sprite.Group()

    def run(self, dt):
        self.display_surface.fill("black")
        self.all_sprites.draw(self.display_surface)
        self.all_sprites.update()