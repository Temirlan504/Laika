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
        self.max_meteorites = 50
        self.meteor_spawn_timer = Timer(10000)  # Try to spawn a meteor every 10 seconds
        self.meteor_spawn_timer.activate()

        self.LAST_SOL = 10

        self.debug_mode = True
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

    def on_resize(self, size):
        # Update local screen reference
        self.screen = self.game.screen

        # Tell effects to rebuild their surfaces
        self.fade_effect.on_resize(self.screen)
        self.night_overlay.on_resize(self.screen)

    def setup_level(self):
        # Make sure player exists
        if self.game.player is None:
            raise RuntimeError("Player must be initialized before entering level state")
        
        # Save current player position (in case it was loaded from save)
        saved_position = self.game.player.rect.center
        
        # Load map tiles
        self.game_map.setup(
            self.all_sprites, self.collision_sprites,
            self.interaction_zones, ground_positions=self.ground_positions
        )

        # Only spawn player at map spawn point if this is a NEW game
        # (check if player is still at default starting position)
        default_start = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        
        # If player is at default position AND there's a map spawnpoint, use it
        if saved_position == default_start and self.game_map.player_spawnpoint:
            self.game.player.rect.center = self.game_map.player_spawnpoint
            self.game.player.hitbox.center = self.game_map.player_spawnpoint
        # Otherwise, keep the loaded position (restore it)
        else:
            self.game.player.rect.center = saved_position
            self.game.player.hitbox.center = saved_position

        self.all_sprites.add(self.game.player)
        self.dynamic_sprites.add(self.game.player)
    
    def on_enter(self, return_pos=None, **kwargs):
        # Make sure player exists - if not, something went wrong
        if not self.game.player:
            print("ERROR: Level entered without player! Returning to main menu.")
            self.state_machine.change_state("main_menu")
            return
        
        # Load any pending buildings from save game
        if hasattr(self.game, '_pending_buildings'):
            self.game.save_manager.load_pending_buildings(self.game)
        
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
                elif event.key == pygame.K_TAB:
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
                
                # Hotbar number keys (1-8)
                elif pygame.K_1 <= event.key <= pygame.K_9:
                    slot_index = event.key - pygame.K_1  # Convert key to 0-8
                    self.game.player.hotbar.select_slot(slot_index)
            
            # Mouse button DOWN events
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                
                if event.button == 1:  # Left click
                    # Try inventory drag start first
                    clicked_slot = self.game.inventory_ui.handle_mouse_down(mouse_pos, 1)
                    
                    # If not clicking inventory, handle building/deleting
                    if clicked_slot is None:
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
                
                elif event.button == 3:  # Right click
                    # Handle right-click on inventory (for future quick-use)
                    clicked_slot = self.game.inventory_ui.handle_mouse_down(mouse_pos, 3)
                    if clicked_slot is not None:
                        slot = self.game.player.inventory.get_slot(clicked_slot)
                        if slot:
                            self.game.player.use_item(slot["item_id"])

                # Scroll wheel up
                elif event.button == 4:
                    self.game.player.hotbar.select_previous()

                # Scroll wheel down
                elif event.button == 5:
                    self.game.player.hotbar.select_next()
            
            # Mouse button UP events
            if event.type == pygame.MOUSEBUTTONUP:
                mouse_pos = pygame.mouse.get_pos()
                
                if event.button == 1:  # Left click release
                    # Handle drag-and-drop
                    result = self.game.inventory_ui.handle_mouse_up(mouse_pos, 1)
                    if result:
                        from_info, to_info, action_type = result
                        
                        if action_type == 'swap':
                            # from_info and to_info are now tuples like ('inventory', index) or ('hotbar', index)
                            from_type, from_index = from_info
                            to_type, to_index = to_info
                            
                            # Get slot data based on storage type
                            if from_type == 'inventory':
                                from_data = self.game.player.inventory.get_slot(from_index)
                            else:  # hotbar
                                from_data = self.game.player.hotbar.get_slot(from_index)
                            
                            if to_type == 'inventory':
                                to_data = self.game.player.inventory.get_slot(to_index)
                            else:  # hotbar
                                to_data = self.game.player.hotbar.get_slot(to_index)
                            
                            # If both slots have the same item, try to stack
                            if from_data and to_data and from_data["item_id"] == to_data["item_id"]:
                                if not self.game.inventory_ui.stack_items(from_info, to_info):
                                    # If stacking failed (full), swap instead
                                    self.game.inventory_ui.swap_slots(from_info, to_info)
                            else:
                                # Different items or one empty - just swap
                                self.game.inventory_ui.swap_slots(from_info, to_info)

    def start_sleep(self):
        if self.sleep_state != self.sleep_state_machine.AWAKE:
            return

        self.sleep_state = self.sleep_state_machine.FADING_OUT
        self.game.player.block_input()
        self.fade_effect.fade_in(self.on_fade_out_complete)

    def on_fade_out_complete(self):
        self.sleep_state = self.sleep_state_machine.ASLEEP
        
        # Sleeping always advances the day now (since we can't sleep after midnight)
        if not self.game.day_cycle.day_advanced:
            self.game.day_cycle.try_advance_day("sleep")

        # Advance crops in all greenhouses
        for greenhouse in self.game.greenhouse_data.values():
            for data in greenhouse['soil'].values():
                plant = data['plant']
                if plant:
                    plant.grow_to_final()
        
        # Auto-save after sleeping
        self.game.save_manager.auto_save(self.game)

        # Jump to morning and reset cycle for the new day
        self.game.clock_system.set_time(6, 0)
        self.game.day_cycle.reset_cycle()
        
        self.fade_effect.fade_out(self.on_fade_in_complete)
        
        # Check if we've reached the final day
        if self.check_ending_trigger():
            return

    def check_ending_trigger(self):
        """Check if we've reached the final day and trigger ending"""
        if self.game.day_cycle.day >= self.LAST_SOL:
            print(f"[ENDING] Reached final day ({self.LAST_SOL})! Triggering ending...")
            
            # Block player input
            if self.game.player:
                self.game.player.block_input()
            
            # Transition to ending scene
            self.state_machine.change_state("ending_scene")
            return True
        return False
    
    def on_new_day(self, day):
        """Called when a new day starts (from DayCycle)"""
        print(f"[LEVEL] New day started: Sol {day}")
        
        # Check if this is the final day
        if self.check_ending_trigger():
            return  # Ending triggered, don't continue

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
        """Spawn a meteor at a valid ground position, avoiding obstacles"""
        if len(self.meteorites) >= self.max_meteorites:
            return

        if not self.ground_positions:
            return

        # Try multiple times to find a valid spawn position
        max_attempts = 15
        for attempt in range(max_attempts):
            pos = random.choice(self.ground_positions)
            spawn_x = pos[0] + TILE_SIZE // 2
            spawn_y = pos[1] + TILE_SIZE // 2
            
            # Create a rect for the meteor spawn position
            meteor_spawn_rect = pygame.Rect(
                spawn_x - TILE_SIZE // 2,
                spawn_y - TILE_SIZE // 2,
                TILE_SIZE,
                TILE_SIZE
            )
            
            # Check if position is valid
            if self.is_valid_meteor_spawn(meteor_spawn_rect):
                Meteorite(
                    pos=pos,
                    groups=[
                        self.all_sprites,
                        self.meteorites,
                        self.collision_sprites
                    ]
                )
                print(f"[METEOR] Spawned at ({pos[0]}, {pos[1]}) - Total: {len(self.meteorites)}/{self.max_meteorites}")
                break
            elif attempt == max_attempts - 1:
                print(f"[METEOR] Failed to find valid spawn position after {max_attempts} attempts")

    def is_valid_meteor_spawn(self, meteor_rect):
        """Check if a position is valid for meteor spawning"""
        
        # Don't spawn too close to player (give them some space)
        player_distance_threshold = TILE_SIZE * 3  # 3 tiles away
        dx = self.game.player.rect.centerx - meteor_rect.centerx
        dy = self.game.player.rect.centery - meteor_rect.centery
        distance_to_player = (dx*dx + dy*dy) ** 0.5
        
        if distance_to_player < player_distance_threshold:
            return False
        
        # Don't spawn on greenhouses
        for dome in self.dome_sprites:
            if meteor_rect.colliderect(dome.rect):
                # Check mask collision for precise detection
                if hasattr(dome, 'mask') and dome.mask:
                    offset_x = dome.rect.x - meteor_rect.x
                    offset_y = dome.rect.y - meteor_rect.y
                    
                    meteor_mask = pygame.mask.Mask(meteor_rect.size)
                    meteor_mask.fill()
                    
                    if meteor_mask.overlap(dome.mask, (offset_x, offset_y)):
                        return False
        
        # Don't spawn on other collision objects (cliffs, rocks, etc.)
        for sprite in self.collision_sprites:
            # Skip meteorites themselves
            if sprite in self.meteorites:
                continue
            # Skip domes (already checked above)
            if sprite in self.dome_sprites:
                continue
            # Skip player (already checked above)
            if sprite == self.game.player:
                continue
                
            if meteor_rect.colliderect(sprite.rect):
                # For sprites with masks, do precise collision
                if hasattr(sprite, 'mask') and sprite.mask:
                    offset_x = sprite.rect.x - meteor_rect.x
                    offset_y = sprite.rect.y - meteor_rect.y
                    
                    meteor_mask = pygame.mask.Mask(meteor_rect.size)
                    meteor_mask.fill()
                    
                    if meteor_mask.overlap(sprite.mask, (offset_x, offset_y)):
                        return False
                else:
                    # For sprites without masks, rect collision is enough
                    return False
        
        # Don't spawn too close to existing meteorites
        min_distance = TILE_SIZE * 2  # At least 2 tiles apart
        for meteor in self.meteorites:
            dx = meteor.rect.centerx - meteor_rect.centerx
            dy = meteor.rect.centery - meteor_rect.centery
            distance = (dx*dx + dy*dy) ** 0.5
            
            if distance < min_distance:
                return False
        
        # Position is valid!
        return True

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

        # Only update game logic if not sleeping and dt > 0 (not paused)
        if self.sleep_state == self.sleep_state_machine.AWAKE and dt > 0:
            # Update inventory UI hover state
            if self.game.inventory_ui:
                self.game.inventory_ui.update()
            
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

        if hasattr(self.game, 'hotbar_ui'):
            self.game.hotbar_ui.draw()

        # Debug info (only when dt > 0, not paused)
        # if dt > 0:
        #     self.debug_timer += dt
        #     if self.debug_timer >= 1.0:
        #         print(
        #             f"[DEBUG] HP={self.game.player.current_health:.0f} | "
        #             f"O2={self.game.player.current_oxygen:.0f} | "
        #             f"Hunger={self.game.player.current_hunger:.0f}"
        #         )
        #         self.debug_timer = 0
