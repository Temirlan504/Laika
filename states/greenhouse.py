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
        self.greenhouses = {}

    def on_enter(self, greenhouse_id=None, **kwargs):
        self.current_greenhouse_id = greenhouse_id

        if greenhouse_id not in self.greenhouses:
            self.greenhouses[greenhouse_id] = {
                'crops': [],
                'name': f'Greenhouse {greenhouse_id}'
            }

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

        # Spawn player inside greenhouse
        if self.map_loader.player_spawnpoint:
            self.game.player.rect.center = self.map_loader.player_spawnpoint
            self.game.player.hitbox.center = self.map_loader.player_spawnpoint

        self.all_sprites.add(self.game.player)

        self.game.interaction_prompt.hide()

    def draw_soil(self):
        for soil in self.soil_sprites:
            offset_rect = soil.rect.copy()
            offset_rect.topleft -= self.all_sprites.offset
            self.screen.blit(soil.image, offset_rect)

    def handle_input(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state_machine.change_state("level")

    def run(self, dt):
        self.screen.fill("black")

        # Update player
        self.game.player.update(dt, self.collision_sprites)

        # 🔥 Consume events ONCE
        events = self.game.player.consume_events()
        for event_type, pos in events:
            self.soil_layer.handle_event(event_type, pos)

        # Draw soil below player
        self.draw_soil()

        # Draw world
        self.all_sprites.custom_draw()
