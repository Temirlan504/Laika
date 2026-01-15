import pygame
from utils.settings import *

class CameraGroup(pygame.sprite.Group):
    def __init__(self, player, screen, map_width, map_height):
        super().__init__()
        self.player = player
        self.screen = screen
        self.map_width = map_width
        self.map_height = map_height
        self.debug_mode = False
        self.offset = pygame.Vector2()

    def update_offset(self):
        # Camera offset
        offset_x = self.player.rect.centerx - self.screen.get_width() // 2
        offset_y = self.player.rect.centery - self.screen.get_height() // 2

        offset_x = max(0, min(offset_x, self.map_width - self.screen.get_width()))
        offset_y = max(0, min(offset_y, self.map_height - self.screen.get_height()))

        self.offset.x = offset_x
        self.offset.y = offset_y

    def custom_draw(self):
        self.update_offset()

        sprites = sorted(
            self.sprites(),
            key=lambda spr: (spr.z_index, spr.rect.centery)
        )

        for sprite in sprites:
            offset_rect = sprite.rect.move(-self.offset.x, -self.offset.y)
            self.screen.blit(sprite.image, offset_rect)

            if self.debug_mode and hasattr(sprite, "hitbox"):
                offset_hitbox = sprite.hitbox.move(-self.offset.x, -self.offset.y)
                pygame.draw.rect(self.screen, (255, 0, 0), offset_hitbox, 2)
