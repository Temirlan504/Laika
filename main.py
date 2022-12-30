import pygame, sys

pygame.init()

WIDTH, HEIGHT = 1280, 720
display = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Laika")
clock = pygame.time.Clock()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    dt = clock.tick()/1000
    pygame.display.update()