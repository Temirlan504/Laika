import pygame, sys
from level import Level

pygame.init()

WIDTH, HEIGHT = 1280, 720 # Screen width and height
screen = pygame.display.set_mode((WIDTH, HEIGHT)) # Creating screen window
pygame.display.set_caption("Laika") # Name of the window (game)
clock = pygame.time.Clock() # Clock for the game run

level = Level() # game itself

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
    dt = clock.tick()/1000

    level.run(dt) # Running game

    pygame.display.update()