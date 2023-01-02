import pygame
from player import Player
from settings import WIDTH, HEIGHT

class Level:
    def __init__(self, display_surface):
        self.display_surface = display_surface
        # Sprite groups
        self.all_sprites = pygame.sprite.Group()

        # Player
        self.player = Player((WIDTH/2, HEIGHT/2), self.all_sprites)

    def run(self, dt):
        self.display_surface.fill("black")
        self.all_sprites.draw(self.display_surface)
        self.all_sprites.update()