import pygame
import sys
import os
from utils.button import Button, clamp

class MainMenuState:
    def __init__(self, state_machine, game):
        self.state_machine = state_machine
        self.game = game
        self.screen = game.screen
        
        # Load fonts
        self.load_fonts()
        
        # Load background (contains title and subtitle from Canva)
        self.load_background()
        
        # Create buttons only
        self.create_buttons()
    
    def on_enter(self, **kwargs):
        """Called when entering main menu state"""
        # Hide game UI elements
        self.game.day_ui.visible = False
        self.game.interaction_prompt.visible = False
        if self.game.inventory_ui:
            self.game.inventory_ui.visible = False
    
    def load_fonts(self):
        """Load Press Start 2P font or fallback"""
        font_path = "assets/fonts/PressStart2P.ttf"
        
        # Try to load custom font
        if os.path.exists(font_path):
            self.button_font = pygame.font.Font(font_path, 35)
        else:
            # Fallback to system font
            print("Warning: PressStart2P.ttf not found, using default font")
            self.button_font = pygame.font.Font(None, 45)
    
    def load_background(self):
        bg_path = "assets/main_menu_bg.png"

        if os.path.exists(bg_path):
            self.background_original = pygame.image.load(bg_path).convert()
            self.background = pygame.transform.scale(
                self.background_original,
                (self.screen.get_width(), self.screen.get_height())
            )
        else:
            self.background_original = pygame.Surface(
                (self.screen.get_width(), self.screen.get_height())
            )
            self.background_original.fill((40, 40, 40))
            self.background = self.background_original.copy()

    def create_buttons(self):
        """Create menu buttons"""
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()

        button_width = 350
        button_height = 70

        button_x = (screen_width - button_width) // 2
        start_y = int(screen_height * 0.45)
        spacing = clamp(int(screen_height * 0.1), 80, 110)

        self.buttons = []

        def add_button(text, index, callback):
            return Button(
                x=button_x,
                y=start_y + spacing * index,
                width=button_width,
                height=button_height,
                text=text,
                font=self.button_font,
                callback=callback
            )

        new_game_btn = add_button("NEW GAME", 0, self.new_game)
        self.buttons.append(new_game_btn)

        continue_btn = add_button("CONTINUE", 1, self.continue_game)
        if not self.has_save_file():
            continue_btn.normal_color = (100, 100, 100)
            continue_btn.hover_color = (100, 100, 100)
            continue_btn.callback = None
        self.buttons.append(continue_btn)

        settings_btn = add_button("SETTINGS", 2, self.open_settings)
        self.buttons.append(settings_btn)

        quit_btn = add_button("QUIT", 3, self.quit_game)
        self.buttons.append(quit_btn)
    
    def has_save_file(self):
        """Check if save file exists"""
        return os.path.exists("save_data.json")
    
    # Button callbacks
    def new_game(self):
        """Start a new game"""
        print("Starting new game...")
        
        # Initialize player and game systems
        self.game.initialize_game()
        
        # Reset game state
        self.game.day_cycle.day = 0
        self.game.clock_system.set_time(6, 0)
        self.game.player.current_health = self.game.player.max_health
        self.game.player.current_hunger = self.game.player.max_hunger
        self.game.player.current_oxygen = self.game.player.max_oxygen
        
        # Change to game state
        self.state_machine.change_state("level")
    
    def continue_game(self):
        """Load and continue saved game"""
        if self.has_save_file():
            print("Loading saved game...")
            # TODO: Load save data
            self.state_machine.change_state("level")
    
    def open_settings(self):
        """Open settings menu"""
        print("Opening settings...")
        # TODO: Create settings state
        # self.state_machine.change_state("settings")
    
    def quit_game(self):
        """Quit the game"""
        print("Quitting game...")
        pygame.quit()
        sys.exit()
    
    def handle_input(self, events):
        """Handle input events"""
        for event in events:
            # Handle button events
            for button in self.buttons:
                button.handle_event(event)
            
            # Quick start with ENTER
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.new_game()
    
    # Handle window resize
    def on_resize(self, size):
        width, height = size

        # Rescale background
        self.background = pygame.transform.scale(
            self.background_original,
            (width, height)
        )

        # Recreate buttons (re-center them)
        self.create_buttons()
    
    def update(self, dt):
        """Update button hover states"""
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            button.update(mouse_pos)
    
    def run(self, dt):
        """Main loop for main menu"""
        self.update(dt)
        
        # Draw background (includes title and subtitle from Canva)
        self.screen.blit(self.background, (0, 0))
        
        # Draw buttons
        for button in self.buttons:
            button.draw(self.screen)
        
        # Optional: Draw version at bottom
        small_font = pygame.font.Font(None, 20)
        version_text = small_font.render("v1.0.0", True, (150, 150, 150))
        version_rect = version_text.get_rect(bottomleft=(10, self.screen.get_height() - 10))
        self.screen.blit(version_text, version_rect)
