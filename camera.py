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

        # Cached sorted sprite list — rebuilt only when the group changes
        self._sorted_cache = []
        self._dirty = True          # force rebuild on first draw

    # ------------------------------------------------------------------
    # Override add/remove so we know when to invalidate the sort cache
    # ------------------------------------------------------------------
    def add(self, *sprites, **kwargs):
        super().add(*sprites, **kwargs)
        self._dirty = True

    def remove(self, *sprites, **kwargs):
        super().remove(*sprites, **kwargs)
        self._dirty = True

    def empty(self):
        super().empty()
        self._dirty = True

    # ------------------------------------------------------------------
    # Camera
    # ------------------------------------------------------------------
    def update_offset(self):
        offset_x = self.player.rect.centerx - self.screen.get_width() // 2
        offset_y = self.player.rect.centery - self.screen.get_height() // 2

        offset_x = max(0, min(offset_x, self.map_width - self.screen.get_width()))
        offset_y = max(0, min(offset_y, self.map_height - self.screen.get_height()))

        self.offset.x = offset_x
        self.offset.y = offset_y

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------
    def custom_draw(self):
        self.update_offset()

        # Static sprites (tiles) are sorted once; dynamic sprites (player,
        # meteorites) are re-inserted at the correct depth each frame so
        # centery-based draw order stays correct as things move.
        if self._dirty:
            # Full rebuild when sprites are added or removed
            self._sorted_cache = sorted(
                self.sprites(),
                key=lambda spr: (spr.z_index, spr.rect.centery)
            )
            self._dirty = False
        else:
            # Re-sort only the dynamic sprites in-place each frame
            self._sorted_cache.sort(key=lambda spr: (spr.z_index, spr.rect.centery))

        # Visible screen rect in world space — used for culling
        screen_w = self.screen.get_width()
        screen_h = self.screen.get_height()
        view_rect = pygame.Rect(
            self.offset.x, self.offset.y,
            screen_w, screen_h
        )

        for sprite in self._sorted_cache:
            # Skip sprites outside the viewport (frustum culling)
            if not view_rect.colliderect(sprite.rect):
                continue

            offset_rect = sprite.rect.move(-self.offset.x, -self.offset.y)
            self.screen.blit(sprite.image, offset_rect)

            if self.debug_mode and hasattr(sprite, "hitbox"):
                offset_hitbox = sprite.hitbox.move(-self.offset.x, -self.offset.y)
                pygame.draw.rect(self.screen, (255, 0, 0), offset_hitbox, 2)
