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

        # Player placeholder
        self.image = self.animations[self.status][self.frame_index]
        self.image = pygame.transform.scale(self.image, (TILE_SIZE, TILE_SIZE))
        self.rect = self.image.get_rect(center=pos) # Postion player's sprite
        self.hitbox = self.rect.inflate((-25, -20))  # Adjust hitbox size
        self.z_index = LAYERS['player']  # Ensure player is above ground and cliffs

        # Movement attributes
        self.direction = pygame.math.Vector2(0, 0)
        self.speed = 150

        # Timers
        self.timers = {
            'tool_use': Timer(350, self.use_tool)
        }

        # Tools attributes
        self.tools = ['hoe', 'pickaxe']
        self.selected_tool = 'pickaxe'

    # --- Tool use action ---
    def use_tool(self):
        pass  # Placeholder for tool use logic

    # --- Importing assets into a dictionary and animating player ---
    def import_assets(self):
        self.animations = {
            'up_idle': [], 'down_idle': [], 'left_idle': [], 'right_idle': [],
            'up': [], 'down': [], 'left': [], 'right': [],
            'up_hoe': [], 'down_hoe': [], 'left_hoe': [], 'right_hoe': [],
            'up_pickaxe': [], 'down_pickaxe': [], 'left_pickaxe': [], 'right_pickaxe': [],
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

    # --- Move player and handle collisions ---
    def move_player(self, dt, collision_sprites):
        if self.direction.magnitude() > 0:
            self.direction = self.direction.normalize()

        # Horizontal movement and collision detection
        self.hitbox.x += self.direction.x * self.speed * dt
        for sprite in collision_sprites:
            if self.hitbox.colliderect(sprite.rect):
                if self.direction.x > 0:  # Moving right
                    self.hitbox.right = sprite.rect.left
                if self.direction.x < 0:  # Moving left
                    self.hitbox.left = sprite.rect.right

        # Vertical movement and collision detection
        self.hitbox.y += self.direction.y * self.speed * dt
        for sprite in collision_sprites:
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
