import pygame
from utils.settings import *
from camera import CameraGroup
from utils.map_loader import MapLoader
from greenhouse.soil import SoilLayer

class GreenhouseState:
    def __init__(self, state_machine, game):
        self.state_machine = state_machine
        self.game = game
        self.screen = game.screen

        self.current_greenhouse_id = None

    def on_enter(self, greenhouse_id=None, return_pos=None, **kwargs):
        self.current_greenhouse_id = greenhouse_id
        self.return_pos = return_pos

        self.greenhouse_data = self.game.greenhouse_data[greenhouse_id]

        # --- Load greenhouse map ---
        self.map_loader = MapLoader("data/tmx/greenhouse.tmx")

        # --- Sprite groups ---
        self.collision_sprites = pygame.sprite.Group()
        self.interaction_zones = pygame.sprite.Group()
        self.soil_sprites = pygame.sprite.Group()
        self.soil_layer = SoilLayer(self.soil_sprites)

        self.all_sprites = CameraGroup(
            self.game.player,
            self.screen,
            self.map_loader.map_width,
            self.map_loader.map_height
        )

        self.map_loader.setup(
            self.all_sprites,
            self.collision_sprites,
            self.interaction_zones,
            self.soil_sprites
        )

        soil_data = self.greenhouse_data['soil']

        for soil in self.soil_sprites:
            key = soil.tile_pos

            if key in soil_data:
                saved = soil_data[key]
                soil.state = saved['state']
                soil.plant = saved['plant']
                soil.update_visual()

        # Spawn player inside greenhouse
        if self.map_loader.player_spawnpoint:
            self.game.player.rect.center = self.map_loader.player_spawnpoint
            self.game.player.hitbox.center = self.map_loader.player_spawnpoint

        self.all_sprites.add(self.game.player)

        self.game.interaction_prompt.hide()

    def save_soil_state(self):
        soil_data = {}

        for soil in self.soil_sprites:
            soil_data[soil.tile_pos] = {
                'state': soil.state,
                'plant': soil.plant
            }

        self.greenhouse_data['soil'] = soil_data

    def draw_soil(self):
        for soil in self.soil_sprites:
            offset_rect = soil.rect.copy()
            offset_rect.topleft -= self.all_sprites.offset
            self.screen.blit(soil.image, offset_rect)

    def handle_input(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.save_soil_state()
                    self.state_machine.change_state(
                        "level", return_pos=self.return_pos
                    )

    def run(self, dt):
        self.screen.fill("black")

        # Update player
        self.game.player.update(dt, self.collision_sprites)

        # 🔥 Consume events ONCE
        events = self.game.player.consume_events()
        for event_type, pos in events:
            self.soil_layer.handle_event(event_type, pos)

        self.soil_sprites.update()

        # Draw soil below player
        self.draw_soil()

        # Draw world
        self.all_sprites.custom_draw()
