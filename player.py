import pygame

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, group):
        super().__init__(group)
        self.image = pygame.Surface((32,32))
        self.image.fill("white")
        self.rect = self.image.get_rect(center=pos)