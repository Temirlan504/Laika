import pygame
from utils.button import Button
from utils.settings import SCREEN_WIDTH, SCREEN_HEIGHT

class SaveLoadMenuState:
    """Menu for saving and loading games"""
    
    def __init__(self, state_machine, game):
        """
        Args:
            state_machine: State machine instance
            game: Main game object
        """
        self.state_machine = state_machine
        self.game = game
        self.screen = game.screen
        
        # Mode will be determined by which state name we're registered as
        # 'save_menu' -> mode='save', 'load_menu' -> mode='load'
        self.mode = 'save'  # Default
        
        # Fonts
        self.title_font = pygame.font.Font(None, 72)
        self.slot_font = pygame.font.Font(None, 48)
        self.info_font = pygame.font.Font(None, 32)
        self.small_font = pygame.font.Font(None, 24)
        
        # Colors
        self.bg_color = (20, 20, 30)
        self.title_color = (255, 255, 255)
        self.slot_color = (60, 60, 80)
        self.slot_hover_color = (80, 80, 120)
        self.slot_text_color = (255, 255, 255)
        self.empty_slot_color = (40, 40, 50)
        
        # Layout
        self.slot_width = 600
        self.slot_height = 120
        self.slot_spacing = 20
        self.start_y = 180
        
        # Buttons
        self.slot_buttons = []
        self.back_button = None
        self.delete_buttons = []
        
        self._create_buttons()
    
    def _create_buttons(self):
        """Create UI buttons"""
        # Get save slot data
        slots = self.game.save_manager.get_save_slots()
        
        # Create slot buttons
        self.slot_buttons = []
        self.delete_buttons = []
        
        for i, slot_data in enumerate(slots):
            slot_num = slot_data['slot']
            y_pos = self.start_y + i * (self.slot_height + self.slot_spacing)
            x_pos = (SCREEN_WIDTH - self.slot_width) // 2
            
            # Slot button
            button = Button(
                x=x_pos,
                y=y_pos,
                width=self.slot_width - 100,  # Leave space for delete button
                height=self.slot_height,
                text=f"Slot {slot_num}",
                callback=lambda s=slot_num: self._handle_slot_click(s),
                font=self.slot_font
            )
            button.slot_data = slot_data
            self.slot_buttons.append(button)
            
            # Delete button (only for existing saves in load mode)
            if slot_data['exists'] and self.mode == 'load':
                delete_btn = Button(
                    x=x_pos + self.slot_width - 90,
                    y=y_pos + 10,
                    width=80,
                    height=40,
                    text="Delete",
                    callback=lambda s=slot_num: self._handle_delete(s),
                    font=self.small_font,
                    normal_color=(150, 50, 50),
                    hover_color=(200, 70, 70)
                )
                self.delete_buttons.append(delete_btn)
        
        # Back button
        self.back_button = Button(
            x=50,
            y=SCREEN_HEIGHT - 100,
            width=200,
            height=60,
            text="Back",
            callback=self._handle_back,
            font=self.info_font
        )
    
    def _handle_slot_click(self, slot):
        """Handle clicking on a save slot"""
        if self.mode == 'save':
            # Save the game
            success = self.game.save_manager.save_game(self.game, slot)
            if success:
                print(f"Game saved to slot {slot}")
                # Return to pause menu
                self.state_machine.change_state("pause_menu")
            else:
                print(f"Failed to save to slot {slot}")
        
        elif self.mode == 'load':
            # Load the game
            slots = self.game.save_manager.get_save_slots()
            slot_data = next((s for s in slots if s['slot'] == slot), None)
            
            if slot_data and slot_data['exists']:
                success = self.game.save_manager.load_game(self.game, slot)
                if success:
                    print(f"Game loaded from slot {slot}")
                    # Return to the game
                    self.state_machine.change_state("level")
                else:
                    print(f"Failed to load from slot {slot}")
            else:
                print(f"Slot {slot} is empty")
    
    def _handle_delete(self, slot):
        """Handle deleting a save slot"""
        self.game.save_manager.delete_save(slot)
        # Recreate buttons to reflect changes
        self._create_buttons()
    
    def _handle_back(self):
        """Return to previous menu"""
        if self.mode == 'save':
            self.state_machine.change_state("pause_menu")
        else:
            self.state_machine.change_state("main_menu")
    
    def on_enter(self, **kwargs):
        """Called when entering this state"""
        # Determine mode based on kwargs or try to infer from registered state names
        if 'mode' in kwargs:
            self.mode = kwargs['mode']
        else:
            # Try to infer from which state we are
            # Check if we're registered as save_menu or load_menu by checking the states dict
            self.mode = 'save'  # Default to save
            for state_name, state_instance in self.state_machine.state_instances.items():
                if state_instance is self:
                    if 'load' in state_name.lower():
                        self.mode = 'load'
                    elif 'save' in state_name.lower():
                        self.mode = 'save'
                    break
        
        self._create_buttons()  # Refresh slot data
    
    def handle_input(self, events):
        """Handle input events"""
        mouse_pos = pygame.mouse.get_pos()
        
        # Update all button hover states
        for button in self.slot_buttons:
            button.update(mouse_pos)
        for button in self.delete_buttons:
            button.update(mouse_pos)
        self.back_button.update(mouse_pos)
        
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._handle_back()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    # Check slot buttons
                    for button in self.slot_buttons:
                        if button.hovered:
                            button.callback()
                    
                    # Check delete buttons
                    for button in self.delete_buttons:
                        if button.hovered:
                            button.callback()
                    
                    # Check back button
                    if self.back_button.hovered:
                        self.back_button.callback()
    
    def run(self, dt):
        """Main run loop"""
        self.screen.fill(self.bg_color)
        
        # Draw title
        title_text = "SAVE GAME" if self.mode == 'save' else "LOAD GAME"
        title_surf = self.title_font.render(title_text, True, self.title_color)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 80))
        self.screen.blit(title_surf, title_rect)
        
        # Get mouse position and update button hover states
        mouse_pos = pygame.mouse.get_pos()
        for button in self.slot_buttons:
            button.update(mouse_pos)
        for button in self.delete_buttons:
            button.update(mouse_pos)
        self.back_button.update(mouse_pos)
        
        # Draw slot buttons
        for button in self.slot_buttons:
            slot_data = button.slot_data
            is_hovered = button.hovered
            
            # Determine color
            if slot_data['exists']:
                color = self.slot_hover_color if is_hovered else self.slot_color
            else:
                color = self.empty_slot_color
            
            # Draw slot background
            pygame.draw.rect(self.screen, color, button.rect, border_radius=10)
            pygame.draw.rect(self.screen, self.title_color, button.rect, 3, border_radius=10)
            
            # Draw slot text
            if slot_data['exists']:
                # Slot number
                slot_text = self.slot_font.render(f"Slot {slot_data['slot']}", True, self.slot_text_color)
                self.screen.blit(slot_text, (button.rect.x + 20, button.rect.y + 15))
                
                # Slot info (day, timestamp)
                info_text = f"Sol {slot_data['day']} - {slot_data['timestamp'][:16]}"
                info_surf = self.small_font.render(info_text, True, (200, 200, 200))
                self.screen.blit(info_surf, (button.rect.x + 20, button.rect.y + 70))
            else:
                # Empty slot
                empty_text = self.slot_font.render(f"Slot {slot_data['slot']} - Empty", True, (100, 100, 100))
                self.screen.blit(empty_text, (button.rect.x + 20, button.rect.y + 40))
        
        # Draw delete buttons
        for button in self.delete_buttons:
            is_hovered = button.hovered
            color = button.hover_color if is_hovered else button.normal_color
            
            pygame.draw.rect(self.screen, color, button.rect, border_radius=5)
            pygame.draw.rect(self.screen, (255, 255, 255), button.rect, 2, border_radius=5)
            
            text_surf = button.font.render(button.text, True, (255, 255, 255))
            text_rect = text_surf.get_rect(center=button.rect.center)
            self.screen.blit(text_surf, text_rect)
        
        # Draw back button
        is_hovered = self.back_button.hovered
        color = self.back_button.hover_color if is_hovered else self.back_button.normal_color
        
        pygame.draw.rect(self.screen, color, self.back_button.rect, border_radius=8)
        pygame.draw.rect(self.screen, (255, 255, 255), self.back_button.rect, 2, border_radius=8)
        
        text_surf = self.back_button.font.render(self.back_button.text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=self.back_button.rect.center)
        self.screen.blit(text_surf, text_rect)
