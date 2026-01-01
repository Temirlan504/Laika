import pygame
from pytmx import load_pygame
from sprites import GenericSprite
from collisions import CollisionObject
from utils.settings import *

class MapLoader:
    def __init__(self, map_path):
        self.map_path = map_path
        self.tmx_data = load_pygame(self.map_path)

        self.map_width = self.tmx_data.width * TILE_SIZE
        self.map_height = self.tmx_data.height * TILE_SIZE

        self.player_spawnpoint = None

    def setup(self, sprite_group, collision_sprites):
        tmx_data = self.tmx_data

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

        # --- Import collision objects rectangles ---
        SCALE = TILE_SIZE / tmx_data.tilewidth
        for obj in tmx_data.get_layer_by_name('collisions'):
            rect = pygame.Rect(
                obj.x * SCALE,
                obj.y * SCALE,
                obj.width * SCALE,
                obj.height * SCALE
            )
            CollisionObject(rect, collision_sprites)

        # --- Import Spaceship (tile object) ---
        for obj in tmx_data.get_layer_by_name('spaceship'):
            if obj.name == 'spaceship' and obj.gid:
                image = obj.image
                image = pygame.transform.scale(
                    image,
                    (int(obj.width * SCALE), int(obj.height * SCALE))
                )
                GenericSprite(
                    pos=(obj.x * SCALE, obj.y * SCALE),
                    surface=image,
                    groups=sprite_group,
                    z_index=LAYERS['spaceship']
                )


        # --- Get player spawn point ---
        markers = tmx_data.get_layer_by_name('markers')
        for obj in markers:
            if obj.name == 'player_spawnpoint':
                self.player_spawnpoint = (obj.x * SCALE + (obj.width * SCALE) / 2,
                                          obj.y * SCALE + (obj.height * SCALE) / 2)
