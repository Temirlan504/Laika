import pygame
from sprites import GreenhouseDome
from utils.settings import *
from utils.fade_effect import FadeEffect, NightOverlay
from utils.map_loader import MapLoader
from camera import CameraGroup
from building.preview import DomePreview

class LevelState:
    def __init__(self, state_machine, game):
        self.state_machine = state_machine
        self.game = game # Reference to main.py Game class
        self.screen = game.screen
        self.fade_effect = FadeEffect(self.screen)
        self.night_overlay = NightOverlay(self.game.clock_system, self.screen)
        self.sleeping = False

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
        self.interaction_zones = pygame.sprite.Group() # Group for interaction zones
        self.dynamic_sprites = pygame.sprite.Group() # Group for sprites that need updates

        # Load greenhouse image
        dome_image = pygame.image.load("assets/dome.png").convert_alpha()
        self.preview = DomePreview(dome_image)

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
            
            # Mouse click events
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.preview.valid:
                    dome = GreenhouseDome(
                        center_pos=self.preview.rect.center,
                        image=self.preview.base_image,
                        groups=[self.all_sprites, self.collision_sprites]
                    )
                    self.all_sprites.add(dome)
                    self.collision_sprites.add(dome)

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

    def mouse_to_world(self):
        mouse_screen_pos = pygame.mouse.get_pos()
        mouse_world_pos = pygame.Vector2(
            mouse_screen_pos[0] + self.all_sprites.offset.x,
            mouse_screen_pos[1] + self.all_sprites.offset.y
        )
        return mouse_world_pos
    
    def can_place_dome(self, preview, obstacles):
        # First check if dome would overlap with player
        if preview.rect.colliderect(self.game.player.hitbox):
            offset_x = self.game.player.hitbox.x - preview.rect.x
            offset_y = self.game.player.hitbox.y - preview.rect.y
            
            # Create a mask for player hitbox
            player_mask = pygame.mask.Mask(self.game.player.hitbox.size)
            player_mask.fill()
            
            if preview.mask.overlap(player_mask, (offset_x, offset_y)):
                return False
        
        # Then check against other obstacles (all should have masks now)
        for obj in obstacles:
            if not preview.rect.colliderect(obj.rect):
                continue

            # Use mask collision for all objects
            if hasattr(obj, "mask") and obj.mask:
                # Offset is from preview to obj (where obj is relative to preview)
                offset_x = obj.rect.x - preview.rect.x
                offset_y = obj.rect.y - preview.rect.y

                if preview.mask.overlap(obj.mask, (offset_x, offset_y)):
                    return False
        return True

    def run(self, dt):
        self.screen.fill('black')

        # --- Update ---
        self.fade_effect.update(dt)
        self.night_overlay.update()

        if not self.sleeping:
            self.check_collisions(dt)

        self.preview.set_position(self.mouse_to_world())

        valid = self.can_place_dome(
            self.preview,
            self.collision_sprites.sprites()
        )
        self.preview.set_valid(valid)

        # --- Draw ---
        self.all_sprites.custom_draw()
        self.preview.draw(self.screen, self.all_sprites.offset)
        self.draw_debug()

        self.night_overlay.draw()
        self.fade_effect.draw()
