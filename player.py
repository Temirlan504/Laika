import pygame
from utils.settings import *
from utils.support import import_folder

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

        # Movement attributes
        self.velocity = pygame.math.Vector2(0, 0)
        self.speed = 200

    def import_assets(self):
        self.animations = {
            'up_idle': [],
            'down_idle': [],
            'left_idle': [],
            'right_idle': [],
        }

        for animation in self.animations.keys():
            full_path = 'assets/player/' + animation
            self.animations[animation] = import_folder(full_path)

    def handle_input(self):
        keys = pygame.key.get_pressed()
        self.velocity.x = 0
        self.velocity.y = 0
        if keys[pygame.K_a]:
            self.velocity.x = -self.speed
        if keys[pygame.K_d]:
            self.velocity.x = self.speed
        if keys[pygame.K_w]:
            self.velocity.y = -self.speed
        if keys[pygame.K_s]:
            self.velocity.y = self.speed

    def move_player(self, dx, dy):
        if self.velocity.magnitude() > 0:
            self.velocity = self.velocity.normalize()
        self.rect.x += dx # New position = old position + delta_x
        self.rect.y += dy # New position = old position + delta_y

    def update(self, dt):
        self.handle_input()
        self.move_player(self.velocity.x * dt, self.velocity.y * dt)
