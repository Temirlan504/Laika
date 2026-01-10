import pygame
from utils.settings import *
from utils.fade_effect import FadeEffect
from utils.map_loader import MapLoader
from camera import CameraGroup

class LevelState:
    def __init__(self, state_machine, game):
        self.state_machine = state_machine
        self.game = game # Reference to main.py Game class
        self.screen = game.screen
        self.fade_effect = FadeEffect(self.screen)
        self.sleeping = False

        self.debug_mode = False # Toggle debug mode for collision rectangles
        
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
        self.interaction_zones = pygame.sprite.Group() # Group for interaction zones
        self.dynamic_sprites = pygame.sprite.Group() # Group for sprites that need updates

        self.setup_level()

    # --- Setting up the level with player and other sprites ---
    def setup_level(self):
        # Load map tiles
        self.game_map.setup(self.all_sprites, self.collision_sprites, self.interaction_zones)

        # Spawn player
        if self.game_map.player_spawnpoint:
            self.game.player.rect.center = self.game_map.player_spawnpoint
            self.game.player.hitbox.center = self.game_map.player_spawnpoint
        else:
            # If no spawn point found, default to center of screen
            self.game.player.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
            self.game.player.hitbox.center = self.game.player.rect.center

        self.all_sprites.add(self.game.player) # Add player to sprite group
        self.dynamic_sprites.add(self.game.player) # Add player to dynamic sprites

    # --- Pause menu logic ---
    def handle_input(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state_machine.change_state("pause_menu")
                # Player sleep logic
                elif event.key == pygame.K_e:
                    if self.current_interaction:
                        if self.game.clock_system.can_sleep():
                            self.start_sleep()
                        else:
                            print("Too early to sleep")
    
    # --- Player sleep sequence with fade effect ---
    def start_sleep(self):
        if self.sleeping:
            return

        self.sleeping = True
        self.game.player.block_input()

        # Fade to black, then advance day
        self.fade_effect.fade_in(self.on_fade_out_complete)

    def on_fade_out_complete(self):
        self.game.day_cycle.next_day()
        self.game.clock_system.set_time(6, 0)
        self.game.day_cycle.start_new_day()
        self.fade_effect.fade_out(self.on_fade_in_complete)

    def on_fade_in_complete(self):
        self.sleeping = False
        self.game.player.unblock_input()

    # --- Check collision and update sprites ---
    def check_collisions(self, dt):
        for sprite in self.dynamic_sprites:
            if sprite == self.game.player:
                sprite.update(dt, self.collision_sprites)
            else:
                sprite.update(dt)
        
        # Check if player is in any interaction zone
        self.current_interaction = None
        for zone in self.interaction_zones:
            if self.game.player.hitbox.colliderect(zone.rect):
                self.current_interaction = zone
                break
        
        if self.current_interaction:
            self.game.interaction_prompt.show("Press E to Sleep")
        else:
            self.game.interaction_prompt.hide()

    # --- Draw debug rectangles for collision objects ---
    def draw_debug(self):
        if self.debug_mode:
            for sprite in self.collision_sprites:
                offset_rect = sprite.rect.copy()
                offset_rect.x -= self.all_sprites.player.rect.centerx - self.screen.get_width() // 2
                offset_rect.y -= self.all_sprites.player.rect.centery - self.screen.get_height() // 2
                pygame.draw.rect(self.screen, (0, 255, 0), offset_rect, 2)
            
            # Draw interaction zones in blue
            for zone in self.interaction_zones:
                offset_rect = zone.rect.copy()
                offset_rect.x -= self.all_sprites.player.rect.centerx - self.screen.get_width() // 2
                offset_rect.y -= self.all_sprites.player.rect.centery - self.screen.get_height() // 2
                pygame.draw.rect(self.screen, (0, 0, 255), offset_rect, 2)

    def run(self, dt):
        self.screen.fill((184, 88, 88))
        self.all_sprites.custom_draw()
        self.draw_debug() # Draw collision hitboxes for debugging
        self.fade_effect.draw()
        self.fade_effect.update(dt)
        if not self.sleeping:
            self.check_collisions(dt)
