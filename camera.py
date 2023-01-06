import pygame

class CameraGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        # Get the display_surface that was created from pygame.display.set_mode(...)
        self.display_surface = pygame.display.get_surface()

    # Method to custom draw all the sprites (same as sprites.draw() but mine)
    def custom_draw(self):
        for sprite in sorted(self.sprites(), key=lambda sprite: sprite.rect.centery):
            self.display_surface.blit(sprite.image, sprite.rect)