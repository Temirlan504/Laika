import pygame
from utils.settings import *
from utils.support import import_folder
from utils.timer import Timer

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
        self.rect = self.image.get_rect(center=pos) # Postion player's sprite
        self.hitbox = self.rect.inflate((-25, -20))  # Adjust hitbox size
        self.z_index = LAYERS['player']  # Ensure player is above ground and cliffs

        self.inventory = {}

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
        self.tool_ray_length = 32  # pixels

    def take_damage(self, amount):
        self.health = max(0, self.health - amount)
        if self.health == 0:
            self.is_alive = False

    def heal(self, amount):
        self.health = min(self.max_health, self.health + amount)

    def add_item(self, item_name, amount=1):
        if item_name not in self.inventory:
            self.inventory[item_name] = 0
        self.inventory[item_name] += amount
        print(f"Added {amount}x {item_name} (Total: {self.inventory[item_name]})")

    def consume_events(self):
        events = self.events.copy()
        self.events.clear()
        return events

    def use_tool(self):
        target_pos = self.get_target_pos()

        if self.selected_tool == 'hoe':
            self.events.append(('hoe', target_pos))
        elif self.selected_tool == 'watering_can':
            self.events.append(('water', target_pos))
        elif self.selected_tool == 'seed':
            self.events.append(('plant', target_pos))
        elif self.selected_tool == 'pickaxe':
            self.events.append(('pickaxe', target_pos))

    # --- Tool use action ---
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

        # Default to under player if idle
        if direction.length() == 0:
            return self.hitbox.center

        return self.hitbox.center + direction * self.tool_ray_length

    # --- Importing assets into a dictionary and animating player ---
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

    # --- Player's direction vectors and movement ---
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

            # Tool use
            if keys[pygame.K_SPACE]:
                # Timer for tool use
                self.timers['tool_use'].activate()
                self.frame_index = 0
                # Stop movement when using tool
                self.direction = pygame.math.Vector2(0, 0)
            
            # Select tool (example with number keys)
            if keys[pygame.K_1]:
                self.selected_tool = 'hoe'
            if keys[pygame.K_2]:
                self.selected_tool = 'pickaxe'
            if keys[pygame.K_3]:
                self.selected_tool = 'watering_can'
            if keys[pygame.K_4]:
                self.selected_tool = 'seed'

            # Harvest (interaction key)
            if keys[pygame.K_e] and not self.timers['harvest'].active:
                self.timers['harvest'].activate()
                target_pos = self.get_target_pos()
                self.events.append(('harvest', target_pos))

    # --- Block and unblock player input ---
    def block_input(self):
        self.input_blocked = True
        self.direction = pygame.math.Vector2(0, 0)

    def unblock_input(self):
        self.input_blocked = False

    # --- Helper function to check mask collision ---
    def check_mask_collision(self, sprite):
        """Check if player's hitbox collides with sprite's mask"""
        if not hasattr(sprite, 'mask') or not sprite.mask:
            return False
        
        offset_x = sprite.rect.left - self.hitbox.left
        offset_y = sprite.rect.top - self.hitbox.top
        
        player_mask = pygame.mask.Mask(self.hitbox.size)
        player_mask.fill()
        
        return player_mask.overlap(sprite.mask, (offset_x, offset_y)) is not None

    # --- Move player and handle collisions ---
    def move_player(self, dt, collision_sprites):
        if self.direction.magnitude() > 0:
            self.direction = self.direction.normalize()

        # Horizontal movement and collision detection
        original_x = self.hitbox.x
        self.hitbox.x += self.direction.x * self.speed * dt
        
        for sprite in collision_sprites:
            if hasattr(sprite, 'mask') and sprite.mask:
                # Mask-based collision
                if self.hitbox.colliderect(sprite.rect) and self.check_mask_collision(sprite):
                    # Binary search to find exact collision point
                    low, high = 0.0, 1.0
                    for _ in range(8):  # 8 iterations for precision
                        mid = (low + high) / 2
                        self.hitbox.x = original_x + self.direction.x * self.speed * dt * mid
                        
                        if self.check_mask_collision(sprite):
                            high = mid
                        else:
                            low = mid
                    
                    # Place player just before collision
                    self.hitbox.x = original_x + self.direction.x * self.speed * dt * low
                    break
            else:
                # Rectangle collision for objects without masks
                if self.hitbox.colliderect(sprite.rect):
                    if self.direction.x > 0:  # Moving right
                        self.hitbox.right = sprite.rect.left
                    if self.direction.x < 0:  # Moving left
                        self.hitbox.left = sprite.rect.right

        # Vertical movement and collision detection
        original_y = self.hitbox.y
        self.hitbox.y += self.direction.y * self.speed * dt
        
        for sprite in collision_sprites:
            if hasattr(sprite, 'mask') and sprite.mask:
                # Mask-based collision
                if self.hitbox.colliderect(sprite.rect) and self.check_mask_collision(sprite):
                    # Binary search to find exact collision point
                    low, high = 0.0, 1.0
                    for _ in range(8):  # 8 iterations for precision
                        mid = (low + high) / 2
                        self.hitbox.y = original_y + self.direction.y * self.speed * dt * mid
                        
                        if self.check_mask_collision(sprite):
                            high = mid
                        else:
                            low = mid
                    
                    # Place player just before collision
                    self.hitbox.y = original_y + self.direction.y * self.speed * dt * low
                    break
            else:
                # Rectangle collision for objects without masks
                if self.hitbox.colliderect(sprite.rect):
                    if self.direction.y > 0:  # Moving down
                        self.hitbox.bottom = sprite.rect.top
                    if self.direction.y < 0:  # Moving up
                        self.hitbox.top = sprite.rect.bottom

        self.rect.center = self.hitbox.center

    # --- Player status management (idle, walking, mining, etc.) ---
    def get_status(self):
        # Set idle status if no movement
        if self.direction.magnitude() == 0:
            self.status = self.status.split('_')[0] + '_idle'

        if self.timers['tool_use'].active:
            self.status = self.status.split('_')[0] + '_' + self.selected_tool  # Example: using hoe tool
    
    def update_timers(self):
        for timer in self.timers.values():
            timer.update()

    # --- Update player states ---
    def update(self, dt, collision_sprites):
        self.handle_input()
        self.get_status()
        self.move_player(dt, collision_sprites)
        self.animate(dt)
        self.update_timers()
