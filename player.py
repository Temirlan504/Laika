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
        self.z_index = LAYERS['player']  # Ensure player is above ground and cliffs

        # Movement attributes
        self.velocity = pygame.math.Vector2(0, 0)
        self.speed = 100

        # Timers
        self.timers = {
            'tool_use': Timer(350, self.use_tool)
        }

        # Tools attributes
        self.tools = ['hoe', 'pickaxe']
        self.selected_tool = 'pickaxe'

    # --- Tool use action ---
    def use_tool(self):
        print(f"Using {self.selected_tool}!")

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
            self.velocity.x = 0
            self.velocity.y = 0
            if keys[pygame.K_a]:
                self.velocity.x = -self.speed
                self.status = 'left'
            if keys[pygame.K_d]:
                self.velocity.x = self.speed
                self.status = 'right'
            if keys[pygame.K_w]:
                self.velocity.y = -self.speed
                self.status = 'up'
            if keys[pygame.K_s]:
                self.velocity.y = self.speed
                self.status = 'down'

            # Tool use
            if keys[pygame.K_SPACE]:
                # Timer for tool use
                self.timers['tool_use'].activate()
                self.frame_index = 0
                # Stop movement when using tool
                self.velocity = pygame.math.Vector2(0, 0)
            
            # Select tool (example with number keys)
            if keys[pygame.K_1]:
                self.selected_tool = 'hoe'
            if keys[pygame.K_2]:
                self.selected_tool = 'pickaxe'

    def move_player(self, dx, dy):
        if self.velocity.magnitude() > 0:
            self.velocity = self.velocity.normalize()
        self.rect.x += dx # New position_x = old position_x + delta_x
        self.rect.y += dy # New position_y = old position_y + delta_y

    # --- Player status management (idle, walking, mining, etc.) ---
    def get_status(self):
        # Set idle status if no movement
        if self.velocity.magnitude() == 0:
            self.status = self.status.split('_')[0] + '_idle'

        if self.timers['tool_use'].active:
            self.status = self.status.split('_')[0] + '_' + self.selected_tool  # Example: using hoe tool
    
    def update_timers(self):
        for timer in self.timers.values():
            timer.update()

    # --- Update player states ---
    def update(self, dt):
        self.handle_input()
        self.get_status()
        self.move_player(self.velocity.x * dt, self.velocity.y * dt)
        self.animate(dt)
        self.update_timers()
