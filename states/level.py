import random
import pygame
from sprites import GreenhouseDome, Meteorite

from utils.settings import *
from utils.fade_effect import FadeEffect, NightOverlay
from utils.map_loader import MapLoader
from utils.timer import Timer
from utils.support import resource_path

from camera import CameraGroup
from building.preview import DomePreview
from building.door import DoorInteractionZone

from systems.time_system_fsm import SleepState
from systems.oxygen_system import OxygenSystem
from systems.hunger_system import HungerSystem
from ui.hud import IronOreCounterUI, OxygenWarningUI


class LevelState:
    # --- Class-level constants ---
    LAST_SOL = 3
    DOME_IRON_COST = 50
    MAX_DOMES = 15

    def __init__(self, state_machine, game):
        self.state_machine = state_machine
        self.game = game
        self.screen = game.screen
        self.fade_effect = FadeEffect(self.screen)
        self.night_overlay = NightOverlay(self.game.clock_system, self.screen)

        self.sleep_state = SleepState.AWAKE

        self.build_mode = False
        self.delete_mode = False
        self.dome_sprites = pygame.sprite.Group()

        self.ground_positions = []
        self.meteorites = pygame.sprite.Group()
        self.max_meteorites = 30
        self.meteor_spawn_timer = Timer(10000)
        self.meteor_spawn_timer.activate()

        # --- Interaction state (initialised here so handle_input is always safe) ---
        self.current_interaction = None
        self.current_greenhouse = None

        # Guard so the ending is triggered at most once
        self.ending_triggered = False

        # --- DEBUG MODE ---
        self.debug_mode = False
        self.debug_timer = 0

        # Load Tiled map
        self.map_path = resource_path('data/tmx/main.tmx')
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

        # Load greenhouse image — kept as an instance attribute so _spawn_dome
        # can reuse it without reloading from disk each time.
        dome_image = pygame.image.load(resource_path("assets/dome.png")).convert_alpha()
        dome_image = pygame.transform.scale(dome_image, (612, 429))
        self._dome_image = dome_image
        self.preview = DomePreview(dome_image)

        # Cached player hitbox mask for build-mode collision (rebuilt on resize)
        self._player_hitbox_mask = None

        # Player stats
        self.oxygen_system = OxygenSystem()
        self.hunger_system = HungerSystem()

        # HUD: iron ore counter
        self.iron_ore_counter = IronOreCounterUI(self.game.player, self.screen)

        # Oxygen warnings
        self.oxygen_warning_ui = OxygenWarningUI(self.game.player, self.screen)

        self.setup_level()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def on_resize(self, size):
        self.screen = self.game.screen
        self.fade_effect.on_resize(self.screen)
        self.night_overlay.on_resize(self.screen)
        self._player_hitbox_mask = None

    def setup_level(self):
        if self.game.player is None:
            raise RuntimeError("Player must be initialised before entering level state")

        saved_position = self.game.player.rect.center

        self.game_map.setup(
            self.all_sprites, self.collision_sprites,
            self.interaction_zones, ground_positions=self.ground_positions
        )

        default_start = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        if saved_position == default_start and self.game_map.player_spawnpoint:
            self.game.player.rect.center = self.game_map.player_spawnpoint
            self.game.player.hitbox.center = self.game_map.player_spawnpoint
        else:
            self.game.player.rect.center = saved_position
            self.game.player.hitbox.center = saved_position

        self.all_sprites.add(self.game.player)
        self.dynamic_sprites.add(self.game.player)
        if not hasattr(self.game, '_pending_buildings'):
            pos = self.game_map.starter_greenhouse_pos
            if pos:
                self._spawn_dome(pos)
            else:
                print("[WARN] No 'starter_greenhouse' marker found in Tiled markers layer!")

    def _spawn_dome(self, center_pos):
        """Spawn a greenhouse dome at center_pos and register its door zone.
        Shared by the starter dome and player-built domes."""
        # Ensure greenhouse_data exists (may not yet during setup_level on fresh start)
        if not hasattr(self.game, 'greenhouse_data'):
            self.game.greenhouse_data = {}

        dome = GreenhouseDome(
            center_pos=center_pos,
            image=self._dome_image,
            groups=[self.all_sprites, self.collision_sprites, self.dome_sprites]
        )
        print(f"[DOME] Spawned at {center_pos}, rect.center={dome.rect.center}, id={dome.greenhouse_id}")

        if dome.greenhouse_id not in self.game.greenhouse_data:
            self.game.greenhouse_data[dome.greenhouse_id] = {"soil": {}}

        door_world_pos = pygame.Vector2(dome.rect.center) + dome.door_offset
        door_rect = pygame.Rect(0, 0, 96, 48)
        door_rect.center = door_world_pos

        zone = DoorInteractionZone(rect=door_rect, owner=dome, text="Press E to Enter")
        self.interaction_zones.add(zone)
        return dome

    def on_enter(self, return_pos=None, **kwargs):
        self.ending_triggered = False
        self.game.day_ui.day = self.game.day_cycle.day

        if not self.game.player:
            print("ERROR: Level entered without player! Returning to main menu.")
            self.state_machine.change_state("main_menu")
            return

        if hasattr(self.game, '_pending_buildings'):
            self.game.save_manager.load_pending_buildings(self.game)

        self.game.day_ui.visible = True
        self.game.interaction_prompt.visible = False

        if self.game.inventory_ui:
            self.game.inventory_ui.visible = False
        if self.game.hotbar_ui:
            self.game.hotbar_ui.visible = True
        if self.game.health_bar_ui:
            self.game.health_bar_ui.visible = True
        if self.game.oxygen_bar_ui:
            self.game.oxygen_bar_ui.visible = True
        if self.game.hunger_bar_ui:
            self.game.hunger_bar_ui.visible = True

        self.game.player.unblock_input()

        if return_pos:
            self.game.player.rect.center = return_pos
            self.game.player.hitbox.center = return_pos

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------
    def handle_input(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.game.inventory_ui.visible:
                        self.game.inventory_ui.hide()
                        self.game.hotbar_ui.show()
                    else:
                        self.state_machine.change_state("pause_menu")

                elif event.key == pygame.K_TAB:
                    self.game.inventory_ui.toggle()
                    if self.game.inventory_ui.visible:
                        self.game.hotbar_ui.hide()
                    else:
                        self.game.hotbar_ui.show()

                elif event.key == pygame.K_e:
                    if not self.current_interaction:
                        return
                    zone = self.current_interaction

                    if isinstance(zone, DoorInteractionZone):
                        if self.current_greenhouse:
                            self.state_machine.change_state(
                                "greenhouse",
                                greenhouse_id=self.current_greenhouse.greenhouse_id,
                                return_pos=self.game.player.rect.center
                            )
                        return

                    if zone.text == "Press E to Sleep":
                        if self.game.clock_system.can_sleep():
                            self.start_sleep()
                        else:
                            print("Too early to sleep")

                elif event.key == pygame.K_b:
                    self.build_mode = not self.build_mode
                    if self.build_mode:
                        self.delete_mode = False
                    print(f"Build mode: {'ON' if self.build_mode else 'OFF'}")

                elif event.key == pygame.K_x:
                    self.delete_mode = not self.delete_mode
                    if self.delete_mode:
                        self.build_mode = False
                    print(f"Delete mode: {'ON' if self.delete_mode else 'OFF'}")

                elif pygame.K_1 <= event.key <= pygame.K_9:
                    self.game.player.hotbar.select_slot(event.key - pygame.K_1)

            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()

                if event.button == 1:
                    clicked_slot = self.game.inventory_ui.handle_mouse_down(mouse_pos, 1)

                    if clicked_slot is None:
                        if self.delete_mode:
                            self._handle_delete_click()
                        elif self.build_mode:
                            self._handle_build_click()

                elif event.button == 4:
                    self.game.player.hotbar.select_previous()
                elif event.button == 5:
                    self.game.player.hotbar.select_next()

            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    mouse_pos = pygame.mouse.get_pos()
                    result = self.game.inventory_ui.handle_mouse_up(mouse_pos, 1)
                    if result:
                        from_info, to_info, action_type = result
                        if action_type == 'swap':
                            self._resolve_inventory_drag(from_info, to_info)

    def _handle_delete_click(self):
        mouse_world_pos = self.mouse_to_world()
        for dome in self.dome_sprites:
            if not dome.rect.collidepoint(mouse_world_pos):
                continue
            local_x = int(mouse_world_pos.x - dome.rect.x)
            local_y = int(mouse_world_pos.y - dome.rect.y)
            if 0 <= local_x < dome.rect.width and 0 <= local_y < dome.rect.height:
                if dome.mask.get_at((local_x, local_y)):
                    for zone in self.interaction_zones:
                        if isinstance(zone, DoorInteractionZone) and zone.owner == dome:
                            zone.kill()
                            break
                    dome.kill()
                    print("Dome deleted!")
                    break

    def _handle_build_click(self):
        if len(self.dome_sprites) >= self.MAX_DOMES:
            print("Maximum number of greenhouses reached")
            return

        if not self.preview.valid:
            return

        self._consume_iron_ore()
        self._spawn_dome(self.preview.rect.center)

    def _resolve_inventory_drag(self, from_info, to_info):
        """Stack or swap two inventory/hotbar slots after a drag-and-drop."""
        from_type, from_index = from_info
        to_type, to_index = to_info

        from_data = (
            self.game.player.inventory.get_slot(from_index)
            if from_type == 'inventory'
            else self.game.player.hotbar.get_slot(from_index)
        )
        to_data = (
            self.game.player.inventory.get_slot(to_index)
            if to_type == 'inventory'
            else self.game.player.hotbar.get_slot(to_index)
        )

        if from_data and to_data and from_data["item_id"] == to_data["item_id"]:
            if not self.game.inventory_ui.stack_items(from_info, to_info):
                self.game.inventory_ui.swap_slots(from_info, to_info)
        else:
            self.game.inventory_ui.swap_slots(from_info, to_info)

    # ------------------------------------------------------------------
    # Sleep / day cycle
    # ------------------------------------------------------------------
    def start_sleep(self):
        if self.sleep_state != SleepState.AWAKE:
            return
        self.sleep_state = SleepState.FADING_OUT
        self.game.player.block_input()
        self.fade_effect.fade_in(self.on_fade_out_complete)

    def on_fade_out_complete(self):
        self.sleep_state = SleepState.ASLEEP
        self.game.music_system.stop()  # Stop music immediately on sleep

        # Advance the day exactly once for sleeping
        self.game.day_cycle.reset_cycle()
        self.game.day_cycle.try_advance_day("sleep")

        for greenhouse in self.game.greenhouse_data.values():
            for data in greenhouse['soil'].values():
                if data['plant']:
                    data['plant'].grow_to_final()

        self.game.save_manager.auto_save(self.game)

        # Set time to 6 AM
        self.game.clock_system.set_time(6, 0)

        if self.check_ending_trigger():
            return

        self.fade_effect.fade_out(self.on_fade_in_complete)

    def check_ending_trigger(self):
        """Trigger the ending scene if we've reached the final day.
        Safe to call multiple times — acts only once."""
        if self.ending_triggered:
            return False
        if self.game.day_cycle.day >= self.LAST_SOL:
            print(f"[ENDING] Reached final day ({self.LAST_SOL})! Triggering ending...")
            self.ending_triggered = True
            if self.game.player:
                self.game.player.block_input()
            self.state_machine.change_state("credits")
            return True
        return False

    def on_new_day(self, day):
        """Called when a new day starts (from DayCycle)."""
        print(f"[LEVEL] New day started: Sol {day}")
        self.check_ending_trigger()

    def on_fade_in_complete(self):
        self.sleep_state = SleepState.AWAKE
        self.game.music_system.resume()  # Resume ambient music on wake
        self.game.player.unblock_input()

    # ------------------------------------------------------------------
    # Collision / interaction
    # ------------------------------------------------------------------
    def check_collisions(self, dt):
        if not self.game.player:
            return

        for sprite in self.dynamic_sprites:
            if sprite == self.game.player:
                sprite.update(dt, self.collision_sprites)
            else:
                sprite.update(dt)

        self.current_interaction = None
        self.current_greenhouse = None

        for zone in self.interaction_zones:
            if self.game.player.hitbox.colliderect(zone.rect):
                self.current_interaction = zone
                if isinstance(zone, DoorInteractionZone):
                    self.current_greenhouse = zone.owner
                break

        if self.current_interaction:
            if isinstance(self.current_interaction, DoorInteractionZone):
                self.game.interaction_prompt.show("Press E to Enter Greenhouse")
            else:
                self.game.interaction_prompt.show(self.current_interaction.text)
        else:
            self.game.interaction_prompt.hide()

    # ------------------------------------------------------------------
    # Build mode helpers
    # ------------------------------------------------------------------
    def _get_player_hitbox_mask(self):
        """Return a cached filled mask matching the player's current hitbox."""
        hitbox = self.game.player.hitbox
        if (self._player_hitbox_mask is None or
                self._player_hitbox_mask.get_size() != hitbox.size):
            self._player_hitbox_mask = pygame.mask.Mask(hitbox.size)
            self._player_hitbox_mask.fill()
        return self._player_hitbox_mask

    def _has_enough_iron_ore(self):
        """Return True if the player holds at least DOME_IRON_COST iron ore."""
        inv_total = self.game.player.inventory.get_total("iron_ore")
        hotbar_total = sum(
            slot["quantity"]
            for slot in self.game.player.hotbar.slots
            if slot and slot["item_id"] == "iron_ore"
        )
        return (inv_total + hotbar_total) >= self.DOME_IRON_COST

    def _consume_iron_ore(self):
        """Remove DOME_IRON_COST iron ore (hotbar first, then inventory)."""
        remaining = self.DOME_IRON_COST

        for i, slot in enumerate(self.game.player.hotbar.slots):
            if remaining <= 0:
                break
            if slot and slot["item_id"] == "iron_ore":
                taken = min(slot["quantity"], remaining)
                slot["quantity"] -= taken
                remaining -= taken
                if slot["quantity"] == 0:
                    self.game.player.hotbar.slots[i] = None

        if remaining > 0:
            self.game.player.inventory.remove_item("iron_ore", remaining)

    def can_place_dome(self, preview, obstacles):
        if not self._has_enough_iron_ore():
            return False

        if preview.rect.colliderect(self.game.player.hitbox):
            offset = (
                self.game.player.hitbox.x - preview.rect.x,
                self.game.player.hitbox.y - preview.rect.y,
            )
            if preview.mask.overlap(self._get_player_hitbox_mask(), offset):
                return False

        for obj in obstacles:
            if not preview.rect.colliderect(obj.rect):
                continue
            if hasattr(obj, "mask") and obj.mask:
                offset = (obj.rect.x - preview.rect.x, obj.rect.y - preview.rect.y)
                if preview.mask.overlap(obj.mask, offset):
                    return False
        return True

    # ------------------------------------------------------------------
    # Meteor spawning
    # ------------------------------------------------------------------
    def try_spawn_meteor(self):
        if len(self.meteorites) >= self.max_meteorites or not self.ground_positions:
            return

        meteor_size = (TILE_SIZE, TILE_SIZE)
        meteor_mask = pygame.mask.Mask(meteor_size)
        meteor_mask.fill()

        for attempt in range(15):
            pos = random.choice(self.ground_positions)
            meteor_spawn_rect = pygame.Rect(pos[0], pos[1], TILE_SIZE, TILE_SIZE)

            if self._is_valid_meteor_spawn(meteor_spawn_rect, meteor_mask):
                Meteorite(
                    pos=pos,
                    groups=[self.all_sprites, self.meteorites, self.collision_sprites]
                )
                print(f"[METEOR] Spawned at {pos} - Total: {len(self.meteorites)}/{self.max_meteorites}")
                return

        print("[METEOR] Failed to find a valid spawn position after 15 attempts")

    def _is_valid_meteor_spawn(self, meteor_rect, meteor_mask):
        """Return True if meteor_rect is a valid spawn location."""
        player_center = pygame.Vector2(self.game.player.rect.center)
        meteor_center = pygame.Vector2(meteor_rect.center)
        if player_center.distance_to(meteor_center) < TILE_SIZE * 3:
            return False

        for dome in self.dome_sprites:
            if meteor_rect.colliderect(dome.rect):
                if hasattr(dome, 'mask') and dome.mask:
                    offset = (dome.rect.x - meteor_rect.x, dome.rect.y - meteor_rect.y)
                    if meteor_mask.overlap(dome.mask, offset):
                        return False

        meteorite_set = set(self.meteorites)
        dome_set = set(self.dome_sprites)
        for sprite in self.collision_sprites:
            if sprite in meteorite_set or sprite in dome_set or sprite is self.game.player:
                continue
            if meteor_rect.colliderect(sprite.rect):
                if hasattr(sprite, 'mask') and sprite.mask:
                    offset = (sprite.rect.x - meteor_rect.x, sprite.rect.y - meteor_rect.y)
                    if meteor_mask.overlap(sprite.mask, offset):
                        return False
                else:
                    return False

        min_dist_sq = (TILE_SIZE * 2) ** 2
        for meteor in self.meteorites:
            dx = meteor.rect.centerx - meteor_rect.centerx
            dy = meteor.rect.centery - meteor_rect.centery
            if dx * dx + dy * dy < min_dist_sq:
                return False

        return True

    # ------------------------------------------------------------------
    # Tool events
    # ------------------------------------------------------------------
    def handle_tool_events(self):
        for event_data in self.game.player.consume_events():
            event_type, pos = event_data[0], event_data[1]
            if event_type == 'pickaxe':
                threshold_sq = (TILE_SIZE * 0.7) ** 2
                for meteor in self.meteorites:
                    dx = meteor.rect.centerx - pos[0]
                    dy = meteor.rect.centery - pos[1]
                    if dx * dx + dy * dy <= threshold_sq:
                        meteor.mine(self.game.player)
                        break

    # ------------------------------------------------------------------
    # Draw helpers
    # ------------------------------------------------------------------
    def draw_debug(self):
        if not self.debug_mode:
            return
        cx = self.all_sprites.player.rect.centerx - self.screen.get_width() // 2
        cy = self.all_sprites.player.rect.centery - self.screen.get_height() // 2
        for sprite in self.collision_sprites:
            r = sprite.rect.move(-cx, -cy)
            pygame.draw.rect(self.screen, (0, 255, 0), r, 2)
        for zone in self.interaction_zones:
            r = zone.rect.move(-cx, -cy)
            pygame.draw.rect(self.screen, (0, 0, 255), r, 2)

    def draw_delete_cursor(self):
        mp = pygame.mouse.get_pos()
        pygame.draw.circle(self.screen, (255, 0, 0), mp, 10, 2)
        pygame.draw.line(self.screen, (255, 0, 0), (mp[0] - 7, mp[1] - 7), (mp[0] + 7, mp[1] + 7), 2)
        pygame.draw.line(self.screen, (255, 0, 0), (mp[0] + 7, mp[1] - 7), (mp[0] - 7, mp[1] + 7), 2)

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    def mouse_to_world(self):
        mx, my = pygame.mouse.get_pos()
        return pygame.Vector2(
            mx + self.all_sprites.offset.x,
            my + self.all_sprites.offset.y
        )

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def run(self, dt):
        self.screen.fill('black')

        self.fade_effect.update(dt)
        self.night_overlay.update()

        if self.sleep_state == SleepState.AWAKE and dt > 0:
            if self.game.inventory_ui:
                self.game.inventory_ui.update()

            for greenhouse in self.game.greenhouse_data.values():
                for data in greenhouse.get('soil', {}).values():
                    if data.get('plant'):
                        data['plant'].update()

            self.meteor_spawn_timer.update()
            if self.meteor_spawn_timer.deactivate:
                if len(self.meteorites) < self.max_meteorites:
                    self.try_spawn_meteor()
                self.meteor_spawn_timer.activate()

            if self.game.inventory_ui.visible:
                self.game.player.block_input()
            else:
                self.game.player.unblock_input()

            self.check_collisions(dt)
            self.oxygen_system.update(self.game.player, dt)
            self.hunger_system.update(self.game.player, dt)
            self.handle_tool_events()

        elif dt == 0 and self.game.player:
            self.game.player.block_input()

        if self.build_mode:
            self.preview.set_position(self.mouse_to_world())
            self.preview.set_valid(
                self.can_place_dome(self.preview, self.collision_sprites.sprites())
            )

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

        self.iron_ore_counter.draw()
        self.oxygen_warning_ui.draw(dt=dt)
