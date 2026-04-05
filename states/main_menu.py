import pygame
import sys
from utils.button import Button, clamp
from utils.support import resource_path

class MainMenuState:
    def __init__(self, state_machine, game):
        self.state_machine = state_machine
        self.game = game
        self.screen = game.screen

        self.load_fonts()
        self.load_sounds()
        self.load_background()
        
        # Create buttons only
        self.create_buttons()
    
    
    def load_fonts(self):
        font_path = resource_path("assets/fonts/PressStart2P.ttf")
        try:
            self.button_font = pygame.font.Font(font_path, 35)
        except FileNotFoundError:
            print("Warning: PressStart2P.ttf not found, using default font")
            self.button_font = pygame.font.Font(None, 45)

    def load_sounds(self):
        self.sounds = {}
        for name, path in [('hover', 'assets/sounds/button_hover.ogg'),
                            ('click', 'assets/sounds/button_click.ogg')]:
            try:
                sound = pygame.mixer.Sound(resource_path(path))
                sound.set_volume(0.5)
                self.sounds[name] = sound
            except Exception as e:
                print(f"[SOUND] Could not load {name}: {e}")
                self.sounds[name] = None

    def load_background(self):
        try:
            self.background_original = pygame.image.load(resource_path("assets/main_menu_bg.png")).convert()
        except FileNotFoundError:
            self.background_original = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
            self.background_original.fill((40, 40, 40))

        self.background = pygame.transform.scale(
            self.background_original,
            (self.screen.get_width(), self.screen.get_height())
        )
    
    def on_enter(self, **kwargs):
        """Called when entering main menu state"""
        # Hide game UI elements
        self.game.day_ui.visible = False
        self.game.interaction_prompt.visible = False
        if self.game.inventory_ui:
            self.game.inventory_ui.visible = False
        if hasattr(self.game, 'hotbar_ui') and self.game.hotbar_ui:
            self.game.hotbar_ui.hide()
        if hasattr(self.game, 'health_bar_ui') and self.game.health_bar_ui:
            self.game.health_bar_ui.hide()
        if hasattr(self.game, 'oxygen_bar_ui') and self.game.oxygen_bar_ui:
            self.game.oxygen_bar_ui.hide()
        if hasattr(self.game, 'hunger_bar_ui') and self.game.hunger_bar_ui:
            self.game.hunger_bar_ui.hide()
        
        # Recreate buttons to update continue button state
        self.create_buttons()

        # Resize background to fit current screen size
        self.background = pygame.transform.scale(
            self.background_original,
            (self.screen.get_width(), self.screen.get_height())
        )

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

        continue_btn = add_button("LOAD GAME", 1, self.continue_game)
        has_save = self.has_save_file()
        print(f"[MAIN_MENU] Has save file: {has_save}")
        if not has_save:
            continue_btn.normal_color = (100, 100, 100)
            continue_btn.hover_color = (100, 100, 100)
            continue_btn.callback = None
            print("[MAIN_MENU] Continue button disabled (no save)")
        else:
            print("[MAIN_MENU] Continue button enabled")
        self.buttons.append(continue_btn)

        settings_btn = add_button("SETTINGS", 2, self.open_settings)
        settings_btn.normal_color = (100, 100, 100)
        settings_btn.hover_color = (100, 100, 100)
        settings_btn.callback = None
        self.buttons.append(settings_btn)

        quit_btn = add_button("QUIT", 3, self.quit_game)
        self.buttons.append(quit_btn)
    
    def has_save_file(self):
        """Check if any save file exists (auto-save or manual saves)"""
        # Check auto-save first
        if self.game.save_manager.has_auto_save():
            return True
        
        # Check manual save slots (1-3)
        slots = self.game.save_manager.get_save_slots()
        for slot in slots:
            if slot['exists']:
                return True
        
        return False
    
    # Button callbacks
    def new_game(self):
        """Start a new game"""
        print("Starting new game...")

        # Clear stale level/greenhouse state so they're recreated fresh
        if "level" in self.state_machine.state_instances:
            del self.state_machine.state_instances["level"]
        if "greenhouse" in self.state_machine.state_instances:
            del self.state_machine.state_instances["greenhouse"]
        
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
        """Open load menu to choose which save to continue from"""
        print("Opening load menu...")
        self.state_machine.change_state("load_menu", mode='load')

    def load_game(self):
        """Open load menu"""
        self.state_machine.change_state("load_menu", mode='load')
    
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
        for event in events:
            if event.type == pygame.MOUSEMOTION:
                for button in self.buttons:
                    was_hovered = button.hovered
                    button.hovered = button.rect.collidepoint(event.pos)
                    if button.hovered and not was_hovered:
                        if self.sounds.get('hover'):
                            self.sounds['hover'].play()

            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                for button in self.buttons:
                    if button.pressed and button.hovered and button.callback:
                        if self.sounds.get('click'):
                            self.sounds['click'].play()

            for button in self.buttons:
                button.handle_event(event)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if self.sounds.get('click'):
                        self.sounds['click'].play()
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
