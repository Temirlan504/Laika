import pygame

class CollisionObject(pygame.sprite.Sprite):
    def __init__(self, rect, groups):
        super().__init__(groups)
        self.rect = pygame.Rect(rect)
        self.mask = pygame.mask.Mask((self.rect.width, self.rect.height))
        self.mask.fill()
