import pygame
import sys
from utils.button import Button

class PauseMenuState:
    def __init__(self, state_machine, game):
        self.state_machine = state_machine
        self.game = game
        self.screen = game.screen
        
        # Colors
        self.overlay_color = (0, 0, 0, 180)  # Semi-transparent black
        self.title_color = (255, 255, 255)
        self.button_normal = (209, 94, 62)  # #d15e3e (same as main menu)
        self.button_hover = (230, 120, 90)
        self.button_pressed = (180, 70, 50)
        
        # Create overlay surface
        self.create_overlay()
        
        # Load fonts
        self.load_fonts()
        
        # Create buttons
        self.create_buttons()
        
        # Confirmation dialog
        self.showing_quit_confirm = False
        self.showing_main_menu_confirm = False
        self.confirm_buttons = []
    
    def on_enter(self, **kwargs):
        """Called when entering pause menu"""
        # Block player input
        if self.game.player:
            self.game.player.block_input()
        
        # Don't hide game UI - we want to see it behind the overlay
        # But make sure inventory is closed
        if self.game.inventory_ui:
            self.game.inventory_ui.hide()
        
        # Reset confirmation dialogs
        self.showing_quit_confirm = False
        self.showing_main_menu_confirm = False
    
    def load_fonts(self):
        """Load fonts"""
        import os
        font_path = "assets/fonts/PressStart2P.ttf"
        
        if os.path.exists(font_path):
            self.title_font = pygame.font.Font(font_path, 60)
            self.button_font = pygame.font.Font(font_path, 30)
            self.small_font = pygame.font.Font(font_path, 20)
        else:
            self.title_font = pygame.font.Font(None, 80)
            self.button_font = pygame.font.Font(None, 40)
            self.small_font = pygame.font.Font(None, 28)
    
    def create_overlay(self):
        """Create semi-transparent overlay"""
        self.overlay = pygame.Surface(
            (self.screen.get_width(), self.screen.get_height())
        )
        self.overlay.fill((0, 0, 0))
        self.overlay.set_alpha(180)  # Semi-transparent
    
    def create_buttons(self):
        """Create pause menu buttons"""
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        
        button_width = 350
        button_height = 60
        button_x = (screen_width - button_width) // 2
        
        # Start buttons below the "PAUSED" title
        start_y = (screen_height // 2) - 100
        spacing = 80
        
        self.buttons = []
        
        # RESUME button
        resume_btn = Button(
            x=button_x,
            y=start_y,
            width=button_width,
            height=button_height,
            text="RESUME",
            font=self.button_font,
            normal_color=self.button_normal,
            hover_color=self.button_hover,
            pressed_color=self.button_pressed,
            callback=self.resume_game
        )
        self.buttons.append(resume_btn)
        
        # SETTINGS button
        settings_btn = Button(
            x=button_x,
            y=start_y + spacing,
            width=button_width,
            height=button_height,
            text="SETTINGS",
            font=self.button_font,
            normal_color=self.button_normal,
            hover_color=self.button_hover,
            pressed_color=self.button_pressed,
            callback=self.open_settings
        )
        self.buttons.append(settings_btn)
        
        # SAVE GAME button
        save_btn = Button(
            x=button_x,
            y=start_y + spacing * 2,
            width=button_width,
            height=button_height,
            text="SAVE GAME",
            font=self.button_font,
            normal_color=self.button_normal,
            hover_color=self.button_hover,
            pressed_color=self.button_pressed,
            callback=self.save_game
        )
        self.buttons.append(save_btn)
        
        # MAIN MENU button
        main_menu_btn = Button(
            x=button_x,
            y=start_y + spacing * 3,
            width=button_width,
            height=button_height,
            text="MAIN MENU",
            font=self.button_font,
            normal_color=self.button_normal,
            hover_color=self.button_hover,
            pressed_color=self.button_pressed,
            callback=self.show_main_menu_confirm
        )
        self.buttons.append(main_menu_btn)
        
        # QUIT button
        quit_btn = Button(
            x=button_x,
            y=start_y + spacing * 4,
            width=button_width,
            height=button_height,
            text="QUIT GAME",
            font=self.button_font,
            normal_color=self.button_normal,
            hover_color=self.button_hover,
            pressed_color=self.button_pressed,
            callback=self.show_quit_confirm
        )
        self.buttons.append(quit_btn)
    
    def create_confirmation_buttons(self, confirm_callback, cancel_callback):
        """Create YES/NO confirmation buttons"""
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        
        button_width = 180
        button_height = 60
        spacing = 40
        
        center_x = screen_width // 2
        center_y = screen_height // 2 + 50
        
        self.confirm_buttons = []
        
        # YES button
        yes_btn = Button(
            x=center_x - button_width - spacing // 2,
            y=center_y,
            width=button_width,
            height=button_height,
            text="YES",
            font=self.button_font,
            normal_color=(200, 50, 50),  # Red
            hover_color=(230, 80, 80),
            pressed_color=(170, 30, 30),
            callback=confirm_callback
        )
        self.confirm_buttons.append(yes_btn)
        
        # NO button
        no_btn = Button(
            x=center_x + spacing // 2,
            y=center_y,
            width=button_width,
            height=button_height,
            text="NO",
            font=self.button_font,
            normal_color=(100, 100, 100),  # Gray
            hover_color=(130, 130, 130),
            pressed_color=(70, 70, 70),
            callback=cancel_callback
        )
        self.confirm_buttons.append(no_btn)
    
    # Button callbacks
    def resume_game(self):
        """Resume the game"""
        print("Resuming game...")
        # Unblock player input
        if self.game.player:
            self.game.player.unblock_input()
        self.state_machine.change_state("level")
    
    def open_settings(self):
        """Open settings menu"""
        print("Opening settings... (TODO)")
        # TODO: Create settings state
        # self.state_machine.change_state("settings", return_state="pause_menu")
    
    def save_game(self):
        """Save the game"""
        print("Saving game... (TODO)")
        # TODO: Implement save system
        # For now, just show a message
        pass
    
    def show_main_menu_confirm(self):
        """Show confirmation dialog for returning to main menu"""
        self.showing_main_menu_confirm = True
        self.create_confirmation_buttons(
            confirm_callback=self.return_to_main_menu,
            cancel_callback=self.hide_confirmations
        )
    
    def show_quit_confirm(self):
        """Show confirmation dialog for quitting"""
        self.showing_quit_confirm = True
        self.create_confirmation_buttons(
            confirm_callback=self.quit_game,
            cancel_callback=self.hide_confirmations
        )
    
    def hide_confirmations(self):
        """Hide all confirmation dialogs"""
        self.showing_quit_confirm = False
        self.showing_main_menu_confirm = False
        self.confirm_buttons = []
    
    def return_to_main_menu(self):
        """Return to main menu (with save prompt?)"""
        print("Returning to main menu...")
        
        # Clear level state so it gets recreated on next new game
        if "level" in self.state_machine.state_instances:
            del self.state_machine.state_instances["level"]
        if "greenhouse" in self.state_machine.state_instances:
            del self.state_machine.state_instances["greenhouse"]
        
        # Clear player reference
        self.game.player = None
        self.game.inventory_ui = None
        
        # Clear greenhouse data
        self.game.greenhouse_data = {}
        
        self.state_machine.change_state("main_menu")
    
    def quit_game(self):
        """Quit the game"""
        print("Quitting game...")
        pygame.quit()
        sys.exit()
    
    def handle_input(self, events):
        """Handle input events"""
        for event in events:
            if event.type == pygame.KEYDOWN:
                # ESC to resume
                if event.key == pygame.K_ESCAPE:
                    if self.showing_quit_confirm or self.showing_main_menu_confirm:
                        # Cancel confirmation dialog
                        self.hide_confirmations()
                    else:
                        # Resume game
                        self.resume_game()
            
            # Handle button clicks
            if self.showing_quit_confirm or self.showing_main_menu_confirm:
                # Handle confirmation buttons
                for button in self.confirm_buttons:
                    button.handle_event(event)
            else:
                # Handle main pause menu buttons
                for button in self.buttons:
                    button.handle_event(event)
    
    def update(self, dt):
        """Update button hover states"""
        mouse_pos = pygame.mouse.get_pos()
        
        if self.showing_quit_confirm or self.showing_main_menu_confirm:
            for button in self.confirm_buttons:
                button.update(mouse_pos)
        else:
            for button in self.buttons:
                button.update(mouse_pos)
    
    def draw_title(self):
        """Draw PAUSED title"""
        title_surface = self.title_font.render("PAUSED", True, self.title_color)
        title_rect = title_surface.get_rect(
            center=(self.screen.get_width() // 2, 150)
        )
        
        # Draw shadow
        shadow_surface = self.title_font.render("PAUSED", True, (0, 0, 0))
        shadow_rect = shadow_surface.get_rect(
            center=(self.screen.get_width() // 2 + 3, 153)
        )
        
        self.screen.blit(shadow_surface, shadow_rect)
        self.screen.blit(title_surface, title_rect)
    
    def draw_confirmation_dialog(self):
        """Draw confirmation dialog box"""
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        
        # Dialog box
        dialog_width = 600
        dialog_height = 300
        dialog_x = (screen_width - dialog_width) // 2
        dialog_y = (screen_height - dialog_height) // 2
        
        # Darker overlay for dialog
        dialog_overlay = pygame.Surface((screen_width, screen_height))
        dialog_overlay.fill((0, 0, 0))
        dialog_overlay.set_alpha(100)
        self.screen.blit(dialog_overlay, (0, 0))
        
        # Dialog background
        dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
        pygame.draw.rect(self.screen, (40, 40, 50), dialog_rect)
        pygame.draw.rect(self.screen, (200, 200, 200), dialog_rect, 3)
        
        # Dialog text
        if self.showing_quit_confirm:
            text = "Quit to desktop?"
        elif self.showing_main_menu_confirm:
            text = "Return to main menu?"
        
        text_surface = self.small_font.render(text, True, self.title_color)
        text_rect = text_surface.get_rect(
            center=(screen_width // 2, screen_height // 2 - 30)
        )
        self.screen.blit(text_surface, text_rect)
        
        # Warning text
        warning = "Unsaved progress will be lost!"
        warning_surface = pygame.font.Font(None, 24).render(warning, True, (255, 100, 100))
        warning_rect = warning_surface.get_rect(
            center=(screen_width // 2, screen_height // 2 + 10)
        )
        self.screen.blit(warning_surface, warning_rect)
        
        # Draw confirmation buttons
        for button in self.confirm_buttons:
            button.draw(self.screen)
    
    # Handle window resize
    def on_resize(self, size):
        self.create_overlay()

        # Recreate buttons (re-center them)
        self.create_buttons()
    
    def run(self, dt):
        """Main loop for pause menu"""
        self.update(dt)
        
        # Note: The game state is still rendered in the background
        # We just draw the overlay and menu on top
        
        # Draw semi-transparent overlay
        self.screen.blit(self.overlay, (0, 0))
        
        # Draw title
        self.draw_title()
        
        # Draw buttons or confirmation dialog
        if self.showing_quit_confirm or self.showing_main_menu_confirm:
            self.draw_confirmation_dialog()
        else:
            # Draw main pause menu buttons
            for button in self.buttons:
                button.draw(self.screen)
            
            # Draw hint text at bottom
            hint_font = pygame.font.Font(None, 22)
            hint_text = hint_font.render("Press ESC or P to resume", True, (180, 180, 180))
            hint_rect = hint_text.get_rect(
                center=(self.screen.get_width() // 2, self.screen.get_height() - 30)
            )
            self.screen.blit(hint_text, hint_rect)
