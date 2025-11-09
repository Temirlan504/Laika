import pygame
from utils.settings import *
from player import Player

class LevelState:
    def __init__(self, game):
        self.game = game
        self.screen = pygame.display.get_surface()
        self.is_running = True
        self.all_sprites = pygame.sprite.Group()
        self.setup_level()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # Switch to pause menu
                    from states.pause_menu import PauseMenuState
                    self.game.goto_state(PauseMenuState(self.game, self))

    def setup_level(self):
        # Create player at center of the screen
        player = Player((SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), self.all_sprites)

    def run(self, dt):
        self.screen.fill((0, 0, 0))
        self.handle_events()
        self.all_sprites.draw(self.screen)
        self.all_sprites.update(dt)
