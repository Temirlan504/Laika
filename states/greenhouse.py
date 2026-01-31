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

        # Load greenhouse map
        self.map_loader = MapLoader("data/tmx/greenhouse.tmx")

        # Sprite groups
        self.collision_sprites = pygame.sprite.Group()
        self.interaction_zones = pygame.sprite.Group()
        self.soil_sprites = pygame.sprite.Group()
        self.soil_layer = SoilLayer(self.soil_sprites, self.game.player)

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

        # Restore saved soil state
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
                # ESC: Close inventory if open, otherwise exit greenhouse
                if event.key == pygame.K_ESCAPE:
                    if self.game.inventory_ui.visible:
                        self.game.inventory_ui.hide()
                    else:
                        self.save_soil_state()
                        self.state_machine.change_state(
                            "level", return_pos=self.return_pos
                        )
                
                # Toggle inventory (handled here instead of main.py)
                elif event.key == pygame.K_TAB or event.key == pygame.K_i:
                    self.game.inventory_ui.toggle()
            
            # Handle inventory clicks
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.game.inventory_ui.handle_click(pygame.mouse.get_pos())

    def refill_oxygen(self, dt):
        self.game.player.refill_oxygen(40 * dt)

    def run(self, dt):
        self.screen.fill("black")

        # Update hover state for inventory
        self.game.inventory_ui.handle_hover(pygame.mouse.get_pos())

        # Block player input when inventory is open
        if self.game.inventory_ui.visible:
            self.game.player.block_input()
        else:
            self.game.player.unblock_input()

        # Update player
        self.game.player.update(dt, self.collision_sprites)

        # Handle tool events from player
        events = self.game.player.consume_events()
        for event_data in events:
            event_type = event_data[0]
            pos = event_data[1]
            
            # For planting, pass the seed_id
            if event_type == 'plant' and len(event_data) > 2:
                seed_id = event_data[2]
                self.soil_layer.handle_event(event_type, pos, seed_id)
            else:
                self.soil_layer.handle_event(event_type, pos)

        # Refill oxygen
        self.refill_oxygen(dt)

        # Update soil tiles
        self.soil_sprites.update()

        # Draw soil below player
        self.draw_soil()

        # Draw world
        self.all_sprites.custom_draw()
