import pygame
from sprites import GreenhouseDome
from utils.settings import *
from utils.fade_effect import FadeEffect, NightOverlay
from utils.map_loader import MapLoader
from camera import CameraGroup
from building.preview import DomePreview
from systems.time_system_fsm import SleepState

class LevelState:
    def __init__(self, state_machine, game):
        self.state_machine = state_machine
        self.game = game # Reference to main.py Game class
        self.screen = game.screen
        self.fade_effect = FadeEffect(self.screen)
        self.night_overlay = NightOverlay(self.game.clock_system, self.screen)

        self.sleep_state_machine = SleepState
        self.sleep_state = self.sleep_state_machine.AWAKE

        self.build_mode = False  # Toggle for build mode
        self.delete_mode = False  # Toggle for delete domes mode
        self.dome_sprites = pygame.sprite.Group()  # Track all placed domes

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

        # Load greenhouse image
        dome_image = pygame.image.load("assets/dome.png").convert_alpha()
        dome_image = pygame.transform.scale(dome_image, (612, 429))
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
                
                # Toggle build mode with B key
                elif event.key == pygame.K_b:
                    self.build_mode = not self.build_mode
                    if self.build_mode:
                        self.delete_mode = False  # Disable delete mode
                    print(f"Build mode: {'ON' if self.build_mode else 'OFF'}")
                
                # Toggle delete mode with X key
                elif event.key == pygame.K_x:
                    self.delete_mode = not self.delete_mode
                    if self.delete_mode:
                        self.build_mode = False  # Disable build mode
                    print(f"Delete mode: {'ON' if self.delete_mode else 'OFF'}")
            
            # Mouse click events
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.delete_mode:
                    # Delete mode: remove dome at mouse position
                    mouse_world_pos = self.mouse_to_world()
                    for dome in self.dome_sprites:
                        if dome.rect.collidepoint(mouse_world_pos):
                            # Check mask collision for precise deletion
                            local_x = int(mouse_world_pos.x - dome.rect.x)
                            local_y = int(mouse_world_pos.y - dome.rect.y)
                            
                            if (0 <= local_x < dome.rect.width and 
                                0 <= local_y < dome.rect.height):
                                if dome.mask.get_at((local_x, local_y)):
                                    # Remove from all groups
                                    dome.kill()
                                    print("Dome deleted!")
                                    break
                elif self.build_mode:
                    # Build mode: place dome
                    if self.preview.valid:
                        dome = GreenhouseDome(
                            center_pos=self.preview.rect.center,
                            image=self.preview.base_image,
                            groups=[self.all_sprites, self.collision_sprites, self.dome_sprites]
                        )
                        print("Dome placed!")

    # --- Player sleep sequence with fade effect ---
    def start_sleep(self):
        if self.sleep_state != self.sleep_state_machine.AWAKE:
            return

        self.sleep_state = self.sleep_state_machine.FADING_OUT
        self.game.player.block_input()
        self.fade_effect.fade_in(self.on_fade_out_complete)

    def on_fade_out_complete(self):
        self.sleep_state = self.sleep_state_machine.ASLEEP

        # Advance day if not already done
        self.game.day_cycle.try_advance_day("sleep")

        # Jump to morning = new cycle
        self.game.clock_system.set_time(6, 0)
        self.game.day_cycle.reset_cycle()

        self.fade_effect.fade_out(self.on_fade_in_complete)

    def on_fade_in_complete(self):
        self.sleep_state = self.sleep_state_machine.AWAKE
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

    def draw_delete_cursor(self):
        mouse_screen_pos = pygame.mouse.get_pos()
        # Draw a red X or circle at mouse position
        pygame.draw.circle(self.screen, (255, 0, 0), mouse_screen_pos, 10, 2)
        pygame.draw.line(self.screen, (255, 0, 0), 
                        (mouse_screen_pos[0] - 7, mouse_screen_pos[1] - 7),
                        (mouse_screen_pos[0] + 7, mouse_screen_pos[1] + 7), 2)
        pygame.draw.line(self.screen, (255, 0, 0),
                        (mouse_screen_pos[0] + 7, mouse_screen_pos[1] - 7),
                        (mouse_screen_pos[0] - 7, mouse_screen_pos[1] + 7), 2)

    def run(self, dt):
        self.screen.fill('black')

        # --- Update ---
        self.fade_effect.update(dt)
        self.night_overlay.update()

        if self.sleep_state == self.sleep_state_machine.AWAKE:
            self.check_collisions(dt)

        # Only show preview in build mode
        if self.build_mode:
            self.preview.set_position(self.mouse_to_world())
            valid = self.can_place_dome(
                self.preview,
                self.collision_sprites.sprites()
            )
            self.preview.set_valid(valid)

        # --- Draw ---
        self.all_sprites.custom_draw()
        
        if self.build_mode:
            self.preview.draw(self.screen, self.all_sprites.offset)
        elif self.delete_mode:
            # Show delete cursor/indicator
            self.draw_delete_cursor()
        
        self.draw_debug()
        self.night_overlay.draw()
        self.fade_effect.draw()
