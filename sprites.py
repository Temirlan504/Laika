import pygame
from utils.settings import *

class GenericSprite(pygame.sprite.Sprite):
    def __init__(self, pos, surface, groups, z_index):
        super().__init__(groups)
        self.image = surface
        self.rect = self.image.get_rect(topleft=pos)
        self.z_index = z_index

class InteractionSprite(GenericSprite):
    def __init__(self, pos, size, groups, name):
        surface = pygame.Surface(size)
        super().__init__(pos, surface, groups, z_index=0)
        self.name = name
