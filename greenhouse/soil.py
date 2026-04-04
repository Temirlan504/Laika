import pygame
import random

from utils.settings import LAYERS, TILE_SIZE
from utils.timer import Timer
from utils.support import resource_path

from greenhouse.plant import Plant
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
        
        # Timer for plant growth
        self.growth_timer = None

        # Cache for loaded plant sprites
        self.plant_sprite_cache = {}

    def load_plant_sprite(self, plant_type, stage):
        cache_key = (plant_type, stage)
        if cache_key in self.plant_sprite_cache:
            return self.plant_sprite_cache[cache_key]

        sprite_path = resource_path(f"assets/items/crop_stages/{plant_type}/{stage}.png")

        try:
            sprite = pygame.image.load(sprite_path).convert_alpha()
            target_size = int(TILE_SIZE * 0.5)
            sprite = pygame.transform.scale(sprite, (target_size, target_size))
            self.plant_sprite_cache[cache_key] = sprite
            return sprite
        except FileNotFoundError:
            self.plant_sprite_cache[cache_key] = None
            return None
        except Exception as e:
            print(f"[SOIL] Error loading plant sprite {sprite_path}: {e}")
            self.plant_sprite_cache[cache_key] = None
            return None

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
        """Plant a seed from player's inventory OR hotbar"""
        if self.state != "watered" or self.plant is not None:
            return False
        
        # Check if player has the seed in inventory OR hotbar
        has_in_inventory = player.inventory.has_item(seed_id, 1)
        has_in_hotbar = player.hotbar.has_item(seed_id, 1)
        
        if not has_in_inventory and not has_in_hotbar:
            print(f"You don't have any {seed_id}")
            return False
        
        # Get seed definition
        seed_def = get_item(seed_id)
        if not seed_def or not hasattr(seed_def, 'plant_type'):
            print(f"Invalid seed: {seed_id}")
            return False
        
        # Try to remove from hotbar first, then inventory
        removed = False
        if has_in_hotbar:
            removed = player.hotbar.remove_item(seed_id, 1)
        
        if not removed and has_in_inventory:
            removed = player.inventory.remove_item(seed_id, 1)
        
        if removed:
            # Plant it
            self.plant = Plant(seed_def.plant_type, on_visual_change=self.update_visual)
            self.update_visual()
            
            # Start growth timer (plant owns the timer now)
            self.plant.start_growth_timer()
            
            print(f"Planted {seed_def.name}")
            return True
        
        return False

    def grow_to_final(self):
        """Instantly grow plant to final stage (called when sleeping)"""
        if self.plant:
            self.plant.grow_to_final()
            self.update_visual()

    def update(self):
        """Update growth timer"""
        if self.plant:
            self.plant.update()

    def start_growth_timer(self):
        """Start the timer for the next growth stage"""
        if self.plant and not self.plant.is_fully_grown and self.state == "watered":
            # Create timer for next stage
            self.growth_timer = Timer(self.plant.ms_per_stage, self.on_growth_stage_complete)
            self.growth_timer.activate()

    def on_growth_stage_complete(self):
        """Called when a growth stage timer completes"""
        if self.plant and self.state == "watered":
            self.plant.grow()
            self.update_visual()
            
            # Start timer for next stage if not fully grown
            if not self.plant.is_fully_grown:
                self.start_growth_timer()

    def grow_to_final(self):
        """Instantly grow plant to final stage (called when sleeping)"""
        if self.plant:
            self.plant.grow_to_final()
            self.update_visual()
            
            # Cancel any active growth timer
            if self.growth_timer:
                self.growth_timer.deactivate()
                self.growth_timer = None

    def is_harvestable(self):
        return self.plant is not None and self.plant.is_fully_grown
    
    def harvest(self, player):
        """Harvest the crop and add to player inventory"""
        if not self.is_harvestable():
            return

        crop_name = self.plant.plant_type

        # Give back 1-3 seeds (sustainable farming!)
        seed_amount = random.randint(1, 3)
        player.add_item(f"{crop_name}_seed", seed_amount)

        # Give 1-3 crops
        crop_amount = random.randint(1, 3)
        player.add_item(crop_name, crop_amount)

        # Reset soil
        self.plant = None
        if self.growth_timer:
            self.growth_timer.deactivate()
            self.growth_timer = None
        self.state = "dry"
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
            plant_sprite = self.load_plant_sprite(self.plant.plant_type, self.plant.growth_stage)
            
            if plant_sprite:
                # Center the sprite in the tile
                sprite_rect = plant_sprite.get_rect(center=self.image.get_rect().center)
                self.image.blit(plant_sprite, sprite_rect)
            else:
                # Fallback to colored circles if sprite not found
                center = self.image.get_rect().center
                if self.plant.growth_stage == 0:
                    self.image.set_at(center, (0, 255, 0))  # seed
                elif self.plant.growth_stage == 1:
                    pygame.draw.circle(self.image, (0, 200, 0), center, 2)
                elif self.plant.growth_stage == 2:
                    pygame.draw.circle(self.image, (0, 180, 0), center, 6)
                elif self.plant.growth_stage == 3:
                    pygame.draw.circle(self.image, (0, 150, 0), center, 10)


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
