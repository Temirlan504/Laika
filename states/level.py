import pygame
from utils.settings import *
from camera import CameraGroup
from utils.map_loader import MapLoader

class LevelState:
    def __init__(self, state_machine, game):
        self.state_machine = state_machine
        self.game = game # Reference to main.py Game class
        self.screen = game.screen

        self.all_sprites = CameraGroup(self.game.player, self.screen)

        # Load Tiled map
        self.map_path = 'data/tmx/main.tmx'
        self.game_map = MapLoader(self.map_path)

        self.setup_level()

    # --- Setting up the level with player and other sprites ---
    def setup_level(self):
        # Load map tiles
        self.game_map.setup(self.all_sprites)

        # Add player to sprite group
        self.game.player.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.all_sprites.add(self.game.player)

    # --- Pause menu logic ---
    def handle_input(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state_machine.change_state("pause_menu")

    def run(self, dt):
        self.screen.fill((184, 88, 88))
        self.all_sprites.custom_draw()
        self.all_sprites.update(dt)
