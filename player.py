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

        self._load_sounds()
        self._footstep_index = 0
        self._mining_index = 0

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

        # Timers - separate for LMB and RMB actions
        self.timers = {
            'tool_use_lmb': Timer(300, self.use_tool_lmb),  # For mining (pickaxe)
            'tool_use_rmb': Timer(300, self.use_tool_rmb),  # For farming/eating
            'harvest': Timer(200)
        }

        # Tools attributes
        self.tools = ['hoe', 'pickaxe', 'watering_can', 'seed']
        self.selected_tool = 'pickaxe'
        self.selected_seed = 'potato_seed'  # Track which seed to plant
        self.tool_ray_length = 32
    
    def _load_sounds(self):
        self.sounds = {}
        for i in range(1, 4):
            try:
                sound = pygame.mixer.Sound(f"assets/sounds/footstep_{i}.ogg")
                sound.set_volume(0.4)
                self.sounds[f'footstep_{i}'] = sound
            except Exception as e:
                print(f"[SOUND] Could not load footstep_{i}: {e}")

        for i in range(1, 2):
            try:
                sound = pygame.mixer.Sound(f"assets/sounds/mining_{i}.ogg")
                sound.set_volume(0.4)
                self.sounds[f'mining_{i}'] = sound
            except Exception as e:
                print(f"[SOUND] Could not load mining_{i}: {e}")

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
    
    def consume_events(self):
        events = self.events.copy()
        self.events.clear()
        return events

    def use_tool_lmb(self):
        """Use tool with LMB (mining with pickaxe)"""
        target_pos = self.get_target_pos()
        
        # Get the item from the selected hotbar slot
        item_id = self.hotbar.get_selected_item_id()
        
        if not item_id:
            return
        
        # Get item definition to check its type
        item = get_item(item_id)
        if not item:
            return
        
        # LMB: Only pickaxe
        if item.type == ItemType.TOOL and item_id == 'pickaxe':
            self.events.append(('pickaxe', target_pos))

    def use_tool_rmb(self):
        """Use tool with RMB (farming tools, seeds, food)"""
        target_pos = self.get_target_pos()
        
        # Get the item from the selected hotbar slot
        item_id = self.hotbar.get_selected_item_id()
        
        if not item_id:
            return
        
        # Get item definition to check its type
        item = get_item(item_id)
        if not item:
            return
        
        # RMB: Farming tools (hoe, watering can), seeds, and food
        if item.type == ItemType.TOOL:
            if item_id == 'hoe':
                self.events.append(('hoe', target_pos))
            elif item_id == 'watering_can':
                self.events.append(('water', target_pos))
        
        elif item.type == ItemType.SEED:
            self.events.append(('plant', target_pos, item_id))
        
        elif item.type == ItemType.FOOD:
            self.eat_food(item_id)

    def eat_food(self, item_id):
        """Eat food from hotbar"""
        # Check if hunger is already full
        if self.current_hunger >= 97:
            print(f"[PLAYER] You're not hungry!")
            return False
        
        item_def = get_item(item_id)
        if not item_def:
            return False
        
        # Try to remove from hotbar first
        if self.hotbar.remove_item(item_id, 1):
            # Restore hunger and health
            if hasattr(item_def, 'hunger_restore'):
                self.restore_hunger(item_def.hunger_restore)
            if hasattr(item_def, 'health_restore'):
                self.heal(item_def.health_restore)
            print(f"[PLAYER] Ate {item_def.name} (+{item_def.hunger_restore} hunger)")
            return True
        
        return False

    def handle_input(self):
        if self.input_blocked:
            return
        
        keys = pygame.key.get_pressed()
        mouse_buttons = pygame.mouse.get_pressed()

        # Check if any tool timer is active
        any_timer_active = (self.timers['tool_use_lmb'].active or 
                           self.timers['tool_use_rmb'].active)

        if not any_timer_active:
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

            # LMB: Mining (pickaxe only)
            if mouse_buttons[0]:  # Left mouse button
                item_id = self.hotbar.get_selected_item_id()
                if item_id:
                    item = get_item(item_id)
                    if item and item.type == ItemType.TOOL and item_id == 'pickaxe':
                        self.timers['tool_use_lmb'].activate()
                        self.frame_index = 0
                        self.direction = pygame.math.Vector2(0, 0)
            
            # RMB: Farming tools, seeds, food
            if mouse_buttons[2]:  # Right mouse button
                item_id = self.hotbar.get_selected_item_id()
                if item_id:
                    item = get_item(item_id)
                    if item:
                        # Check if it's a farming tool, seed, or food
                        is_farming_tool = (item.type == ItemType.TOOL and 
                                         item_id in ['hoe', 'watering_can'])
                        is_usable = (is_farming_tool or 
                                   item.type == ItemType.SEED or 
                                   item.type == ItemType.FOOD)
                        
                        if is_usable:
                            self.timers['tool_use_rmb'].activate()
                            self.frame_index = 0
                            self.direction = pygame.math.Vector2(0, 0)
            
            # Harvest (interaction key) - E key
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
        prev_frame = int(self.frame_index)
        self.frame_index += self.animation_speed * dt
        if self.frame_index >= len(self.animations[self.status]):
            self.frame_index = 0
        self.image = self.animations[self.status][int(self.frame_index)]

        # Play footstep when a new frame is hit during walking (not idle, not tool use)
        variants = [s for k, s in self.sounds.items() if k.startswith('footstep') and s is not None]
        is_walking = (
            self.direction.magnitude() > 0
            and '_idle' not in self.status
            and not self.timers['tool_use_lmb'].active
            and not self.timers['tool_use_rmb'].active
        )
        current_frame = int(self.frame_index)

        if is_walking and current_frame != prev_frame and current_frame % 2 == 0:
            if variants:
                variants[self._footstep_index % len(variants)].play()
                self._footstep_index += 1

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

        # Update animation based on active timer
        if self.timers['tool_use_lmb'].active or self.timers['tool_use_rmb'].active:
            item_id = self.hotbar.get_selected_item_id()
            if item_id:
                item = get_item(item_id)
                if item and item.type == ItemType.TOOL:
                    self.status = self.status.split('_')[0] + '_' + item_id
                elif item and item.type == ItemType.SEED:
                    self.status = self.status.split('_')[0] + '_seed'
    
    def update_timers(self):
        for timer in self.timers.values():
            timer.update()

    def update(self, dt, collision_sprites):
        self.handle_input()
        self.get_status()
        self.move_player(dt, collision_sprites)
        self.animate(dt)
        self.update_timers()
