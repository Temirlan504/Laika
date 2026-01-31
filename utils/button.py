"""
Reusable Button Component
"""
import pygame

class Button:
    def __init__(self, x, y, width, height, text, font, 
                 normal_color=(209, 94, 62),  # #d15e3e
                 hover_color=(230, 120, 90),
                 pressed_color=(180, 70, 50),
                 text_color=(255, 255, 255),
                 border_radius=10,
                 callback=None):
        
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        
        # Colors
        self.normal_color = normal_color
        self.hover_color = hover_color
        self.pressed_color = pressed_color
        self.text_color = text_color
        self.border_radius = border_radius
        
        # State
        self.hovered = False
        self.pressed = False
        self.callback = callback
        
        # Optional background image (if you want to use Canva button)
        self.bg_image = None
    
    def set_background_image(self, image_path):
        """Load button background from image"""
        self.bg_image = pygame.image.load(image_path).convert_alpha()
        self.bg_image = pygame.transform.scale(self.bg_image, (self.rect.width, self.rect.height))
    
    def handle_event(self, event):
        """Handle mouse events"""
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.hovered:
                self.pressed = True
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                if self.pressed and self.hovered:
                    if self.callback:
                        self.callback()
                self.pressed = False
    
    def update(self, mouse_pos):
        """Update hover state (alternative to event handling)"""
        self.hovered = self.rect.collidepoint(mouse_pos)
    
    def draw(self, screen):
        """Draw the button"""
        # Determine color based on state
        if self.pressed and self.hovered:
            color = self.pressed_color
        elif self.hovered:
            color = self.hover_color
        else:
            color = self.normal_color
        
        # Draw background (image or colored rect)
        if self.bg_image:
            screen.blit(self.bg_image, self.rect)
        else:
            # Draw rounded rectangle
            pygame.draw.rect(screen, color, self.rect, border_radius=self.border_radius)
            # Optional: add border for pixelated effect
            pygame.draw.rect(screen, (180, 80, 60), self.rect, 3, border_radius=self.border_radius)
        
        # Draw text
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
    
    def set_position(self, x, y):
        """Update button position"""
        self.rect.x = x
        self.rect.y = y
