import pygame
from player import Player
from camera import CameraGroup
from settings import WIDTH, HEIGHT
from random import randint

# ====================
class Tree(pygame.sprite.Sprite):
    def __init__(self,pos,group):
        super().__init__(group)
        self.image = pygame.Surface((32,64))
        self.image.fill("black")
        self.rect = self.image.get_rect(topleft=pos)
# ====================

class Level:
    def __init__(self, display_surface):
        self.display_surface = display_surface
        self.camera_group = CameraGroup() # Sprite group for everything

        # Player
        # Create a player object and place it in the center and add it to the camera_group sprites group
        self.player = Player((WIDTH/2, HEIGHT/2), self.camera_group)

        # ====================
        # Spawning trees
        for i in range(20):
            rand_x = randint(0,1000)
            rand_y = randint(0,1000)
            Tree((rand_x, rand_y), self.camera_group)
        # ====================

    def run(self, dt):
        self.display_surface.fill((115, 68, 46)) # Fill screen with brown-ish colour

        # Drawing sprites
        self.camera_group.custom_draw(self.player) # Draw all the sprites on the display surface
        self.camera_group.update(dt) # Call update methods of all sprites