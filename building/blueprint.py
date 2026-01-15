import pygame

class DomeBlueprint:
    def __init__(self, image):
        """
        image: pygame.Surface (greenhouse dome sprite)
        """
        self.image = image
        self.size = image.get_size()
        self.mask = pygame.mask.from_surface(image)
