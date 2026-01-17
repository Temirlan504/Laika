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
        self.mask = pygame.mask.from_surface(self.image)
        self.z_index = z_index
