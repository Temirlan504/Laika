import pygame
import sys

class CreditsState:
    """
    Credits screen showing THE END and scrolling credits.
    Appears after the ending scene cutscene.
    """
    
    def __init__(self, state_machine, game):
        self.state_machine = state_machine
        self.game = game
        self.screen = game.screen
        
        # Fonts
        self.title_font = pygame.font.Font(None, 120)
        self.header_font = pygame.font.Font(None, 64)
        self.credit_font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 32)
        
        # Colors
        self.bg_color = (10, 10, 15)
        self.text_color = (255, 255, 255)
        self.dim_text_color = (150, 150, 150)
        
        # Credits data (customize this with your actual credits!)
        self.credits_data = [
            "",
            "",
            "",
            ("THE END", "title"),
            "",
            "",
            "",
            ("A game by", "header"),
            ("Temirlan Yergazy (Obelus)", "credit"),
            "",
            "",
            ("Built with", "header"),
            ("Python & Pygame", "credit"),
            "",
            "",
            ("Thank you for playing!", "header"),
            "",
            "",
            "",
            ("Press ESC to return to main menu", "small"),
            "",
            "",
            "",
        ]
        
        # Scrolling
        self.scroll_y = 0
        self.scroll_speed = 50  # pixels per second
        
        # Calculate total credits height
        self._calculate_credits_height()
        
        # Phase control
        self.PHASE_THE_END = 0
        self.PHASE_SCROLLING = 1
        self.PHASE_FINISHED = 2
        self.current_phase = self.PHASE_THE_END
        
        # THE END display
        self.the_end_timer = 0
        self.the_end_duration = 30.0  # Show THE END for 3 seconds
        self.the_end_alpha = 0
        self.the_end_fade_speed = 150  # Alpha per second
    
    def _calculate_credits_height(self):
        """Calculate the total height of all credits"""
        self.total_height = 0
        line_spacing = 60
        
        for item in self.credits_data:
            if isinstance(item, tuple):
                text, style = item
                if style == "title":
                    self.total_height += 150
                elif style == "header":
                    self.total_height += 100
                elif style == "credit":
                    self.total_height += line_spacing
                elif style == "small":
                    self.total_height += 50
            else:
                # Empty line
                self.total_height += 40
    
    def on_enter(self, **kwargs):
        """Called when entering credits state"""
        print("[CREDITS] Showing credits...")
        
        # Hide all UI
        if self.game.day_ui:
            self.game.day_ui.visible = False
        if self.game.interaction_prompt:
            self.game.interaction_prompt.visible = False
        if self.game.inventory_ui:
            self.game.inventory_ui.visible = False
        
        # Reset state
        self.current_phase = self.PHASE_THE_END
        self.the_end_timer = 0
        self.the_end_alpha = 0
        self.scroll_y = self.screen.get_height()
    
    def handle_input(self, events):
        """Handle input events"""
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # Return to main menu
                    print("[CREDITS] Returning to main menu...")
                    self.state_machine.change_state("main_menu")
                
                elif event.key == pygame.K_SPACE:
                    # Skip to scrolling credits
                    if self.current_phase == self.PHASE_THE_END:
                        self.current_phase = self.PHASE_SCROLLING
                    # Speed up scrolling
                    elif self.current_phase == self.PHASE_SCROLLING:
                        self.scroll_speed = 200
    
    def update(self, dt):
        """Update credits"""
        if self.current_phase == self.PHASE_THE_END:
            self.the_end_timer += dt
            
            # Fade in THE END
            if self.the_end_alpha < 255:
                self.the_end_alpha = min(255, self.the_end_alpha + self.the_end_fade_speed * dt)
            
            # After duration, start scrolling
            if self.the_end_timer >= self.the_end_duration:
                self.current_phase = self.PHASE_SCROLLING
        
        elif self.current_phase == self.PHASE_SCROLLING:
            # Scroll credits up
            self.scroll_y -= self.scroll_speed * dt
            
            # Check if credits finished scrolling
            if self.scroll_y < -self.total_height - 200:
                self.current_phase = self.PHASE_FINISHED
    
    def draw_the_end(self):
        """Draw THE END screen"""
        self.screen.fill(self.bg_color)
        
        # Draw THE END
        text = self.title_font.render("THE END", True, self.text_color)
        text.set_alpha(int(self.the_end_alpha))
        text_rect = text.get_rect(center=(
            self.screen.get_width() // 2,
            self.screen.get_height() // 2
        ))
        self.screen.blit(text, text_rect)
        
        # Draw skip hint (faded)
        if self.the_end_alpha > 200:
            hint = self.small_font.render("Press SPACE to continue", True, self.dim_text_color)
            hint.set_alpha(100)
            hint_rect = hint.get_rect(center=(
                self.screen.get_width() // 2,
                self.screen.get_height() - 100
            ))
            self.screen.blit(hint, hint_rect)
    
    def draw_scrolling_credits(self):
        """Draw scrolling credits"""
        self.screen.fill(self.bg_color)
        
        y_pos = self.scroll_y
        screen_height = self.screen.get_height()
        screen_width = self.screen.get_width()
        
        for item in self.credits_data:
            # Only draw if visible on screen
            if -100 < y_pos < screen_height + 100:
                if isinstance(item, tuple):
                    text, style = item
                    
                    if style == "title":
                        surface = self.title_font.render(text, True, self.text_color)
                        y_pos += 75
                    elif style == "header":
                        surface = self.header_font.render(text, True, self.text_color)
                        y_pos += 50
                    elif style == "credit":
                        surface = self.credit_font.render(text, True, self.dim_text_color)
                        y_pos += 30
                    elif style == "small":
                        surface = self.small_font.render(text, True, self.dim_text_color)
                        y_pos += 25
                    else:
                        y_pos += 40
                        continue
                    
                    # Center text
                    rect = surface.get_rect(center=(screen_width // 2, y_pos))
                    
                    # Fade out at top and bottom edges
                    alpha = 255
                    if y_pos < 200:
                        alpha = int((y_pos / 200) * 255)
                    elif y_pos > screen_height - 200:
                        alpha = int(((screen_height - y_pos) / 200) * 255)
                    
                    alpha = max(0, min(255, alpha))
                    surface.set_alpha(alpha)
                    
                    self.screen.blit(surface, rect)
                    
                    if style == "title":
                        y_pos += 75
                    elif style == "header":
                        y_pos += 50
                    else:
                        y_pos += 30
                else:
                    # Empty line
                    y_pos += 40
            else:
                # Skip calculations for offscreen items
                if isinstance(item, tuple):
                    text, style = item
                    if style == "title":
                        y_pos += 150
                    elif style == "header":
                        y_pos += 100
                    elif style == "credit":
                        y_pos += 60
                    else:
                        y_pos += 50
                else:
                    y_pos += 40
    
    def draw_finished(self):
        """Draw finished state (after credits scroll)"""
        self.screen.fill(self.bg_color)
        
        # Show message
        text = self.header_font.render("Thank you for playing!", True, self.text_color)
        text_rect = text.get_rect(center=(
            self.screen.get_width() // 2,
            self.screen.get_height() // 2
        ))
        self.screen.blit(text, text_rect)
        
        # ESC hint
        hint = self.small_font.render("Press ESC to return to main menu", True, self.dim_text_color)
        hint_rect = hint.get_rect(center=(
            self.screen.get_width() // 2,
            self.screen.get_height() // 2 + 80
        ))
        self.screen.blit(hint, hint_rect)
    
    def run(self, dt):
        """Main run loop"""
        self.update(dt)
        
        if self.current_phase == self.PHASE_THE_END:
            self.draw_the_end()
        elif self.current_phase == self.PHASE_SCROLLING:
            self.draw_scrolling_credits()
        elif self.current_phase == self.PHASE_FINISHED:
            self.draw_finished()
