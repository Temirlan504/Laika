import pygame
from pytmx import load_pygame
from sprites import GenericSprite
from utils.settings import *

class MapLoader:
    def __init__(self, map_path):
        self.map_path = map_path

    def setup(self, sprite_group):
        tmx_data = load_pygame(self.map_path)

        # ---- Import Ground layer ----
        for x, y, tile_surface in tmx_data.get_layer_by_name('ground').tiles():
            tile_surface = pygame.transform.scale(tile_surface, (TILE_SIZE, TILE_SIZE))
            GenericSprite(
                pos=(x * TILE_SIZE, y * TILE_SIZE),
                surface=tile_surface,
                groups=sprite_group,
                z_index=LAYERS['ground']
            )

        # ---- Import Cliffs layer ----
        for x, y, tile_surface in tmx_data.get_layer_by_name('cliffs').tiles():
            tile_surface = pygame.transform.scale(tile_surface, (TILE_SIZE, TILE_SIZE))
            GenericSprite(
                pos=(x * TILE_SIZE, y * TILE_SIZE),
                surface=tile_surface,
                groups=sprite_group,
                z_index=LAYERS['cliffs']
            )

        # --- Player spawn point ---
        for obj in tmx_data.get_layer_by_name('markers'):
            if obj.name == 'player_spawnpoint':
                self.player_spawn = (obj.x, obj.y)