import random
import pygame

from utils.settings import LAYERS, TILE_SIZE
from utils.timer import Timer

# How long (ms) before a depleted glacier refreezes (5 minutes default)
GLACIER_REFREEZE_MS = 5 * 60 * 1000

# Puddle colour drawn over the Tiled tile when mined
_PUDDLE_COLOUR = (60, 120, 255, 255)   # Blue colour


class IceGlacierTile(pygame.sprite.Sprite):
    def __init__(self, rect, groups, z_index=LAYERS['ground']):
        super().__init__(groups)
        self.rect  = rect
        # Always SRCALPHA so we can be fully transparent when intact
        self.image = pygame.Surface(rect.size, pygame.SRCALPHA)
        self.z_index = z_index

        self.hp       = 3
        self.depleted = False
        self.tile_pos = (rect.x // TILE_SIZE, rect.y // TILE_SIZE)

        # Fires once the refreeze delay elapses — calls self.refreeze()
        self.refreeze_timer = Timer(GLACIER_REFREEZE_MS, self.refreeze)

        # Start fully transparent (intact ice — Tiled tile visible)
        self._clear_image()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _clear_image(self):
        """Make the overlay invisible (intact state)."""
        self.image.fill((0, 0, 0, 0))

    def _draw_puddle(self):
        """Fill the overlay with the blue puddle (depleted state)."""
        self.image.fill((0, 0, 0, 0))
        pygame.draw.rect(self.image, _PUDDLE_COLOUR, self.image.get_rect())

    # ------------------------------------------------------------------
    # Mining
    # ------------------------------------------------------------------
    def mine(self, player):
        """Call once per pickaxe hit. Drops ice shards when hp reaches 0."""
        if self.depleted:
            return

        self.hp -= 1

        # Play the player's mining sound
        mining_sounds = [
            s for k, s in player.sounds.items()
            if k.startswith('mining') and s is not None
        ]
        if mining_sounds:
            mining_sounds[player._mining_index % len(mining_sounds)].play()
            player._mining_index += 1

        if self.hp <= 0:
            amount = random.randint(1, 3)
            player.add_item("ice_shard", amount)
            print(f"[ICE] Mined! +{amount} ice shard(s). Refreezing in {GLACIER_REFREEZE_MS // 1000}s.")
            self.depleted = True
            self._draw_puddle()
            self.refreeze_timer.activate()
        else:
            print(f"[ICE] Mining… {self.hp} HP remaining.")

    def refreeze(self):
        """Called by the timer when the refreeze delay elapses."""
        self.hp       = 3
        self.depleted = False
        self._clear_image()
        print(f"[ICE] Glacier at {self.tile_pos} has refrozen.")

    # ------------------------------------------------------------------
    # Update (tick the timer every frame)
    # ------------------------------------------------------------------
    def update(self):
        self.refreeze_timer.update()


class IceGlacierLayer:
    """
    Manages all IceGlacierTile overlays for the level.
    Mirror of SoilLayer — call handle_event() from level.py's tool loop,
    and update() once per frame so refreeze timers tick.
    """

    def __init__(self, glacier_sprites, player):
        self.glacier_sprites = glacier_sprites
        self.player          = player

    def get_tile_at_pos(self, pos):
        for tile in self.glacier_sprites:
            if tile.rect.collidepoint(pos):
                return tile
        return None

    def handle_event(self, event_type, pos):
        if event_type != 'pickaxe':
            return
        tile = self.get_tile_at_pos(pos)
        if tile:
            tile.mine(self.player)

    def update(self):
        for tile in self.glacier_sprites:
            tile.update()
