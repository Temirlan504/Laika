import pygame
from utils.settings import *
from camera import CameraGroup
from utils.map_loader import MapLoader

class LevelState:
    def __init__(self, state_machine, game):
        self.state_machine = state_machine
        self.game = game # Reference to main.py Game class
        self.screen = game.screen
        self.debug_mode = True # Toggle debug mode for collision rectangles
        
        # Load Tiled map
        self.map_path = 'data/tmx/main.tmx'
        self.game_map = MapLoader(self.map_path)

        self.all_sprites = CameraGroup(
            self.game.player,
            self.screen,
            self.game_map.map_width,
            self.game_map.map_height
        )
        self.collision_sprites = pygame.sprite.Group() # Group for collision objects

        self.setup_level()

    # --- Setting up the level with player and other sprites ---
    def setup_level(self):
        # Load map tiles
        self.game_map.setup(self.all_sprites, self.collision_sprites)

        # Spawn player
        if self.game_map.player_spawnpoint:
            self.game.player.rect.center = self.game_map.player_spawnpoint
            self.game.player.hitbox.center = self.game_map.player_spawnpoint
        else:
            # If no spawn point found, default to center of screen
            self.game.player.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
            self.game.player.hitbox.center = self.game.player.rect.center

        self.all_sprites.add(self.game.player) # Add player to sprite group

    # --- Pause menu logic ---
    def handle_input(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state_machine.change_state("pause_menu")

    # --- Check collision and update sprites ---
    def check_collisions(self, dt):
        for sprite in self.all_sprites.sprites():
            if sprite == self.game.player:
                sprite.update(dt, self.collision_sprites)
            else:
                sprite.update(dt)

    # --- Draw debug rectangles for collision objects ---
    def draw_debug(self):
        if self.debug_mode:
            for sprite in self.collision_sprites:
                offset_rect = sprite.rect.copy()
                offset_rect.x -= self.all_sprites.player.rect.centerx - self.screen.get_width() // 2
                offset_rect.y -= self.all_sprites.player.rect.centery - self.screen.get_height() // 2
                pygame.draw.rect(self.screen, (0, 255, 0), offset_rect, 2)

    def run(self, dt):
        self.screen.fill((184, 88, 88))
        self.all_sprites.custom_draw()
        self.draw_debug() # Draw collision hitboxes for debugging
        self.check_collisions(dt)
