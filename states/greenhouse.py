import pygame
from utils.settings import *

class GreenhouseState:
    def __init__(self, state_machine, game):
        self.state_machine = state_machine
        self.game = game
        self.screen = game.screen
        
        self.crops = []  # Will hold crop objects later
    
    def on_new_day(self, sol):
        """Called when a new day starts - grow crops!"""
        print(f"GreenhouseState: New day {sol}, growing crops...")
        for crop in self.crops:
            crop.grow()
    
    def handle_input(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # Exit greenhouse, return to level
                    self.state_machine.change_state("level")
    
    def run(self, dt):
        self.screen.fill((50, 100, 50))  # Green background for now
        
        # Draw temporary text
        font = pygame.font.Font(None, 36)
        text = font.render("GREENHOUSE - Press ESC to exit", True, (255, 255, 255))
        self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT // 2))
