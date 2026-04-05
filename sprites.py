import random
import pygame
from utils.settings import *
from utils.support import resource_path

class GenericSprite(pygame.sprite.Sprite):
    def __init__(self, pos, surface, groups, z_index):
        super().__init__(groups)
        self.image = surface
        self.rect = self.image.get_rect(topleft=pos)
        self.mask = pygame.mask.from_surface(self.image)
        self.z_index = z_index

class InteractionSprite(GenericSprite):
    def __init__(self, pos, size, groups, name, text):
        surface = pygame.Surface(size)
        super().__init__(pos, surface, groups, z_index=0)
        self.name = name
        self.text = text

class GreenhouseDome(pygame.sprite.Sprite):
    _next_id = 1  # Class variable to assign unique IDs
    def __init__(self, center_pos, image, groups, z_index=2):
        super().__init__(groups)
        self.door_offset = pygame.Vector2(10, 210)  # Door position relative to dome center
        self.image = image
        self.rect = self.image.get_rect(center=center_pos)
        
        # Full mask for dome-to-dome placement checking
        self.full_mask = pygame.mask.from_surface(self.image)
        
        # Collision mask - only bottom half for player collision
        self.mask = pygame.mask.Mask(self.image.get_size())
        
        # Copy only the bottom half of the full mask to collision mask
        height = self.image.get_height()
        collision_start_y = int(height * 0.3) # Collision starts at 30% of height
        
        for y in range(collision_start_y, height):
            for x in range(self.image.get_width()):
                if self.full_mask.get_at((x, y)):
                    self.mask.set_at((x, y), 1)
        
        self.z_index = z_index
        self.greenhouse_id = GreenhouseDome._next_id
        GreenhouseDome._next_id += 1
        print(f"Created GreenhouseDome with ID: {self.greenhouse_id}")

class Meteorite(pygame.sprite.Sprite):
    # Class variable to cache the meteor image (load once, use many times)
    _meteor_image = None
    
    def __init__(self, pos, groups, z_index=2):
        super().__init__(groups)

        # Load meteor image (cached)
        if Meteorite._meteor_image is None:
            try:
                meteor_img = pygame.image.load(resource_path("assets/tilesets/objects/meteor.png")).convert_alpha()
                Meteorite._meteor_image = pygame.transform.scale(meteor_img, (TILE_SIZE, TILE_SIZE))
                print("Meteor sprite loaded successfully!")
            except FileNotFoundError:
                print("Warning: Could not load meteor.png, using placeholder")
                Meteorite._meteor_image = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                pygame.draw.circle(
                    Meteorite._meteor_image,
                    (140, 140, 160),
                    (TILE_SIZE//2, TILE_SIZE//2),
                    TILE_SIZE//2
                )
        
        self.image = Meteorite._meteor_image.copy()
        self.rect = self.image.get_rect(topleft=pos)
        self.mask = pygame.mask.from_surface(self.image)
        self.z_index = z_index

        self.hp = 3  # hits to break
        
        # Add some visual variety - randomly rotate/flip
        self._add_variety()
    
    def _add_variety(self):
        """Add visual variety to meteorites"""
        # Random rotation (0, 90, 180, 270 degrees)
        angle = random.choice([0, 90, 180, 270])
        if angle != 0:
            self.image = pygame.transform.rotate(self.image, angle)
            self.rect = self.image.get_rect(center=self.rect.center)
            self.mask = pygame.mask.from_surface(self.image)
        
        # Random flip (50% chance)
        if random.random() < 0.5:
            self.image = pygame.transform.flip(self.image, True, False)
            self.mask = pygame.mask.from_surface(self.image)

    def mine(self, player):
        """Player mines this meteorite"""
        self.hp -= 1
        self._flash()

        mining_sounds = [s for k, s in player.sounds.items() if k.startswith('mining') and s is not None]
        if mining_sounds:
            mining_sounds[player._mining_index % len(mining_sounds)].play()
            player._mining_index += 1
        
        if self.hp <= 0:
            amount = random.randint(1, 3)
            player.add_item("iron_ore", amount)
            print(f"Meteorite destroyed! Collected {amount} iron ore")
            self.kill()
        else:
            print(f"Mining meteorite... {self.hp} HP remaining")
    
    def _flash(self):
        """Create a brief flash effect when hit"""
        # Brighten the image temporarily
        flash_surface = self.image.copy()
        flash_surface.fill((255, 255, 255, 100), special_flags=pygame.BLEND_RGBA_ADD)
        self.image = flash_surface

class DeathChest(pygame.sprite.Sprite):
    def __init__(self, pos, groups):
        super().__init__(groups)
        try:
            self.image = pygame.image.load(resource_path("assets/tilesets/objects/chest.png")).convert_alpha()
            self.image = pygame.transform.scale(self.image, (TILE_SIZE, TILE_SIZE))
        except FileNotFoundError:
            self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
            self.image.fill((139, 90, 43))
        self.rect  = self.image.get_rect(center=pos)
        self.z_index = 2
