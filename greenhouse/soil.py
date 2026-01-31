import pygame
import random
from utils.settings import LAYERS, TILE_SIZE
from greenhouse.plant import Plant
from utils.timer import Timer
from items import get_item

class SoilTile(pygame.sprite.Sprite):
    def __init__(self, rect, groups, z_index=LAYERS['ground']):
        super().__init__(groups)
        self.rect = rect
        self.image = pygame.Surface(rect.size, pygame.SRCALPHA)
        self.z_index = z_index

        self.state = "dry"
        self.plant = None
        self.tile_pos = (rect.x // TILE_SIZE, rect.y // TILE_SIZE)

        # Timer for plant growth (in milliseconds)
        self.growth_timer = Timer(1500000000, self.advance_plant)

    def hoe(self):
        if self.state == "dry":
            print("Tilled soil")
            self.state = "hoed"
            self.update_visual()

    def water(self):
        if self.state == "hoed":
            print("Watered soil")
            self.state = "watered"
            self.update_visual()

    def plant_seed(self, player, seed_id):
        """Plant a seed from player's inventory"""
        if self.state != "watered" or self.plant is not None:
            return False
        
        # Check if player has the seed
        if not player.has_item(seed_id, 1):
            print(f"You don't have any {seed_id}")
            return False
        
        # Get seed definition
        seed_def = get_item(seed_id)
        if not seed_def or not hasattr(seed_def, 'plant_type'):
            print(f"Invalid seed: {seed_id}")
            return False
        
        # Remove seed from inventory
        if player.remove_item(seed_id, 1):
            # Plant it
            self.plant = Plant(seed_def.plant_type)
            self.update_visual()
            self.growth_timer.activate()
            print(f"Planted {seed_def.name}")
            return True
        
        return False

    def advance_plant(self):
        if self.plant and self.state == "watered":
            self.plant.grow()
            self.update_visual()

            # continue growing until fully grown
            if not self.plant.is_fully_grown:
                self.growth_timer.activate()

    def is_harvestable(self):
        return self.plant is not None and self.plant.is_fully_grown
    
    def harvest(self, player):
        """Harvest the crop and add to player inventory"""
        if not self.is_harvestable():
            return

        crop_name = self.plant.plant_type

        # Give back 1 seed (sustainable farming!)
        player.add_item(f"{crop_name}_seed", 1)

        # Give 1-3 crops
        crop_amount = random.randint(1, 3)
        player.add_item(crop_name, crop_amount)

        # Reset soil
        self.plant = None
        self.state = "dry"
        self.growth_timer.deactivate()
        self.update_visual()

        print(f"Harvested {crop_amount}x {crop_name} + 1 seed")

    def update_visual(self):
        self.image.fill((0, 0, 0, 0))  # clear

        if self.state == "hoed":
            pygame.draw.rect(self.image, (120, 90, 50), self.image.get_rect())

        elif self.state == "watered":
            pygame.draw.rect(self.image, (60, 80, 120), self.image.get_rect())

        # Plant visual
        if self.plant:
            center = self.image.get_rect().center

            if self.plant.growth_stage == 0:
                self.image.set_at(center, (0, 255, 0))  # seed
            elif self.plant.growth_stage == 1:
                pygame.draw.circle(self.image, (0, 200, 0), center, 2)
            elif self.plant.growth_stage == 2:
                pygame.draw.circle(self.image, (0, 180, 0), center, 6)
            elif self.plant.growth_stage == 3:
                pygame.draw.circle(self.image, (0, 150, 0), center, 10)

    def update(self):
        self.growth_timer.update()


class SoilLayer:
    def __init__(self, soil_sprites, player):
        self.soil_sprites = soil_sprites
        self.player = player

    def get_tile_at_pos(self, pos):
        for soil in self.soil_sprites:
            if soil.rect.collidepoint(pos):
                return soil
        return None

    def handle_event(self, event_type, pos, seed_id=None):
        """Handle farming events from player"""
        soil = self.get_tile_at_pos(pos)
        if soil is None:
            return

        if event_type == 'hoe':
            soil.hoe()
        
        elif event_type == 'water':
            soil.water()
        
        elif event_type == 'plant':
            # Use the seed_id passed from player
            if seed_id:
                soil.plant_seed(self.player, seed_id)
        
        elif event_type == 'harvest':
            if soil.is_harvestable():
                soil.harvest(self.player)
