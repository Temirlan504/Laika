import pygame
import sys
from utils.settings import *
from states.level import LevelState
from states.pause_menu import PauseMenuState
from states.greenhouse import GreenhouseState
from states.state_machine import StateMachine
from ui.ui_manager import UIManager
from ui.hud import DayUI
from ui.interaction_ui import InteractionPrompt
from player import Player

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Laika: Space Adventure")
        self.clock = pygame.time.Clock()

        # --- Create GLOBAL player object ---
        self.all_sprites = pygame.sprite.Group()
        self.player = Player((SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), self.all_sprites)

        # --- Create GLOBAL variables ---
        self.greenhouse_data = {}

        # --- Create Day Cycle System ---
        from systems.day_cycle import DayCycle
        self.day_cycle = DayCycle()

        # --- Create Clock System ---
        from systems.clock_system import ClockSystem
        self.clock_system = ClockSystem(self.day_cycle)
        self.clock_system.subscribe(self.day_cycle)

        # --- UI Manager and UI Elements ---
        self.ui_manager = UIManager()

        self.day_ui = DayUI(self.day_cycle, self.clock_system, self.screen)
        self.interaction_prompt = InteractionPrompt(self.screen)

        self.ui_manager.add(self.day_ui)
        self.ui_manager.add(self.interaction_prompt)

        # --- State Machine Setup ---
        self.state_machine = StateMachine(self)
        self.state_machine.add_state("level", LevelState)
        self.state_machine.add_state("pause_menu", PauseMenuState)
        self.state_machine.add_state("greenhouse", GreenhouseState)
        self.state_machine.change_state("level") # Start with level state

        self.day_cycle.subscribe(self.state_machine.current_state)

    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000

            # Handle quitting the game
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            # Update clock system
            self.clock_system.update(dt)
            
            # Current state logic
            self.state_machine.current_state.handle_input(events)
            self.state_machine.run(dt)

            # Draw UI elements
            self.ui_manager.draw()

            pygame.display.update()

if __name__ == "__main__":
    game = Game()
    game.run()
