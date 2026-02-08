import pygame
import os

class UIConfig:
    """Centralized UI configuration for consistent styling across all UI elements"""
    
    def __init__(self):
        # Initialize pygame font system
        pygame.font.init()
        
        # ============= FONTS =============
        self.font_path = "assets/fonts/PressStart2P.ttf"
        
        # ============= COLOURS =============
        # Base colors
        self.WHITE = (255, 255, 255)
        self.LIGHT_GRAY = (178, 171, 159)
        self.DARK_GRAY = (122, 124, 124)
        self.LIGHT_ORANGE = (227, 136, 98)
        self.DARK_ORANGE = (171, 78, 58)
        self.BLACK = (23, 23, 23)
        
        # Transparent colors (with alpha)
        self.COLOR_PANEL_BG_ALPHA = (25, 30, 45, 230)  # Semi-transparent panel
        self.COLOR_DARK_BG_ALPHA = (15, 20, 35, 220)  # Semi-transparent dark bg
        self.COLOR_OVERLAY = (0, 0, 0, 180)  # Dark overlay for modals
        
        # ============= UI IMAGES =============
        self.images = {}
        self._load_ui_images()
    
    def _load_ui_images(self):
        """Load UI background images and icons"""
        image_paths = {
            'day_time_panel_bg': 'assets/ui/day_time_panel_bg.png',
            'inventory_bg': 'assets/ui/inventory_bg.png',
            'interaction_prompt_bg': 'assets/ui/interaction_prompt_bg.png',
        }
        
        for key, path in image_paths.items():
            try:
                if os.path.exists(path):
                    self.images[key] = pygame.image.load(path).convert_alpha()
            except:
                self.images[key] = None
    
    def get_image(self, key):
        """Get a loaded UI image, returns None if not found"""
        return self.images.get(key, None)
    
    def get_font(self, size, bold=False):
        """Get a font of the specified size
        Uses custom font if available, otherwise falls back to system font
        """
        try:
            return pygame.font.Font(self.font_path, size)
        except:
            return pygame.font.SysFont("consolas,monaco,courier", size, bold=bold)

# Create a global instance to be imported by all UI files
ui_config = UIConfig()
