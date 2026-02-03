import pygame
from utils.settings import *
from camera import CameraGroup
from utils.map_loader import MapLoader
from greenhouse.soil import SoilLayer

class GreenhouseState:
    def __init__(self, state_machine, game):
        self.state_machine = state_machine
        self.game = game
        self.screen = game.screen

        self.current_greenhouse_id = None

    def on_enter(self, greenhouse_id=None, return_pos=None, **kwargs):
        self.current_greenhouse_id = greenhouse_id
        self.return_pos = return_pos

        self.greenhouse_data = self.game.greenhouse_data[greenhouse_id]

        # Load greenhouse map
        self.map_loader = MapLoader("data/tmx/greenhouse.tmx")

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
        self.game.interaction_prompt.hide()

    def save_soil_state(self):
        soil_data = {}
        for soil in self.soil_sprites:
            soil_data[soil.tile_pos] = {
                'state': soil.state,
                'plant': soil.plant
            }
        self.greenhouse_data['soil'] = soil_data

    def draw_soil(self):
        for soil in self.soil_sprites:
            offset_rect = soil.rect.copy()
            offset_rect.topleft -= self.all_sprites.offset
            self.screen.blit(soil.image, offset_rect)

    def handle_input(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                # ESC: Close inventory if open, otherwise exit greenhouse
                if event.key == pygame.K_ESCAPE:
                    if self.game.inventory_ui.visible:
                        self.game.inventory_ui.hide()
                    else:
                        self.save_soil_state()
                        self.state_machine.change_state(
                            "level", return_pos=self.return_pos
                        )
                
                # Toggle inventory (handled here instead of main.py)
                elif event.key == pygame.K_TAB or event.key == pygame.K_i:
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
        if self.game.inventory_ui.visible:
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

        # Draw world
        self.all_sprites.custom_draw()
