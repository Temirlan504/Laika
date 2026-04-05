import pygame
from utils.button import Button
from utils.settings import SCREEN_WIDTH, SCREEN_HEIGHT
from utils.support import resource_path

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
        
        # Confirmation dialog state
        self.show_confirmation = False
        self.confirmation_action = None  # 'save', 'load', or 'delete'
        self.confirmation_slot = None
        
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
        
        # Layout - centered vertically
        self.slot_width = 600
        self.slot_height = 120
        self.slot_spacing = 20
        self.title_height = 100  # Space for title
        
        # Will be calculated in run() based on actual screen size
        self.title_y = 0
        self.start_y = 0
        
        # Buttons
        self.slot_buttons = []
        self.back_button = None
        self.delete_buttons = []
        
        # Confirmation dialog buttons
        self.confirm_yes_button = None
        self.confirm_no_button = None
        
        self._create_buttons()
        self.load_sounds()

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
    
    def _create_buttons(self):
        """Create UI buttons"""
        # Get save slot data
        slots = self.game.save_manager.get_save_slots()
        
        # If in load mode, also include auto-save (slot 0)
        if self.mode == 'load':
            auto_save_file = self.game.save_manager.save_directory / "save_slot_0.json"
            if auto_save_file.exists():
                try:
                    import json
                    with open(auto_save_file, 'r') as f:
                        data = json.load(f)
                        auto_save_slot = {
                            'slot': 0,
                            'exists': True,
                            'timestamp': data.get('metadata', {}).get('timestamp', 'Unknown'),
                            'day': data.get('world', {}).get('day', 0),
                            'playtime': data.get('metadata', {}).get('playtime', 0)
                        }
                        # Insert auto-save at the beginning
                        slots.insert(0, auto_save_slot)
                except:
                    pass
        
        # Create slot buttons
        self.slot_buttons = []
        self.delete_buttons = []
        
        for i, slot_data in enumerate(slots):
            slot_num = slot_data['slot']
            y_pos = self.start_y + i * (self.slot_height + self.slot_spacing)
            x_pos = (SCREEN_WIDTH - self.slot_width) // 2
            
            # Slot button label
            if slot_num == 0:
                slot_label = "Auto-Save"
            else:
                slot_label = f"Slot {slot_num}"
            
            # Slot button
            button = Button(
                x=x_pos,
                y=y_pos,
                width=self.slot_width - 100,  # Leave space for delete button
                height=self.slot_height,
                text=slot_label,
                callback=lambda s=slot_num: self._handle_slot_click(s),
                font=self.slot_font
            )
            button.slot_data = slot_data
            self.slot_buttons.append(button)
            
            # Delete button (only for manual saves in load mode, not auto-save)
            if slot_data['exists'] and self.mode == 'load' and slot_num != 0:
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
            # Show confirmation for saving (will overwrite)
            slots = self.game.save_manager.get_save_slots()
            slot_data = next((s for s in slots if s['slot'] == slot), None)
            
            if slot_data and slot_data['exists']:
                # Slot has data - confirm overwrite
                self.show_confirmation = True
                self.confirmation_action = 'save'
                self.confirmation_slot = slot
            else:
                # Empty slot - save directly
                self._perform_save(slot)
        
        elif self.mode == 'load':
            # Show confirmation for loading
            slots = self.game.save_manager.get_save_slots()
            slot_data = next((s for s in slots if s['slot'] == slot), None)
            
            if slot_data and slot_data['exists']:
                self.show_confirmation = True
                self.confirmation_action = 'load'
                self.confirmation_slot = slot
            else:
                print(f"Slot {slot} is empty")
    
    def _handle_delete(self, slot):
        """Handle deleting a save slot"""
        # Show confirmation for deleting
        self.show_confirmation = True
        self.confirmation_action = 'delete'
        self.confirmation_slot = slot
    
    def _perform_save(self, slot):
        """Actually perform the save operation"""
        success = self.game.save_manager.save_game(self.game, slot)
        if success:
            print(f"Game saved to slot {slot}")
            # Return to pause menu
            self.state_machine.change_state("pause_menu")
        else:
            print(f"Failed to save to slot {slot}")
    
    def _perform_load(self, slot):
        """Actually perform the load operation"""
        # Initialize player if it doesn't exist (loading from main menu)
        if self.game.player is None:
            print("Creating player for load...")
            self.game.initialize_game()
        
        # Clear stale level/greenhouse state
        if "level" in self.state_machine.state_instances:
            del self.state_machine.state_instances["level"]
        if "greenhouse" in self.state_machine.state_instances:
            del self.state_machine.state_instances["greenhouse"]
        
        # Load the save data
        success = self.game.save_manager.load_game(self.game, slot)
        if success:
            print(f"Game loaded from slot {slot}")
            # Return to the game
            self.state_machine.change_state("level")
        else:
            print(f"Failed to load from slot {slot}")
    
    def _perform_delete(self, slot):
        """Actually perform the delete operation"""
        self.game.save_manager.delete_save(slot)
        print(f"Deleted save slot {slot}")
        # Recreate buttons to reflect changes
        self._create_buttons()
    
    def _confirm_action(self):
        """Confirm the pending action"""
        if self.confirmation_action == 'save':
            self._perform_save(self.confirmation_slot)
        elif self.confirmation_action == 'load':
            self._perform_load(self.confirmation_slot)
        elif self.confirmation_action == 'delete':
            self._perform_delete(self.confirmation_slot)
        
        # Close confirmation dialog
        self.show_confirmation = False
        self.confirmation_action = None
        self.confirmation_slot = None
    
    def _cancel_confirmation(self):
        """Cancel the confirmation dialog"""
        self.show_confirmation = False
        self.confirmation_action = None
        self.confirmation_slot = None
    
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
        mouse_pos = pygame.mouse.get_pos()

        if self.show_confirmation:
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self._cancel_confirmation()
                    elif event.key == pygame.K_RETURN:
                        self._confirm_action()

                if event.type == pygame.MOUSEMOTION:
                    for button in [self.confirm_yes_button, self.confirm_no_button]:
                        if button:
                            was_hovered = button.hovered
                            button.hovered = button.rect.collidepoint(event.pos)
                            if button.hovered and not was_hovered:
                                if self.sounds.get('hover'):
                                    self.sounds['hover'].play()

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.confirm_yes_button and self.confirm_yes_button.hovered:
                        if self.sounds.get('click'):
                            self.sounds['click'].play()
                        self.confirm_yes_button.callback()
                    elif self.confirm_no_button and self.confirm_no_button.hovered:
                        if self.sounds.get('click'):
                            self.sounds['click'].play()
                        self.confirm_no_button.callback()

            if self.confirm_yes_button:
                self.confirm_yes_button.update(mouse_pos)
            if self.confirm_no_button:
                self.confirm_no_button.update(mouse_pos)
            return

        # Normal input
        all_buttons = self.slot_buttons + self.delete_buttons + [self.back_button]

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._handle_back()

            if event.type == pygame.MOUSEMOTION:
                for button in all_buttons:
                    was_hovered = button.hovered
                    button.hovered = button.rect.collidepoint(event.pos)
                    if button.hovered and not was_hovered:
                        if self.sounds.get('hover'):
                            self.sounds['hover'].play()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for button in all_buttons:
                    if button.hovered and button.callback:
                        if self.sounds.get('click'):
                            self.sounds['click'].play()
                        button.callback()
                        break

        for button in self.slot_buttons:
            button.update(mouse_pos)
        for button in self.delete_buttons:
            button.update(mouse_pos)
        self.back_button.update(mouse_pos)
    
    def run(self, dt):
        """Main run loop"""
        self.screen.fill(self.bg_color)
        
        # Get actual screen dimensions (important for resizable windows!)
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        
        # Calculate vertical centering based on actual screen size
        total_slots = len(self.slot_buttons)
        total_height = self.title_height + (total_slots * self.slot_height) + ((total_slots - 1) * self.slot_spacing)
        menu_start_y = (screen_height - total_height) // 2
        self.title_y = menu_start_y + 40
        calculated_start_y = menu_start_y + self.title_height
        
        # Draw title
        title_text = "SAVE GAME" if self.mode == 'save' else "LOAD GAME"
        title_surf = self.title_font.render(title_text, True, self.title_color)
        title_rect = title_surf.get_rect(center=(screen_width // 2, self.title_y))
        self.screen.blit(title_surf, title_rect)
        
        # Get mouse position and update button hover states
        mouse_pos = pygame.mouse.get_pos()
        for button in self.slot_buttons:
            button.update(mouse_pos)
        for button in self.delete_buttons:
            button.update(mouse_pos)
        self.back_button.update(mouse_pos)
        
        # Draw slot buttons with dynamically calculated positions
        for i, button in enumerate(self.slot_buttons):
            slot_data = button.slot_data
            
            # Calculate position based on screen size
            y_pos = calculated_start_y + i * (self.slot_height + self.slot_spacing)
            x_pos = (screen_width - self.slot_width) // 2
            
            # Update button rect for proper positioning
            button.rect.x = x_pos
            button.rect.y = y_pos
            
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
                # Slot number/name
                if slot_data['slot'] == 0:
                    slot_text = self.slot_font.render("Auto-Save", True, self.slot_text_color)
                else:
                    slot_text = self.slot_font.render(f"Slot {slot_data['slot']}", True, self.slot_text_color)
                self.screen.blit(slot_text, (button.rect.x + 20, button.rect.y + 15))
                
                # Slot info (day, timestamp)
                info_text = f"Sol {slot_data['day']} - {slot_data['timestamp'][:16]}"
                info_surf = self.small_font.render(info_text, True, (200, 200, 200))
                self.screen.blit(info_surf, (button.rect.x + 20, button.rect.y + 70))
            else:
                # Empty slot
                if slot_data['slot'] == 0:
                    empty_text = self.slot_font.render("Auto-Save - Empty", True, (100, 100, 100))
                else:
                    empty_text = self.slot_font.render(f"Slot {slot_data['slot']} - Empty", True, (100, 100, 100))
                self.screen.blit(empty_text, (button.rect.x + 20, button.rect.y + 40))
        
        # Draw delete buttons with updated positions
        delete_button_index = 0
        for i, button in enumerate(self.slot_buttons):
            slot_data = button.slot_data
            # Only show delete button for existing manual saves
            if slot_data['exists'] and self.mode == 'load' and slot_data['slot'] != 0:
                if delete_button_index < len(self.delete_buttons):
                    delete_btn = self.delete_buttons[delete_button_index]
                    
                    # Position delete button relative to its slot
                    delete_btn.rect.x = button.rect.x + self.slot_width - 90
                    delete_btn.rect.y = button.rect.y + 10
                    
                    is_hovered = delete_btn.hovered
                    color = delete_btn.hover_color if is_hovered else delete_btn.normal_color
                    
                    pygame.draw.rect(self.screen, color, delete_btn.rect, border_radius=5)
                    pygame.draw.rect(self.screen, (255, 255, 255), delete_btn.rect, 2, border_radius=5)
                    
                    text_surf = delete_btn.font.render(delete_btn.text, True, (255, 255, 255))
                    text_rect = text_surf.get_rect(center=delete_btn.rect.center)
                    self.screen.blit(text_surf, text_rect)
                    
                    delete_button_index += 1
        
        # Draw back button (update position for resizable screen)
        self.back_button.rect.y = screen_height - 100
        is_hovered = self.back_button.hovered
        color = self.back_button.hover_color if is_hovered else self.back_button.normal_color
        
        pygame.draw.rect(self.screen, color, self.back_button.rect, border_radius=8)
        pygame.draw.rect(self.screen, (255, 255, 255), self.back_button.rect, 2, border_radius=8)
        
        text_surf = self.back_button.font.render(self.back_button.text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=self.back_button.rect.center)
        self.screen.blit(text_surf, text_rect)
        
        # Draw confirmation dialog if showing
        if self.show_confirmation:
            self._draw_confirmation_dialog()
    
    def _draw_confirmation_dialog(self):
        """Draw the confirmation dialog overlay"""
        # Get actual screen dimensions
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        
        # Semi-transparent overlay
        overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        # Dialog box
        dialog_width = 500
        dialog_height = 250
        dialog_x = (screen_width - dialog_width) // 2
        dialog_y = (screen_height - dialog_height) // 2
        dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
        
        # Draw dialog background
        pygame.draw.rect(self.screen, (40, 40, 50), dialog_rect, border_radius=15)
        pygame.draw.rect(self.screen, (255, 255, 255), dialog_rect, 3, border_radius=15)
        
        # Confirmation text
        if self.confirmation_action == 'save':
            message = f"Overwrite Slot {self.confirmation_slot}?"
            submessage = "This will replace the existing save."
        elif self.confirmation_action == 'load':
            if self.confirmation_slot == 0:
                message = "Load Auto-Save?"
            else:
                message = f"Load Slot {self.confirmation_slot}?"
            submessage = "Unsaved progress will be lost."
        elif self.confirmation_action == 'delete':
            if self.confirmation_slot == 0:
                message = "Delete Auto-Save?"
            else:
                message = f"Delete Slot {self.confirmation_slot}?"
            submessage = "This cannot be undone!"
        else:
            message = "Are you sure?"
            submessage = ""
        
        # Draw message
        msg_surf = self.info_font.render(message, True, (255, 255, 255))
        msg_rect = msg_surf.get_rect(center=(dialog_rect.centerx, dialog_rect.y + 60))
        self.screen.blit(msg_surf, msg_rect)
        
        # Draw submessage
        if submessage:
            submsg_surf = self.small_font.render(submessage, True, (200, 200, 200))
            submsg_rect = submsg_surf.get_rect(center=(dialog_rect.centerx, dialog_rect.y + 100))
            self.screen.blit(submsg_surf, submsg_rect)
        
        # Yes/No buttons
        button_width = 150
        button_height = 50
        button_y = dialog_rect.y + dialog_height - 80
        
        # Create Yes button if not exists
        if not self.confirm_yes_button:
            self.confirm_yes_button = Button(
                x=dialog_rect.centerx - button_width - 20,
                y=button_y,
                width=button_width,
                height=button_height,
                text="YES",
                callback=self._confirm_action,
                font=self.info_font,
                normal_color=(80, 150, 80),
                hover_color=(100, 200, 100)
            )
        
        # Create No button if not exists
        if not self.confirm_no_button:
            self.confirm_no_button = Button(
                x=dialog_rect.centerx + 20,
                y=button_y,
                width=button_width,
                height=button_height,
                text="NO",
                callback=self._cancel_confirmation,
                font=self.info_font,
                normal_color=(150, 80, 80),
                hover_color=(200, 100, 100)
            )
        
        # Update button positions (in case of window resize)
        self.confirm_yes_button.rect.x = dialog_rect.centerx - button_width - 20
        self.confirm_yes_button.rect.y = button_y
        self.confirm_no_button.rect.x = dialog_rect.centerx + 20
        self.confirm_no_button.rect.y = button_y
        
        # Draw buttons
        mouse_pos = pygame.mouse.get_pos()
        
        # Yes button
        is_hovered = self.confirm_yes_button.hovered
        color = self.confirm_yes_button.hover_color if is_hovered else self.confirm_yes_button.normal_color
        pygame.draw.rect(self.screen, color, self.confirm_yes_button.rect, border_radius=8)
        pygame.draw.rect(self.screen, (255, 255, 255), self.confirm_yes_button.rect, 2, border_radius=8)
        text = self.confirm_yes_button.font.render(self.confirm_yes_button.text, True, (255, 255, 255))
        text_rect = text.get_rect(center=self.confirm_yes_button.rect.center)
        self.screen.blit(text, text_rect)
        
        # No button
        is_hovered = self.confirm_no_button.hovered
        color = self.confirm_no_button.hover_color if is_hovered else self.confirm_no_button.normal_color
        pygame.draw.rect(self.screen, color, self.confirm_no_button.rect, border_radius=8)
        pygame.draw.rect(self.screen, (255, 255, 255), self.confirm_no_button.rect, 2, border_radius=8)
        text = self.confirm_no_button.font.render(self.confirm_no_button.text, True, (255, 255, 255))
        text_rect = text.get_rect(center=self.confirm_no_button.rect.center)
        self.screen.blit(text, text_rect)
