import pygame

class DomePreview:
    def __init__(self, image):
        self.base_image = image
        self.image = image.copy()
        self.image.set_alpha(120)  # transparent
        self.mask = pygame.mask.from_surface(image)
        self.rect = self.image.get_rect()

        self.pos = pygame.Vector2(0, 0)
        self.valid = True

    def set_position(self, pos):
        self.pos = pygame.Vector2(pos)
        self.rect.center = self.pos

    def set_valid(self, valid):
        self.valid = valid
        self.image = self.base_image.copy()

        if valid:
            self.image.fill((0, 200, 0), special_flags=pygame.BLEND_RGBA_MULT)
        else:
            self.image.fill((200, 0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        self.image.set_alpha(120)

        self.rect = self.image.get_rect(center=self.rect.center)

    def draw(self, surface, camera_offset):
        rect = self.image.get_rect(center=self.pos)
        rect.topleft -= camera_offset
        surface.blit(self.image, rect)
