import pygame
from utils.settings import *
from camera import CameraGroup
from utils.map_loader import MapLoader
from greenhouse.soil import SoilLayer
from greenhouse.chest import Chest
from greenhouse.chest_ui import ChestUI

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
                soil.update_visual()

        # Spawn player inside greenhouse
        if self.map_loader.player_spawnpoint:
            self.game.player.rect.center = self.map_loader.player_spawnpoint
            self.game.player.hitbox.center = self.map_loader.player_spawnpoint

        self.all_sprites.add(self.game.player)
        
        # Center the camera on the greenhouse
        self.center_camera()
        
        self.game.interaction_prompt.hide()

    def open_chest(self):
        if self.chest_ui:
            return

        chest = self.chests[0]  # simple rule for now
        chest.open()

        self.active_chest = chest
        self.chest_ui = ChestUI(
            self.game.screen,
            self.game.player.inventory,
            self.active_chest.inventory
        )

    def save_soil_state(self):
        soil_data = {}
        for soil in self.soil_sprites:
            soil_data[soil.tile_pos] = {
                'state': soil.state,
                'plant': soil.plant
            }
        self.greenhouse_data['soil'] = soil_data

    def center_camera(self):
        """Center the camera on the greenhouse interior, or follow player if map is larger than screen"""
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        
        # Check if the map fits entirely on screen
        self.map_fits_horizontally = self.map_loader.map_width <= screen_width
        self.map_fits_vertically = self.map_loader.map_height <= screen_height
        
        if self.map_fits_horizontally and self.map_fits_vertically:
            # Map fits on screen - center it
            map_center_x = self.map_loader.map_width / 2
            map_center_y = self.map_loader.map_height / 2
            
            screen_center_x = screen_width / 2
            screen_center_y = screen_height / 2
            
            self.all_sprites.offset.x = map_center_x - screen_center_x
            self.all_sprites.offset.y = map_center_y - screen_center_y
        else:
            # Map is larger - will follow player (handled in run method)
            pass
    
    def update_camera_offset(self):
        """Update camera offset - either centered or following player"""
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        
        # Horizontal offset
        if self.map_fits_horizontally:
            # Keep centered horizontally
            map_center_x = self.map_loader.map_width / 2
            screen_center_x = screen_width / 2
            self.all_sprites.offset.x = map_center_x - screen_center_x
        else:
            # Follow player horizontally
            offset_x = self.game.player.rect.centerx - screen_width // 2
            self.all_sprites.offset.x = max(0, min(offset_x, self.map_loader.map_width - screen_width))
        
        # Vertical offset
        if self.map_fits_vertically:
            # Keep centered vertically
            map_center_y = self.map_loader.map_height / 2
            screen_center_y = screen_height / 2
            self.all_sprites.offset.y = map_center_y - screen_center_y
        else:
            # Follow player vertically
            offset_y = self.game.player.rect.centery - screen_height // 2
            self.all_sprites.offset.y = max(0, min(offset_y, self.map_loader.map_height - screen_height))
    
    def on_resize(self, new_size):
        """Handle window resize - recalculate camera behavior"""
        self.center_camera()

    def draw_soil(self):
        for soil in self.soil_sprites:
            offset_rect = soil.rect.copy()
            offset_rect.topleft -= self.all_sprites.offset
            self.screen.blit(soil.image, offset_rect)

    def handle_input(self, events):
        for event in events:
            if self.chest_ui and self.chest_ui.visible:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.chest_ui.handle_mouse_click(event.pos)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.chest_ui:
                        self.greenhouse_data['chests'][self.active_chest.id] = \
                            self.active_chest.serialize()
                        self.chest_ui.close()
                        self.chest_ui = None
                        self.active_chest = None
                        return

                    if self.game.inventory_ui.visible:
                        self.game.inventory_ui.hide()
                        return

                    return
                
                elif event.key == pygame.K_e and self.near_chest and not self.chest_ui:
                    self.open_chest()

                elif event.key == pygame.K_TAB and not self.chest_ui:
                    self.game.inventory_ui.toggle()
            
            # Mouse button DOWN events
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                
                if event.button == 1:  # Left click
                    # Try inventory drag start first
                    clicked_slot = self.game.inventory_ui.handle_mouse_down(mouse_pos, 1)
                    # If clicking outside inventory, handle other interactions here
                
                elif event.button == 3:  # Right click
                    # Handle right-click on inventory (for quick-use)
                    clicked_slot = self.game.inventory_ui.handle_mouse_down(mouse_pos, 3)
                    if clicked_slot is not None:
                        slot = self.game.player.inventory.get_slot(clicked_slot)
                        if slot:
                            self.game.player.use_item(slot["item_id"])
            
            # Mouse button UP events
            if event.type == pygame.MOUSEBUTTONUP:
                mouse_pos = pygame.mouse.get_pos()
                
                if event.button == 1:  # Left click release
                    # Handle drag-and-drop
                    result = self.game.inventory_ui.handle_mouse_up(mouse_pos, 1)
                    if result:
                        from_slot, to_slot, action_type = result
                        
                        if action_type == 'swap':
                            from_data = self.game.player.inventory.get_slot(from_slot)
                            to_data = self.game.player.inventory.get_slot(to_slot)
                            
                            # If both slots have the same item, try to stack
                            if from_data and to_data and from_data["item_id"] == to_data["item_id"]:
                                if not self.game.inventory_ui.stack_items(from_slot, to_slot):
                                    # If stacking failed (full), swap instead
                                    self.game.inventory_ui.swap_slots(from_slot, to_slot)
                            else:
                                # Different items or one empty - just swap
                                self.game.inventory_ui.swap_slots(from_slot, to_slot)

    def refill_oxygen(self, dt):
        self.game.player.refill_oxygen(40 * dt)

    def run(self, dt):
        self.screen.fill("black")

        # Update inventory UI hover state
        if self.game.inventory_ui:
            self.game.inventory_ui.update()

        # Block player input when inventory is open
        if self.game.inventory_ui.visible or (self.chest_ui and self.chest_ui.visible):
            self.game.player.block_input()
        else:
            self.game.player.unblock_input()

        # Update player
        self.game.player.update(dt, self.collision_sprites)

        # Handle tool events from player
        events = self.game.player.consume_events()
        for event_data in events:
            event_type = event_data[0]
            pos = event_data[1]
            
            # For planting, pass the seed_id
            if event_type == 'plant' and len(event_data) > 2:
                seed_id = event_data[2]
                self.soil_layer.handle_event(event_type, pos, seed_id)
            else:
                self.soil_layer.handle_event(event_type, pos)

        # Refill oxygen
        self.refill_oxygen(dt)

        # Update soil tiles
        self.soil_sprites.update()

        # Draw soil below player
        self.draw_soil()

        # Update camera offset (smart centering or following)
        self.update_camera_offset()

        # Draw world with updated offset
        sprites = sorted(
            self.all_sprites.sprites(),
            key=lambda spr: (spr.z_index, spr.rect.centery)
        )

        for sprite in sprites:
            offset_rect = sprite.rect.move(-self.all_sprites.offset.x, -self.all_sprites.offset.y)
            self.screen.blit(sprite.image, offset_rect)

        self.near_chest = False
        for zone in self.interaction_zones:
            if zone.name == "chest" and zone.rect.colliderect(self.game.player.hitbox):
                self.near_chest = True
                self.game.interaction_prompt.show("Press E to Open Chest")
                break

        if not self.near_chest:
            self.game.interaction_prompt.hide()

        if self.chest_ui and self.chest_ui.visible:
            self.chest_ui.draw()
