import pygame
import sys

from utils.save_manager import SaveManager
from utils.settings import *

from states.main_menu import MainMenuState
from states.level import LevelState
from states.pause_menu import PauseMenuState
from states.greenhouse import GreenhouseState
from states.state_machine import StateMachine
from states.save_load_menu import SaveLoadMenuState
from states.ending_scene_state import EndingSceneState
from states.credits_state import CreditsState

from ui.ui_manager import UIManager
from ui.hud import DayUI, HealthBarUI, HotbarUI, HungerBarUI, OxygenBarUI
from ui.interaction_ui import InteractionPrompt
from ui.inventory_ui import InventoryUI
from player import Player

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Laika: Space Adventure")
        self.clock = pygame.time.Clock()

        # Create GLOBAL variables (but not player yet)
        self.player = None  # Will be created when starting new game
        self.all_sprites = None
        self.greenhouse_data = {}

        # Create Day Cycle System (but don't start yet)
        from systems.day_cycle import DayCycle
        self.day_cycle = DayCycle()

        # Create Clock System (but don't start yet)
        from systems.clock_system import ClockSystem
        self.clock_system = ClockSystem(self.day_cycle)
        self.clock_system.subscribe(self.day_cycle)

        # UI Manager and UI Elements
        self.ui_manager = UIManager()

        self.day_ui = DayUI(self.day_cycle, self.clock_system, self.screen)
        self.interaction_prompt = InteractionPrompt(self.screen)
        
        # Inventory UI will be created when player is created
        self.inventory_ui = None

        self.ui_manager.add(self.day_ui)
        self.ui_manager.add(self.interaction_prompt)

        # Initialize save manager FIRST (before creating states that need it)
        self.save_manager = SaveManager()

        # State Machine Setup
        self.state_machine = StateMachine(self)
        self.state_machine.add_state("main_menu", MainMenuState)
        self.state_machine.add_state("level", LevelState)
        self.state_machine.add_state("pause_menu", PauseMenuState)
        self.state_machine.add_state("greenhouse", GreenhouseState)
        self.state_machine.add_state("ending_scene", EndingSceneState)
        self.state_machine.add_state("credits", CreditsState)
        self.state_machine.add_state("save_menu", SaveLoadMenuState)
        self.state_machine.add_state("load_menu", SaveLoadMenuState)

        self.state_machine.change_state("main_menu")

    def initialize_game(self):
        """Initialize player and game systems (called when starting new game)"""
        # Create player
        self.all_sprites = pygame.sprite.Group()
        self.player = Player((SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), self.all_sprites)
        
        # Create inventory UI
        self.inventory_ui = InventoryUI(self.screen, self.player.inventory, self.player.hotbar)
        self.ui_manager.add(self.inventory_ui)

        # Create HUD UI elements
        self.hotbar_ui = HotbarUI(self.screen, self.player.hotbar)
        self.ui_manager.add(self.hotbar_ui)

        self.health_bar_ui = HealthBarUI(self.player, self.screen)
        self.ui_manager.add(self.health_bar_ui)

        self.oxygen_bar_ui = OxygenBarUI(self.player, self.screen)
        self.ui_manager.add(self.oxygen_bar_ui)

        self.hunger_bar_ui = HungerBarUI(self.player, self.screen)
        self.ui_manager.add(self.hunger_bar_ui)
        
        # Subscribe current state to day cycle if needed
        if hasattr(self.state_machine.current_state, "on_new_day"):
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
                
                # Handle window resize
                if event.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
                    
                    # Update screen references in UI elements
                    self.day_ui.screen = self.screen
                    self.interaction_prompt.screen = self.screen
                    if self.inventory_ui:
                        self.inventory_ui.screen = self.screen
                    
                    if hasattr(self.state_machine.current_state, "on_resize"):
                        self.state_machine.current_state.on_resize(event.size)

            # Only update clock system if player exists (in-game) and not in main menu or pause menu
            if (self.player is not None and 
                self.state_machine.current_state != self.state_machine.state_instances.get("main_menu") and
                self.state_machine.current_state != self.state_machine.state_instances.get("pause_menu")):
                self.clock_system.update(dt)
            
            # Current state logic (inventory toggle is now handled in states)
            self.state_machine.current_state.handle_input(events)
            self.state_machine.run(dt)

            # Draw UI elements (but only if they exist)
            self.ui_manager.draw()

            pygame.display.update()

if __name__ == "__main__":
    game = Game()
    game.run()
