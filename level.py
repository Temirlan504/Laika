import pygame
from player import Player
from settings import WIDTH, HEIGHT

class Level:
    def __init__(self, display_surface):
        self.display_surface = display_surface
        self.all_sprites = pygame.sprite.Group() # Sprite group for everything

        # Player
        # Create a player object and place it in the center and add it to the all_sprites group
        self.player = Player((WIDTH/2, HEIGHT/2), self.all_sprites)

    def run(self, dt):
        self.display_surface.fill((115, 68, 46)) # Fill screen with brown-ish colour

        # Drawing sprites
        self.all_sprites.draw(self.display_surface) # Draw all the sprites on the display surface
        self.all_sprites.update(dt) # Update all the methods inside every sprite class