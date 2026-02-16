import pygame
from utils.fade_effect import FadeEffect

class EndingSceneState:
    """
    Cinematic ending scene where the player lies down and the screen fades to black.
    Triggers when the player reaches the final day (LAST_SOL).
    """
    
    def __init__(self, state_machine, game):
        self.state_machine = state_machine
        self.game = game
        self.screen = game.screen
        
        # Fade effect
        self.fade_effect = FadeEffect(self.screen)
        
        # Scene phases
        self.PHASE_LYING_DOWN = 0
        self.PHASE_FADING = 1
        self.PHASE_COMPLETE = 2
        self.current_phase = self.PHASE_LYING_DOWN
        
        # Timing
        self.lying_down_duration = 3.0  # 3 seconds of lying down before fade
        self.timer = 0
        
        # Player animation state
        self.player_lying_down = False
        self.original_player_image = None
        
        # Text overlay
        try:
            self.font = pygame.font.Font(None, 48)
        except:
            self.font = pygame.font.SysFont(None, 48)
        self.text_alpha = 0
        self.text_fade_in = True
        self.show_text = True
    
    def on_enter(self, **kwargs):
        """Called when entering this state"""
        print("[ENDING] Entering ending scene...")
        
        # Block player input
        if self.game.player:
            self.game.player.block_input()
        
        # Stop time
        if hasattr(self.game, 'clock_system'):
            self.game.clock_system.speed = 0
        
        # Hide UI
        if self.game.day_ui:
            self.game.day_ui.visible = False
        if self.game.interaction_prompt:
            self.game.interaction_prompt.visible = False
        if self.game.inventory_ui:
            self.game.inventory_ui.visible = False
        if self.game.hotbar_ui:
            self.game.hotbar_ui.visible = False
        
        # Reset state
        self.current_phase = self.PHASE_LYING_DOWN
        self.timer = 0
        self.text_alpha = 0
        self.text_fade_in = True
        
        # Make player lie down (rotate sprite)
        if self.game.player:
            self._make_player_lie_down()
    
    def _make_player_lie_down(self):
        """Rotate player sprite to make them appear lying down"""
        if not self.player_lying_down and self.game.player:
            # Save original image
            self.original_player_image = self.game.player.image.copy()
            
            # Rotate player 90 degrees (lying down)
            self.game.player.image = pygame.transform.rotate(
                self.game.player.image, 
                90
            )
            
            # Update rect to maintain center position
            old_center = self.game.player.rect.center
            self.game.player.rect = self.game.player.image.get_rect()
            self.game.player.rect.center = old_center
            
            self.player_lying_down = True
            print("[ENDING] Player lying down...")
    
    def _start_fade(self):
        """Start the fade to black"""
        print("[ENDING] Starting fade to black...")
        self.current_phase = self.PHASE_FADING
        
        # Recreate fade surface with current screen size
        self.fade_effect.surface = pygame.Surface(self.screen.get_size())
        self.fade_effect.surface.fill((0, 0, 0))
        
        # Start fade
        self.fade_effect.fade_in(self._on_fade_complete)
    
    def _on_fade_complete(self):
        """Called when fade to black is complete"""
        print("[ENDING] Fade complete, transitioning to credits...")
        self.current_phase = self.PHASE_COMPLETE
        # Transition to credits
        self.state_machine.change_state("credits")
    
    def handle_input(self, events):
        """Handle input events (mostly blocked during cutscene)"""
        for event in events:
            # Allow skipping with ENTER or SPACE
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    # Skip to next phase
                    if self.current_phase == self.PHASE_LYING_DOWN:
                        self._start_fade()
                    elif self.current_phase == self.PHASE_FADING:
                        # Skip directly to credits
                        self.state_machine.change_state("credits")
    
    def update(self, dt):
        """Update the ending scene"""
        self.timer += dt
        
        if self.current_phase == self.PHASE_LYING_DOWN:
            # Fade in text slowly
            if self.text_fade_in and self.text_alpha < 255:
                self.text_alpha = min(255, self.text_alpha + 60 * dt)
            
            # After lying down duration, start fade
            if self.timer >= self.lying_down_duration:
                self._start_fade()
        
        elif self.current_phase == self.PHASE_FADING:
            # Fade out text
            if self.text_alpha > 0:
                self.text_alpha = max(0, self.text_alpha - 100 * dt)
            
            # Update fade effect
            self.fade_effect.update(dt)
    
    def draw_text_overlay(self):
        """Draw text overlay during lying down phase"""
        if self.show_text and self.text_alpha > 0:
            # Create semi-transparent text
            text_lines = [
                "The journey ends...",
                "Press SPACE to continue"
            ]
            
            y_offset = self.screen.get_height() // 2 - 50
            
            for line in text_lines:
                text_surface = self.font.render(line, True, (255, 255, 255))
                text_surface.set_alpha(int(self.text_alpha))
                
                text_rect = text_surface.get_rect(
                    center=(self.screen.get_width() // 2, y_offset)
                )
                
                self.screen.blit(text_surface, text_rect)
                y_offset += 60
    
    def run(self, dt):
        """Main run loop"""
        self.update(dt)
        
        # Get level state to render the game world
        level_state = self.state_machine.state_instances.get('level')
        
        if level_state:
            # Render the level (frozen) in the background
            level_state.run(0)  # dt=0 means no updates, just draw
        else:
            # Fallback: black screen
            self.screen.fill((0, 0, 0))
        
        # Draw text overlay
        if self.current_phase == self.PHASE_LYING_DOWN:
            self.draw_text_overlay()
        
        # Draw fade effect
        self.fade_effect.draw()
