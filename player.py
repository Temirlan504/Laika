import pygame
from items import ItemType, get_item
from utils.settings import *
from utils.support import import_folder
from utils.timer import Timer
from systems.inventory_system import Hotbar, Inventory

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, group):
        super().__init__(group)
        self.import_assets()
        self.status = 'down_idle'
        self.frame_index = 0
        self.events = []

        # Player placeholder
        self.image = self.animations[self.status][self.frame_index]
        self.image = pygame.transform.scale(self.image, (TILE_SIZE, TILE_SIZE))
        self.rect = self.image.get_rect(center=pos)
        self.hitbox = self.rect.inflate((-25, -20))
        self.z_index = LAYERS['player']

        # Initialize inventory system
        self.inventory = Inventory(size=36)
        self.hotbar = Hotbar(num_slots=9)
        self._give_starter_items()  # Give starter items on creation

        self.max_health = 100
        self.current_health = self.max_health
        self.max_hunger = 100
        self.current_hunger = self.max_hunger
        self.max_oxygen = 100
        self.current_oxygen = self.max_oxygen
        self.is_alive = True

        # Movement attributes
        self.direction = pygame.math.Vector2(0, 0)
        self.speed = 150
        self.input_blocked = False

        # Timers
        self.timers = {
            'tool_use': Timer(300, self.use_tool),
            'harvest': Timer(200)
        }

        # Tools attributes
        self.tools = ['hoe', 'pickaxe', 'watering_can', 'seed']
        self.selected_tool = 'pickaxe'
        self.selected_seed = 'potato_seed'  # Track which seed to plant
        self.tool_ray_length = 32

    def _give_starter_items(self):
        """Give player starting items - called once on initialization"""
        self.inventory.add_item("potato_seed", 10)
        self.inventory.add_item("tomato_seed", 5)
        self.inventory.add_item("carrot_seed", 3)
        
        # Place starter tools in hotbar for convenience
        self.hotbar.set_slot(0, {"item_id": "pickaxe", "quantity": 1})
        self.hotbar.set_slot(1, {"item_id": "hoe", "quantity": 1})
        self.hotbar.set_slot(2, {"item_id": "watering_can", "quantity": 1})

    def take_damage(self, amount):
        self.current_health = max(0, self.current_health - amount)
        if self.current_health == 0:
            self.is_alive = False

    def heal(self, amount):
        self.current_health = min(self.max_health, self.current_health + amount)

    def refill_oxygen(self, amount):
        self.current_oxygen = min(self.max_oxygen, self.current_oxygen + amount)
    
    def restore_hunger(self, amount):
        """Restore hunger (for eating food)"""
        self.current_hunger = min(self.max_hunger, self.current_hunger + amount)

    def add_item(self, item_id, amount=1):
        """Add item to inventory"""
        return self.inventory.add_item(item_id, amount)
    
    def remove_item(self, item_id, amount=1):
        """Remove item from inventory"""
        return self.inventory.remove_item(item_id, amount)
    
    def has_item(self, item_id, amount=1):
        """Check if player has item in inventory"""
        return self.inventory.has_item(item_id, amount)
    
    def use_item(self, item_id):
        """Use/consume an item from inventory"""
        from items import get_item, ItemType
        
        item_def = get_item(item_id)
        if not item_def:
            return False
        
        # Handle food items
        if item_def.type == ItemType.FOOD:
            if self.remove_item(item_id, 1):
                if hasattr(item_def, 'hunger_restore'):
                    self.restore_hunger(item_def.hunger_restore)
                if hasattr(item_def, 'health_restore'):
                    self.heal(item_def.health_restore)
                print(f"Consumed {item_def.name}")
                return True
        
        # Handle seed items - set as selected seed
        if item_def.type == ItemType.SEED:
            self.selected_tool = 'seed'
            self.selected_seed = item_id
            print(f"Selected {item_def.name} for planting")
            return True
        
        # Handle tool items
        if item_def.type == ItemType.TOOL:
            self.selected_tool = item_id
            print(f"Equipped {item_def.name}")
            return True
        
        return False

    def consume_events(self):
        events = self.events.copy()
        self.events.clear()
        return events

    def use_tool(self):
        """Use the currently selected hotbar item"""
        target_pos = self.get_target_pos()
        
        # Get the item from the selected hotbar slot
        item_id = self.hotbar.get_selected_item_id()
        
        print(f"[PLAYER] use_tool() - item_id: {item_id}")  # DEBUG
        
        if not item_id:
            return  # No item in selected slot
        
        # Get item definition to check its type/category
        item = get_item(item_id)
        if not item:
            print(f"[PLAYER] Item not found in database: {item_id}")  # DEBUG
            return
        
        print(f"[PLAYER] Item type: {item.type}")  # DEBUG
        
        # Dispatch based on item type
        if item.type == ItemType.TOOL:
            if item_id == 'hoe':
                self.events.append(('hoe', target_pos))
            elif item_id == 'watering_can':
                self.events.append(('water', target_pos))
            elif item_id == 'pickaxe':
                self.events.append(('pickaxe', target_pos))
        
        elif item.type == ItemType.SEED:
            print(f"[PLAYER] Planting seed: {item_id}, target: {target_pos}")  # DEBUG
            self.events.append(('plant', target_pos, item_id))
        
        elif item.type == ItemType.FOOD:
            # For food items, etc.
            self.use_item(item_id)

    def handle_input(self):
        if self.input_blocked:
            return
        keys = pygame.key.get_pressed()

        if not self.timers['tool_use'].active:
            # Movement
            self.direction.x = 0
            self.direction.y = 0

            if keys[pygame.K_a]:
                self.direction.x = -1
                self.status = 'left'
            if keys[pygame.K_d]:
                self.direction.x = 1
                self.status = 'right'
            if keys[pygame.K_w]:
                self.direction.y = -1
                self.status = 'up'
            if keys[pygame.K_s]:
                self.direction.y = 1
                self.status = 'down'

            # Tool use with SPACE
            if keys[pygame.K_SPACE]:
                # Check if the selected hotbar item is a tool/seed
                item_id = self.hotbar.get_selected_item_id()
                if item_id:
                    item = get_item(item_id)
                    # Only activate tool timer for tools and seeds (use .type not .category)
                    if item and item.type in [ItemType.TOOL, ItemType.SEED]:
                        self.timers['tool_use'].activate()
                        self.frame_index = 0
                        self.direction = pygame.math.Vector2(0, 0)
            
            # Harvest (interaction key)
            if keys[pygame.K_e] and not self.timers['harvest'].active:
                self.timers['harvest'].activate()
                target_pos = self.get_target_pos()
                self.events.append(('harvest', target_pos))

    def get_target_pos(self):
        """Return a position slightly in front of the player (tool ray)"""
        direction = pygame.math.Vector2(0, 0)

        if 'up' in self.status:
            direction.y = -1
        elif 'down' in self.status:
            direction.y = 1
        elif 'left' in self.status:
            direction.x = -1
        elif 'right' in self.status:
            direction.x = 1

        if direction.length() == 0:
            return self.hitbox.center

        return self.hitbox.center + direction * self.tool_ray_length

    def import_assets(self):
        self.animations = {
            'up_idle': [], 'down_idle': [], 'left_idle': [], 'right_idle': [],
            'up': [], 'down': [], 'left': [], 'right': [],
            'up_hoe': [], 'down_hoe': [], 'left_hoe': [], 'right_hoe': [],
            'up_pickaxe': [], 'down_pickaxe': [], 'left_pickaxe': [], 'right_pickaxe': [],
            'up_watering_can': [], 'down_watering_can': [], 'left_watering_can': [], 'right_watering_can': [],
            'up_seed': [], 'down_seed': [], 'left_seed': [], 'right_seed': []
        }

        for animation in self.animations.keys():
            full_path = 'assets/player/' + animation
            self.animations[animation] = import_folder(full_path)

    def animate(self, dt):
        self.animation_speed = 10
        self.frame_index += self.animation_speed * dt
        if self.frame_index >= len(self.animations[self.status]):
            self.frame_index = 0
        self.image = self.animations[self.status][int(self.frame_index)]

    def block_input(self):
        self.input_blocked = True
        self.direction = pygame.math.Vector2(0, 0)

    def unblock_input(self):
        self.input_blocked = False

    def check_mask_collision(self, sprite):
        """Check if player's hitbox collides with sprite's mask"""
        if not hasattr(sprite, 'mask') or not sprite.mask:
            return False
        
        offset_x = sprite.rect.left - self.hitbox.left
        offset_y = sprite.rect.top - self.hitbox.top
        
        player_mask = pygame.mask.Mask(self.hitbox.size)
        player_mask.fill()
        
        return player_mask.overlap(sprite.mask, (offset_x, offset_y)) is not None

    def move_player(self, dt, collision_sprites):
        if self.direction.magnitude() > 0:
            self.direction = self.direction.normalize()

        # Horizontal movement and collision detection
        original_x = self.hitbox.x
        self.hitbox.x += self.direction.x * self.speed * dt
        
        for sprite in collision_sprites:
            if hasattr(sprite, 'mask') and sprite.mask:
                if self.hitbox.colliderect(sprite.rect) and self.check_mask_collision(sprite):
                    low, high = 0.0, 1.0
                    for _ in range(8):
                        mid = (low + high) / 2
                        self.hitbox.x = original_x + self.direction.x * self.speed * dt * mid
                        
                        if self.check_mask_collision(sprite):
                            high = mid
                        else:
                            low = mid
                    
                    self.hitbox.x = original_x + self.direction.x * self.speed * dt * low
                    break
            else:
                if self.hitbox.colliderect(sprite.rect):
                    if self.direction.x > 0:
                        self.hitbox.right = sprite.rect.left
                    if self.direction.x < 0:
                        self.hitbox.left = sprite.rect.right

        # Vertical movement and collision detection
        original_y = self.hitbox.y
        self.hitbox.y += self.direction.y * self.speed * dt
        
        for sprite in collision_sprites:
            if hasattr(sprite, 'mask') and sprite.mask:
                if self.hitbox.colliderect(sprite.rect) and self.check_mask_collision(sprite):
                    low, high = 0.0, 1.0
                    for _ in range(8):
                        mid = (low + high) / 2
                        self.hitbox.y = original_y + self.direction.y * self.speed * dt * mid
                        
                        if self.check_mask_collision(sprite):
                            high = mid
                        else:
                            low = mid
                    
                    self.hitbox.y = original_y + self.direction.y * self.speed * dt * low
                    break
            else:
                if self.hitbox.colliderect(sprite.rect):
                    if self.direction.y > 0:
                        self.hitbox.bottom = sprite.rect.top
                    if self.direction.y < 0:
                        self.hitbox.top = sprite.rect.bottom

        self.rect.center = self.hitbox.center

    def get_status(self):
        if self.direction.magnitude() == 0:
            self.status = self.status.split('_')[0] + '_idle'

        if self.timers['tool_use'].active:
            self.status = self.status.split('_')[0] + '_' + self.selected_tool
    
    def update_timers(self):
        for timer in self.timers.values():
            timer.update()

    def update(self, dt, collision_sprites):
        self.handle_input()
        self.get_status()
        self.move_player(dt, collision_sprites)
        self.animate(dt)
        self.update_timers()
