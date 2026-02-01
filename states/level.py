import random
import pygame
from sprites import GreenhouseDome, Meteorite
from utils.settings import *
from utils.fade_effect import FadeEffect, NightOverlay
from utils.map_loader import MapLoader
from camera import CameraGroup
from building.preview import DomePreview
from systems.time_system_fsm import SleepState
from systems.oxygen_system import OxygenSystem
from building.door import DoorInteractionZone
from utils.timer import Timer

class LevelState:
    def __init__(self, state_machine, game):
        self.state_machine = state_machine
        self.game = game
        self.screen = game.screen
        self.fade_effect = FadeEffect(self.screen)
        self.night_overlay = NightOverlay(self.game.clock_system, self.screen)

        self.sleep_state_machine = SleepState
        self.sleep_state = self.sleep_state_machine.AWAKE

        self.build_mode = False
        self.delete_mode = False
        self.dome_sprites = pygame.sprite.Group()

        self.ground_positions = []
        self.meteorites = pygame.sprite.Group()
        self.max_meteorites = 100
        self.meteor_spawn_timer = Timer(100)
        self.meteor_spawn_timer.activate()

        self.debug_mode = False
        self.debug_timer = 0
        
        # Load Tiled map
        self.map_path = 'data/tmx/main.tmx'
        self.game_map = MapLoader(self.map_path)

        self.all_sprites = CameraGroup(
            self.game.player,
            self.screen,
            self.game_map.map_width,
            self.game_map.map_height
        )
        self.collision_sprites = pygame.sprite.Group()
        self.interaction_zones = pygame.sprite.Group()
        self.dynamic_sprites = pygame.sprite.Group()

        # Load greenhouse image
        dome_image = pygame.image.load("assets/dome.png").convert_alpha()
        dome_image = pygame.transform.scale(dome_image, (612, 429))
        self.preview = DomePreview(dome_image)

        # Oxygen system
        self.oxygen_system = OxygenSystem()

        self.setup_level()

    def setup_level(self):
        # Make sure player exists
        if self.game.player is None:
            raise RuntimeError("Player must be initialized before entering level state")
        
        # Load map tiles
        self.game_map.setup(
            self.all_sprites, self.collision_sprites,
            self.interaction_zones, ground_positions=self.ground_positions
        )

        # Spawn player
        if self.game_map.player_spawnpoint:
            self.game.player.rect.center = self.game_map.player_spawnpoint
            self.game.player.hitbox.center = self.game_map.player_spawnpoint
        else:
            self.game.player.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
            self.game.player.hitbox.center = self.game.player.rect.center

        self.all_sprites.add(self.game.player)
        self.dynamic_sprites.add(self.game.player)
    
    def on_enter(self, return_pos=None, **kwargs):
        # Make sure player exists - if not, something went wrong
        if not self.game.player:
            print("ERROR: Level entered without player! Returning to main menu.")
            self.state_machine.change_state("main_menu")
            return
        
        # Show game UI elements
        self.game.day_ui.visible = True
        self.game.interaction_prompt.visible = False  # Start hidden, shown when near interaction
        if self.game.inventory_ui:
            self.game.inventory_ui.visible = False  # Start hidden, opened with TAB
        
        # Unblock player input when entering level
        self.game.player.unblock_input()
        
        if return_pos:
            self.game.player.rect.center = return_pos
            self.game.player.hitbox.center = return_pos

    def handle_input(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                # ESC: Close inventory if open, otherwise pause menu
                if event.key == pygame.K_ESCAPE:
                    if self.game.inventory_ui.visible:
                        self.game.inventory_ui.hide()
                    else:
                        self.state_machine.change_state("pause_menu")

                # Toggle inventory (handled in state instead of main.py)
                elif event.key == pygame.K_TAB or event.key == pygame.K_i:
                    self.game.inventory_ui.toggle()

                # Interaction key
                elif event.key == pygame.K_e:
                    if not self.current_interaction:
                        return
                    zone = self.current_interaction

                    # Dome door interaction
                    if isinstance(zone, DoorInteractionZone):
                        if self.current_greenhouse:
                            self.state_machine.change_state(
                                "greenhouse",
                                greenhouse_id=self.current_greenhouse.greenhouse_id,
                                return_pos=self.game.player.rect.center
                            )
                        return

                    # Sleep interaction (Tiled)
                    if zone.text == "Press E to Sleep":
                        if self.game.clock_system.can_sleep():
                            self.start_sleep()
                        else:
                            print("Too early to sleep")
                
                # Toggle build mode
                elif event.key == pygame.K_b:
                    self.build_mode = not self.build_mode
                    if self.build_mode:
                        self.delete_mode = False
                    print(f"Build mode: {'ON' if self.build_mode else 'OFF'}")
                
                # Toggle delete mode
                elif event.key == pygame.K_x:
                    self.delete_mode = not self.delete_mode
                    if self.delete_mode:
                        self.build_mode = False
                    print(f"Delete mode: {'ON' if self.delete_mode else 'OFF'}")
            
            # Mouse click events
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Handle inventory clicks first
                self.game.inventory_ui.handle_click(pygame.mouse.get_pos())
                
                # Then handle building/deleting
                if self.delete_mode:
                    mouse_world_pos = self.mouse_to_world()
                    for dome in self.dome_sprites:
                        if dome.rect.collidepoint(mouse_world_pos):
                            local_x = int(mouse_world_pos.x - dome.rect.x)
                            local_y = int(mouse_world_pos.y - dome.rect.y)
                            
                            if (0 <= local_x < dome.rect.width and 
                                0 <= local_y < dome.rect.height):
                                if dome.mask.get_at((local_x, local_y)):
                                    for zone in self.interaction_zones:
                                        if isinstance(zone, DoorInteractionZone) and zone.owner == dome:
                                            zone.kill()
                                            break
                                    dome.kill()
                                    print("Dome deleted!")
                                    break
                
                elif self.build_mode:
                    if self.preview.valid:
                        dome = GreenhouseDome(
                            center_pos=self.preview.rect.center,
                            image=self.preview.base_image,
                            groups=[self.all_sprites, self.collision_sprites, self.dome_sprites]
                        )
                        greenhouse_id = dome.greenhouse_id
                        if greenhouse_id not in self.game.greenhouse_data:
                            self.game.greenhouse_data[greenhouse_id] = {
                                "soil": {}
                            }

                        # Create door interaction zone
                        door_world_pos = (
                            pygame.Vector2(dome.rect.center)
                            + dome.door_offset
                        )
                        door_rect = pygame.Rect(0, 0, 96, 48)
                        door_rect.center = door_world_pos

                        zone = DoorInteractionZone(
                            rect=door_rect,
                            owner=dome,
                            text="Press E to Enter"
                        )
                        self.interaction_zones.add(zone)

    def start_sleep(self):
        if self.sleep_state != self.sleep_state_machine.AWAKE:
            return

        self.sleep_state = self.sleep_state_machine.FADING_OUT
        self.game.player.block_input()
        self.fade_effect.fade_in(self.on_fade_out_complete)

    def on_fade_out_complete(self):
        self.sleep_state = self.sleep_state_machine.ASLEEP
        if not self.game.day_cycle.day_advanced:
            self.game.day_cycle.try_advance_day("sleep")

        # Advance crops in all greenhouses
        for greenhouse in self.game.greenhouse_data.values():
            for data in greenhouse['soil'].values():
                plant = data['plant']
                if plant:
                    plant.grow_to_final()

        # Jump to morning
        self.game.clock_system.set_time(6, 0)
        self.fade_effect.fade_out(self.on_fade_in_complete)

    def on_fade_in_complete(self):
        self.sleep_state = self.sleep_state_machine.AWAKE
        self.game.player.unblock_input()

    def check_collisions(self, dt):
        # Make sure player exists and is in the game
        if not self.game.player:
            return
        
        for sprite in self.dynamic_sprites:
            if sprite == self.game.player:
                sprite.update(dt, self.collision_sprites)
            else:
                sprite.update(dt)
        
        # Check if player is in any interaction zone
        self.current_interaction = None
        self.current_greenhouse = None
        
        for zone in self.interaction_zones:
            if self.game.player.hitbox.colliderect(zone.rect):
                self.current_interaction = zone
                
                if isinstance(zone, DoorInteractionZone):
                    self.current_greenhouse = zone.owner
                break
        
        # Update interaction prompt
        if self.current_interaction:
            if isinstance(self.current_interaction, DoorInteractionZone):
                self.game.interaction_prompt.show("Press E to Enter Greenhouse")
            else:
                self.game.interaction_prompt.show(self.current_interaction.text)
        else:
            self.game.interaction_prompt.hide()

    def draw_debug(self):
        if self.debug_mode:
            for sprite in self.collision_sprites:
                offset_rect = sprite.rect.copy()
                offset_rect.x -= self.all_sprites.player.rect.centerx - self.screen.get_width() // 2
                offset_rect.y -= self.all_sprites.player.rect.centery - self.screen.get_height() // 2
                pygame.draw.rect(self.screen, (0, 255, 0), offset_rect, 2)
            
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
        # Check against player
        if preview.rect.colliderect(self.game.player.hitbox):
            offset_x = self.game.player.hitbox.x - preview.rect.x
            offset_y = self.game.player.hitbox.y - preview.rect.y
            
            player_mask = pygame.mask.Mask(self.game.player.hitbox.size)
            player_mask.fill()
            
            if preview.mask.overlap(player_mask, (offset_x, offset_y)):
                return False
        
        # Check against other obstacles
        for obj in obstacles:
            if not preview.rect.colliderect(obj.rect):
                continue

            if hasattr(obj, "mask") and obj.mask:
                offset_x = obj.rect.x - preview.rect.x
                offset_y = obj.rect.y - preview.rect.y

                if preview.mask.overlap(obj.mask, (offset_x, offset_y)):
                    return False
        return True

    def draw_delete_cursor(self):
        mouse_screen_pos = pygame.mouse.get_pos()
        pygame.draw.circle(self.screen, (255, 0, 0), mouse_screen_pos, 10, 2)
        pygame.draw.line(self.screen, (255, 0, 0), 
                        (mouse_screen_pos[0] - 7, mouse_screen_pos[1] - 7),
                        (mouse_screen_pos[0] + 7, mouse_screen_pos[1] + 7), 2)
        pygame.draw.line(self.screen, (255, 0, 0),
                        (mouse_screen_pos[0] + 7, mouse_screen_pos[1] - 7),
                        (mouse_screen_pos[0] - 7, mouse_screen_pos[1] + 7), 2)

    def try_spawn_meteor(self):
        if len(self.meteorites) >= self.max_meteorites:
            return

        if not self.ground_positions:
            return

        pos = random.choice(self.ground_positions)

        # Don't spawn on player
        if self.game.player.hitbox.collidepoint(
            pos[0] + TILE_SIZE // 2,
            pos[1] + TILE_SIZE // 2
        ):
            return

        Meteorite(
            pos=pos,
            groups=[
                self.all_sprites,
                self.meteorites,
                self.collision_sprites
            ]
        )

    def handle_tool_events(self):
        """Handle tool usage events from player"""
        events = self.game.player.consume_events()
        for event_data in events:
            event_type = event_data[0]
            pos = event_data[1]
            
            if event_type == 'pickaxe':
                # Check all meteorites
                for meteor in self.meteorites:
                    dx = meteor.rect.centerx - pos[0]
                    dy = meteor.rect.centery - pos[1]
                    distance = (dx*dx + dy*dy) ** 0.5
                    
                    if distance <= TILE_SIZE * 0.7:
                        meteor.mine(self.game.player)
                        break

    def run(self, dt):
        self.screen.fill('black')

        self.fade_effect.update(dt)
        self.night_overlay.update()

        # Update inventory hover
        self.game.inventory_ui.handle_hover(pygame.mouse.get_pos())

        # Only update game logic if not sleeping and dt > 0 (not paused)
        if self.sleep_state == self.sleep_state_machine.AWAKE and dt > 0:
            # Meteor spawning
            self.meteor_spawn_timer.update()
            if self.meteor_spawn_timer.deactivate:
                if len(self.meteorites) < self.max_meteorites:
                    self.try_spawn_meteor()
                self.meteor_spawn_timer.activate()

            # Block player input when inventory is open
            if self.game.inventory_ui.visible:
                self.game.player.block_input()
            else:
                self.game.player.unblock_input()
            
            self.check_collisions(dt)
            self.oxygen_system.update(self.game.player, dt)

            self.handle_tool_events()
        elif dt == 0:
            # Game is paused - make absolutely sure player is blocked
            if self.game.player:
                self.game.player.block_input()

        # Build preview (always show even when paused)
        if self.build_mode:
            self.preview.set_position(self.mouse_to_world())
            valid = self.can_place_dome(
                self.preview,
                self.collision_sprites.sprites()
            )
            self.preview.set_valid(valid)

        # Always draw the game (even when paused - pause menu will overlay on top)
        self.all_sprites.custom_draw()

        if self.build_mode:
            self.preview.draw(self.screen, self.all_sprites.offset)
        elif self.delete_mode:
            self.draw_delete_cursor()

        self.draw_debug()
        self.night_overlay.draw()
        self.fade_effect.draw()

        # Debug info (only when dt > 0, not paused)
        if dt > 0:
            self.debug_timer += dt
            if self.debug_timer >= 1.0:
                print(
                    f"[DEBUG] HP={self.game.player.current_health:.0f} | "
                    f"O2={self.game.player.current_oxygen:.0f} | "
                    f"Hunger={self.game.player.current_hunger:.0f}"
                )
                self.debug_timer = 0
