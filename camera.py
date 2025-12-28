import pygame
from utils.settings import *

class CameraGroup(pygame.sprite.Group):
    def __init__(self, player, screen):
        super().__init__()
        self.player = player
        self.screen = screen
        self.offset = pygame.math.Vector2()
        self.debug_mode = False # Enable debug mode to draw Player hitbox

    def custom_draw(self):
        # Calculate offset based on player position
        offset_x = self.player.rect.centerx - self.screen.get_width() // 2
        offset_y = self.player.rect.centery - self.screen.get_height() // 2

        for layer in LAYERS.values():
            for sprite in sorted(self.sprites(), key=lambda spr: spr.z_index):
                if sprite.z_index == layer:
                    offset_rect = sprite.rect.copy()
                    offset_rect.x -= offset_x
                    offset_rect.y -= offset_y
                    self.screen.blit(sprite.image, offset_rect)

                    # --- DRAW HITBOX (DEBUG) ---
                    if self.debug_mode:
                        if hasattr(sprite, "hitbox"):
                            offset_hitbox = sprite.hitbox.copy()
                            offset_hitbox.x -= offset_x
                            offset_hitbox.y -= offset_y
                            pygame.draw.rect(self.screen, (255, 0, 0), offset_hitbox, 2)
