import pygame
import sys
from utils.settings import *
from states.level import LevelState

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Laika: Space Adventure")
        self.clock = pygame.time.Clock()

        # Start in the Level state
        self.current_state = LevelState(self)

    def goto_state(self, new_state):
        self.current_state = new_state

    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000

            # Handle quitting in a unified way
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            # Run current state
            self.current_state.run(dt)
            pygame.display.update()

if __name__ == "__main__":
    game = Game()
    game.run()
