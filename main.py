import pygame, sys
from level import Level
from settings import WIDTH, HEIGHT

pygame.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT)) # Creating screen window
pygame.display.set_caption("Laika") # Name of the window (game)
clock = pygame.time.Clock() # Clock for the game run

level = Level(screen) # Game itself

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
    dt = clock.tick()/1000

    level.run(dt) # Running game

    pygame.display.update()