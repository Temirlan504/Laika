import pygame
from utils.settings import *

class LevelState:
    def __init__(self, state_machine, game):
        self.state_machine = state_machine
        self.game = game # Reference to main.py Game class
        self.screen = game.screen

        self.all_sprites = pygame.sprite.Group()

        self.setup_level()

    # --- Setting up the level with player and other sprites ---
    def setup_level(self):
        self.all_sprites.add(self.game.player) # Add player from main.py to sprite group

    # --- Handle keyboard inputs ---
    def handle_input(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state_machine.change_state("pause_menu")

    def run(self, dt):
        self.all_sprites.update(dt)
        self.screen.fill((184, 88, 88))
        self.all_sprites.draw(self.screen)
