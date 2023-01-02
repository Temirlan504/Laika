import pygame

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, group):
        super().__init__(group)
        self.image = pygame.Surface((32,32))
        self.image.fill("white")
        self.rect = self.image.get_rect(center=pos)

        # Movement attributes
        self.direction = pygame.math.Vector2() # Will determine the direction of the player's movement in "x" and "y"
        self.pos = pygame.math.Vector2(self.rect.center) # store position as float
        self.speed = 200

    # Check if any key is pressed
    def get_input(self):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_w]:
            self.direction.y = -1 # Direction is up
        elif keys[pygame.K_s]:
            self.direction.y = 1 # Direction is down
        else:
            self.direction.y = 0

        if keys[pygame.K_a]:
            self.direction.x = -1 # Direction is left
        elif keys[pygame.K_d]:
            self.direction.x = 1 # Direction is right
        else:
            self.direction.x = 0

    def move_player(self, dt):
        if self.direction.magnitude() > 0: # Handling zero magnitude error
            self.direction = self.direction.normalize() # Make sure that the vector is same in diagonal movement (.noramlize() is pygame's function)

        # Horizontal movement
        self.pos.x += self.direction.x * self.speed * dt
        self.rect.centerx = self.pos.x

        # Vertical movement
        self.pos.y += self.direction.y * self.speed * dt
        self.rect.centery = self.pos.y

    def update(self, dt):
        self.get_input()
        self.move_player(dt)