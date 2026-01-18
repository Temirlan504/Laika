import pygame
from utils.settings import *

class GenericSprite(pygame.sprite.Sprite):
    def __init__(self, pos, surface, groups, z_index):
        super().__init__(groups)
        self.image = surface
        self.rect = self.image.get_rect(topleft=pos)
        self.mask = pygame.mask.from_surface(self.image)
        self.z_index = z_index

class InteractionSprite(GenericSprite):
    def __init__(self, pos, size, groups, name):
        surface = pygame.Surface(size)
        super().__init__(pos, surface, groups, z_index=0)
        self.name = name

class GreenhouseDome(pygame.sprite.Sprite):
    def __init__(self, center_pos, image, groups, z_index=2):
        super().__init__(groups)

        self.image = image
        self.rect = self.image.get_rect(center=center_pos)
        
        # Full mask for dome-to-dome placement checking
        self.full_mask = pygame.mask.from_surface(self.image)
        
        # Collision mask - only bottom half for player collision
        self.mask = pygame.mask.Mask(self.image.get_size())
        
        # Copy only the bottom half of the full mask to collision mask
        height = self.image.get_height()
        collision_start_y = int(height * 0.3) # Collision starts at 30% of height
        
        for y in range(collision_start_y, height):
            for x in range(self.image.get_width()):
                if self.full_mask.get_at((x, y)):
                    self.mask.set_at((x, y), 1)
        
        self.z_index = z_index
