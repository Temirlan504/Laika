import pygame
from utils.settings import *

class GreenhouseState:
    def __init__(self, state_machine, game):
        self.state_machine = state_machine
        self.game = game
        self.screen = game.screen
        
        # Dictionary to store crops for each greenhouse
        # Key: greenhouse_id, Value: list of crops
        self.greenhouses = {}
        
        # Currently active greenhouse
        self.current_greenhouse_id = None
    
    def on_enter(self, greenhouse_id=None, **kwargs):
        """Called when entering this state"""
        self.current_greenhouse_id = greenhouse_id
        
        # Create greenhouse data if it doesn't exist
        if greenhouse_id not in self.greenhouses:
            self.greenhouses[greenhouse_id] = {
                'crops': [],
                'name': f'Greenhouse {greenhouse_id}'
            }

        # Hide interaction prompt when entering greenhouse
        self.game.interaction_prompt.hide()
        
        print(f"Entered {self.greenhouses[greenhouse_id]['name']}")
    
    def on_new_day(self, sol):
        """Called when a new day starts - grow ALL crops in ALL greenhouses"""
        print(f"GreenhouseState: New day {sol}, growing crops in all greenhouses...")
        for gh_id, gh_data in self.greenhouses.items():
            for crop in gh_data['crops']:
                crop.grow()
    
    def handle_input(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # Exit greenhouse, return to level
                    self.state_machine.change_state("level")
    
    def run(self, dt):
        self.screen.fill((50, 100, 50))  # Green background
        
        # Draw greenhouse info
        font = pygame.font.Font(None, 36)
        if self.current_greenhouse_id:
            gh_data = self.greenhouses[self.current_greenhouse_id]
            text = font.render(f"{gh_data['name']} - Press ESC to exit", True, (255, 255, 255))
            crop_text = font.render(f"Crops: {len(gh_data['crops'])}", True, (255, 255, 255))
        else:
            text = font.render("No greenhouse selected", True, (255, 255, 255))
            crop_text = None
        
        self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT // 2))
        if crop_text:
            self.screen.blit(crop_text, (SCREEN_WIDTH // 2 - crop_text.get_width() // 2, SCREEN_HEIGHT // 2 + 50))