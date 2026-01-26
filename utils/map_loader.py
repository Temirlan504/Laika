import pygame
from pytmx import load_pygame
from sprites import GenericSprite, InteractionSprite
from greenhouse.soil import SoilTile
from collisions import CollisionObject
from utils.settings import *

class MapLoader:
    def __init__(self, map_path):
        self.map_path = map_path
        self.tmx_data = load_pygame(self.map_path)

        self.map_width = self.tmx_data.width * TILE_SIZE
        self.map_height = self.tmx_data.height * TILE_SIZE

        self.player_spawnpoint = None

    def has_layer(self, name):
        return name in self.tmx_data.layernames

    def setup(self, sprite_group, collision_sprites, interaction_sprites, soil_sprites=None):
        tmx_data = self.tmx_data
        SCALE = TILE_SIZE / tmx_data.tilewidth

        # print("TMX layers:")
        # for layer in self.tmx_data.layers:
        #     print(layer.name, type(layer))

        # ---- Ground ----
        if self.has_layer('ground'):
            for x, y, tile_surface in tmx_data.get_layer_by_name('ground').tiles():
                tile_surface = pygame.transform.scale(tile_surface, (TILE_SIZE, TILE_SIZE))
                GenericSprite(
                    pos=(x * TILE_SIZE, y * TILE_SIZE),
                    surface=tile_surface,
                    groups=sprite_group,
                    z_index=LAYERS['ground']
                )

        # ---- Cliffs ----
        if self.has_layer('cliffs'):
            for x, y, tile_surface in tmx_data.get_layer_by_name('cliffs').tiles():
                tile_surface = pygame.transform.scale(tile_surface, (TILE_SIZE, TILE_SIZE))
                GenericSprite(
                    pos=(x * TILE_SIZE, y * TILE_SIZE),
                    surface=tile_surface,
                    groups=sprite_group,
                    z_index=LAYERS['cliffs']
                )
        
        # ---- Walls ----
        if self.has_layer('walls'):
            for x, y, tile_surface in tmx_data.get_layer_by_name('walls').tiles():
                tile_surface = pygame.transform.scale(tile_surface, (TILE_SIZE, TILE_SIZE))
                sprite = GenericSprite(
                    pos=(x * TILE_SIZE, y * TILE_SIZE),
                    surface=tile_surface,
                    groups=sprite_group,
                    z_index=LAYERS['walls']
                )

        # ---- Collisions ----
        if self.has_layer('collisions'):
            for obj in tmx_data.get_layer_by_name('collisions'):
                rect = pygame.Rect(
                    obj.x * SCALE,
                    obj.y * SCALE,
                    obj.width * SCALE,
                    obj.height * SCALE
                )
                CollisionObject(rect, collision_sprites)

        # ---- Spaceship + interactions ----
        if self.has_layer('spaceship'):
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

                if obj.name == 'interaction_zone':
                    InteractionSprite(
                        pos=(obj.x * SCALE, obj.y * SCALE),
                        size=(obj.width * SCALE, obj.height * SCALE),
                        groups=interaction_sprites,
                        name=obj.name,
                        text="Press E to Sleep"
                    )

        # ---- Furniture ----
        if self.has_layer('furniture'):
            for obj in tmx_data.get_layer_by_name('furniture'):
                if obj.gid:
                    image = pygame.transform.scale(
                        obj.image,
                        (int(obj.width * SCALE), int(obj.height * SCALE))
                    )
                    sprite = GenericSprite(
                        pos=(obj.x * SCALE, obj.y * SCALE),
                        surface=image,
                        groups=sprite_group,
                        z_index=LAYERS['furniture']
                    )

        # --- Import soil rectangles ---
        if self.has_layer('soil') and soil_sprites is not None:
            for obj in tmx_data.get_layer_by_name('soil'):
                rect = pygame.Rect(
                    obj.x * SCALE,
                    obj.y * SCALE,
                    obj.width * SCALE,
                    obj.height * SCALE
                )
                SoilTile(
                    rect=rect,
                    groups=[sprite_group, soil_sprites]
                )

        # ---- Player spawn ----
        if self.has_layer('markers'):
            for obj in tmx_data.get_layer_by_name('markers'):
                if obj.name == 'player_spawnpoint':
                    self.player_spawnpoint = (
                        obj.x * SCALE + (obj.width * SCALE) / 2,
                        obj.y * SCALE + (obj.height * SCALE) / 2
                    )
