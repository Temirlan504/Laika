import pygame
from camera import CameraGroup

from utils.settings import *
from utils.map_loader import MapLoader

from greenhouse.soil import SoilLayer
from greenhouse.chest import Chest
from greenhouse.chest_ui import ChestUI

from systems.hunger_system import HungerSystem

class GreenhouseState:
    def __init__(self, state_machine, game):
        self.state_machine = state_machine
        self.game = game
        self.screen = game.screen

        self.current_greenhouse_id = None

        self.chests = []
        self.active_chest = None
        self.chest_ui = None
        self.near_chest = False
        self.near_chest_index = None

        # Exit door state
        self.near_exit = False

        self.hunger_system = HungerSystem()

        self.load_sounds()
    
    def load_sounds(self):
        self.sounds = {}
        for name, path in [('chest_open', 'assets/sounds/chest_open.ogg'),
                            ('chest_close', 'assets/sounds/chest_close.ogg')]:
            try:
                sound = pygame.mixer.Sound(path)
                sound.set_volume(0.6)
                self.sounds[name] = sound
            except Exception as e:
                print(f"[SOUND] Could not load {name}: {e}")
                self.sounds[name] = None

    def on_enter(self, greenhouse_id=None, return_pos=None, **kwargs):
        self.current_greenhouse_id = greenhouse_id
        self.return_pos = return_pos

        self.greenhouse_data = self.game.greenhouse_data[greenhouse_id]

        # Load greenhouse map
        self.map_loader = MapLoader("data/tmx/greenhouse.tmx")

        # ---- Setup chests (3 per greenhouse) ----
        if 'chests' not in self.greenhouse_data:
            self.greenhouse_data['chests'] = {}

        self.chests = []

        for i in range(3):
            chest_id = f"{greenhouse_id}_chest_{i}"
            chest = Chest(chest_id)
            chest.load(self.greenhouse_data['chests'].get(chest_id))
            self.chests.append(chest)

        # Sprite groups
        self.collision_sprites = pygame.sprite.Group()
        self.interaction_zones = pygame.sprite.Group()
        self.soil_sprites = pygame.sprite.Group()
        self.soil_layer = SoilLayer(self.soil_sprites, self.game.player)

        self.all_sprites = CameraGroup(
            self.game.player,
            self.screen,
            self.map_loader.map_width,
            self.map_loader.map_height
        )

        self.map_loader.setup(
            self.all_sprites,
            self.collision_sprites,
            self.interaction_zones,
            self.soil_sprites
        )

        # Restore saved soil state
        soil_data = self.greenhouse_data['soil']
        for soil in self.soil_sprites:
            key = soil.tile_pos
            if key in soil_data:
                saved = soil_data[key]
                soil.state = saved['state']
                soil.plant = saved['plant']

                if soil.plant:
                    soil.plant.on_visual_change = soil.update_visual
                soil.update_visual()

                if soil.plant and not soil.plant.is_fully_grown and soil.state == "watered":
                    soil.plant.start_growth_timer()

        # Spawn player inside greenhouse
        if self.map_loader.player_spawnpoint:
            self.game.player.rect.center = self.map_loader.player_spawnpoint
            self.game.player.hitbox.center = self.map_loader.player_spawnpoint

        self.all_sprites.add(self.game.player)
        
        # Center the camera on the greenhouse
        self.center_camera()
        
        self.game.interaction_prompt.hide()
        
        # Show hotbar in greenhouse (you can use tools here)
        if hasattr(self.game, 'hotbar_ui') and self.game.hotbar_ui:
            self.game.hotbar_ui.show()
    
    def on_exit(self):
        """Called when leaving the greenhouse"""
        pass

    def open_chest(self):
        if self.chest_ui or self.near_chest_index is None:
            return

        chest = self.chests[self.near_chest_index]
        chest.open()

        if self.sounds.get('chest_open'):
            self.sounds['chest_open'].play()

        self.active_chest = chest
        self.chest_ui = ChestUI(
            self.game.screen,
            self.game.player.inventory,
            chest.inventory
        )
        
        if hasattr(self.game, 'hotbar_ui') and self.game.hotbar_ui:
            self.game.hotbar_ui.hide()

    def save_soil_state(self):
        soil_data = {}
        for soil in self.soil_sprites:
            soil_data[soil.tile_pos] = {
                'state': soil.state,
                'plant': soil.plant
            }
        self.greenhouse_data['soil'] = soil_data

    def _exit_greenhouse(self):
        """Save state and return to level."""
        self.save_soil_state()
        self.state_machine.change_state("level", return_pos=self.return_pos)

    def center_camera(self):
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        
        self.map_fits_horizontally = self.map_loader.map_width <= screen_width
        self.map_fits_vertically = self.map_loader.map_height <= screen_height
        
        if self.map_fits_horizontally and self.map_fits_vertically:
            map_center_x = self.map_loader.map_width / 2
            map_center_y = self.map_loader.map_height / 2
            
            screen_center_x = screen_width / 2
            screen_center_y = screen_height / 2
            
            self.all_sprites.offset.x = map_center_x - screen_center_x
            self.all_sprites.offset.y = map_center_y - screen_center_y
    
    def update_camera_offset(self):
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        
        if self.map_fits_horizontally:
            map_center_x = self.map_loader.map_width / 2
            screen_center_x = screen_width / 2
            self.all_sprites.offset.x = map_center_x - screen_center_x
        else:
            offset_x = self.game.player.rect.centerx - screen_width // 2
            self.all_sprites.offset.x = max(0, min(offset_x, self.map_loader.map_width - screen_width))
        
        if self.map_fits_vertically:
            map_center_y = self.map_loader.map_height / 2
            screen_center_y = screen_height / 2
            self.all_sprites.offset.y = map_center_y - screen_center_y
        else:
            offset_y = self.game.player.rect.centery - screen_height // 2
            self.all_sprites.offset.y = max(0, min(offset_y, self.map_loader.map_height - screen_height))
    
    def on_resize(self, new_size):
        self.center_camera()

    def draw_soil(self):
        for soil in self.soil_sprites:
            offset_rect = soil.rect.copy()
            offset_rect.topleft -= self.all_sprites.offset
            self.screen.blit(soil.image, offset_rect)

    def handle_input(self, events):
        for event in events:
            if self.chest_ui and self.chest_ui.visible:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                    self.greenhouse_data['chests'][self.active_chest.id] = \
                        self.active_chest.serialize()
                    self.chest_ui.close()
                    self.chest_ui = None
                    self.active_chest = None

                    if self.sounds.get('chest_close'):
                        self.sounds['chest_close'].play()
                    
                    if hasattr(self.game, 'hotbar_ui') and self.game.hotbar_ui:
                        self.game.hotbar_ui.show()
                    return

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.chest_ui.handle_mouse_down(event.pos)
                    return

                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    self.chest_ui.handle_mouse_up(event.pos)
                    return

                return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    self.game.inventory_ui.toggle()
                    if self.game.inventory_ui.visible:
                        if hasattr(self.game, 'hotbar_ui') and self.game.hotbar_ui:
                            self.game.hotbar_ui.hide()
                    else:
                        if hasattr(self.game, 'hotbar_ui') and self.game.hotbar_ui:
                            self.game.hotbar_ui.show()

                elif event.key == pygame.K_e:
                    if self.near_chest:
                        self.open_chest()
                    elif self.near_exit:
                        self._exit_greenhouse()

                elif event.key == pygame.K_ESCAPE:
                    if self.game.inventory_ui.visible:
                        self.game.inventory_ui.hide()
                        if hasattr(self.game, 'hotbar_ui') and self.game.hotbar_ui:
                            self.game.hotbar_ui.show()
                    return
                
                elif pygame.K_1 <= event.key <= pygame.K_9:
                    self.game.player.hotbar.select_slot(event.key - pygame.K_1)

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.game.inventory_ui.handle_mouse_down(
                        pygame.mouse.get_pos(), event.button
                    )
                elif event.button == 4:
                    self.game.player.hotbar.select_previous()
                elif event.button == 5:
                    self.game.player.hotbar.select_next()

            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    result = self.game.inventory_ui.handle_mouse_up(
                        pygame.mouse.get_pos(), 1
                    )
                    if result:
                        from_info, to_info, action_type = result
                        if action_type == 'swap':
                            from_type, from_index = from_info
                            to_type, to_index = to_info
                            
                            if from_type == 'inventory':
                                from_data = self.game.player.inventory.get_slot(from_index)
                            else:
                                from_data = self.game.player.hotbar.get_slot(from_index)
                            
                            if to_type == 'inventory':
                                to_data = self.game.player.inventory.get_slot(to_index)
                            else:
                                to_data = self.game.player.hotbar.get_slot(to_index)
                            
                            if from_data and to_data and from_data["item_id"] == to_data["item_id"]:
                                if not self.game.inventory_ui.stack_items(from_info, to_info):
                                    self.game.inventory_ui.swap_slots(from_info, to_info)
                            else:
                                self.game.inventory_ui.swap_slots(from_info, to_info)

    def refill_oxygen(self, dt):
        self.game.player.refill_oxygen(40 * dt)

    def run(self, dt):
        self.screen.fill("black")

        if self.game.inventory_ui:
            self.game.inventory_ui.update()

        if self.game.inventory_ui.visible or (self.chest_ui and self.chest_ui.visible):
            self.game.player.block_input()
        else:
            self.game.player.unblock_input()

        self.game.player.update(dt, self.collision_sprites)

        events = self.game.player.consume_events()
        for event_data in events:
            event_type = event_data[0]
            pos = event_data[1]
            
            if event_type == 'plant':
                if len(event_data) > 2:
                    seed_id = event_data[2]
                    self.soil_layer.handle_event(event_type, pos, seed_id)
                else:
                    print(f"[ERROR] Plant event missing seed_id! event_data: {event_data}")
            else:
                self.soil_layer.handle_event(event_type, pos)

        self.refill_oxygen(dt)
        self.hunger_system.update(self.game.player, dt)

        self.soil_sprites.update()
        for soil in self.soil_sprites:
            if soil.plant:
                soil.plant.update()
        self.draw_soil()
        self.update_camera_offset()

        sprites = sorted(
            self.all_sprites.sprites(),
            key=lambda spr: (spr.z_index, spr.rect.centery)
        )
        for sprite in sprites:
            offset_rect = sprite.rect.move(-self.all_sprites.offset.x, -self.all_sprites.offset.y)
            self.screen.blit(sprite.image, offset_rect)

        # --- Interaction zone detection ---
        self.near_chest = False
        self.near_chest_index = None
        self.near_exit = False

        self.chest_zones = [z for z in self.interaction_zones if z.name == "chest"]

        for i, zone in enumerate(self.chest_zones):
            if zone.rect.colliderect(self.game.player.hitbox):
                self.near_chest = True
                self.near_chest_index = i
                self.game.interaction_prompt.show("Press E to Open Chest")
                break

        if not self.near_chest:
            # Check exit zone
            for zone in self.interaction_zones:
                if zone.name == "exit" and zone.rect.colliderect(self.game.player.hitbox):
                    self.near_exit = True
                    self.game.interaction_prompt.show("Press E to Exit")
                    break

        if not self.near_chest and not self.near_exit:
            self.game.interaction_prompt.hide()

        if self.chest_ui and self.chest_ui.visible:
            self.chest_ui.draw()
        
        if hasattr(self.game, 'hotbar_ui') and self.game.hotbar_ui:
            self.game.hotbar_ui.draw()
