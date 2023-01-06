import pygame
from player import Player
from camera import CameraGroup
from settings import WIDTH, HEIGHT

class Level:
    def __init__(self, display_surface):
        self.display_surface = display_surface
        self.camera_group = CameraGroup() # Sprite group for everything

        # Player
        # Create a player object and place it in the center and add it to the camera_group sprites group
        self.player = Player((WIDTH/2, HEIGHT/2), self.camera_group)

    def run(self, dt):
        self.display_surface.fill((115, 68, 46)) # Fill screen with brown-ish colour

        # Drawing sprites
        self.camera_group.custom_draw() # Draw all the sprites on the display surface
        self.camera_group.update(dt) # Call update methods of all sprites