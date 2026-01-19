import pygame

class DoorInteractionZone(pygame.sprite.Sprite):
    def __init__(self, rect, owner=None, text="Press E to enter"):
        super().__init__()
        self.rect = rect
        self.owner = owner
        self.text = text
