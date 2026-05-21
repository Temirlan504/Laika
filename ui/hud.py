import pygame
from items import get_item
from ui.ui_element import UIElement
from ui.ui_config import ui_config
from utils.support import resource_path, load_item_image

class DayUI(UIElement):
    def __init__(self, day_cycle, clock, screen):
        super().__init__()
        self.day_cycle = day_cycle
        self.clock = clock
        self.screen = screen
        
        # Load background image
        self.bg_image = None
        try:
            self.bg_image = pygame.image.load(resource_path("assets/ui/day_time_bg.png")).convert_alpha()
        except FileNotFoundError:
            self.bg_image = None
        
        # Fonts - customize sizes here
        self.day_font = ui_config.get_font(20)
        self.time_font = ui_config.get_font(15)
        
        # Panel size
        self.panel_width = 250
        self.panel_height = 100
        
        # Scale background image to fit
        if self.bg_image:
            self.bg_image = pygame.transform.scale(
                self.bg_image, 
                (self.panel_width, self.panel_height)
            )
        
        self.day = day_cycle.day
        day_cycle.subscribe(self)

    def on_new_day(self, day):
        self.day = day

    def draw(self):
        # Position in top-right corner
        bg_x = self.screen.get_width() - self.panel_width - 20
        bg_y = 20
        
        # Draw background (image or fallback)
        if self.bg_image:
            self.screen.blit(self.bg_image, (bg_x, bg_y))
        else:
            # Fallback: dark gray background surface
            bg_surface = pygame.Surface((self.panel_width, self.panel_height))
            bg_surface.fill(ui_config.BLACK)
            self.screen.blit(bg_surface, (bg_x, bg_y))
        
        # Draw text on top of the background
        day_text = f"SOL {self.day}"
        time_text = self.clock.time_string()
        
        day_surface = self.day_font.render(day_text, True, ui_config.DARK_GRAY)
        time_surface = self.time_font.render(time_text, True, ui_config.DARK_GRAY)
        
        # Center text on the background panel
        panel_center_x = bg_x + self.panel_width // 2
        panel_center_y = bg_y + self.panel_height // 2

        offset_x = 50
        
        # Day on top, time on bottom
        day_rect = day_surface.get_rect(center=(panel_center_x + offset_x, panel_center_y - 17))
        time_rect = time_surface.get_rect(center=(panel_center_x + offset_x, panel_center_y + 22))
        
        self.screen.blit(day_surface, day_rect)
        self.screen.blit(time_surface, time_rect)


class IronOreCounterUI(UIElement):
    GOAL        = 50    # Iron ore required to place a greenhouse dome
    CAP_DISPLAY = 99    # Maximum number shown before switching to "99+"
    IMAGE_PATH  = "assets/items/resources/iron_ore.png"

    def __init__(self, player, screen):
        super().__init__()
        self.player  = player
        self.screen  = screen
        self.visible = True

        self.font = ui_config.get_font(15)

        # Match DayUI width so they align cleanly
        self.panel_width  = 250
        self.panel_height = 40

        # Load and scale ore icon to fit inside the bar
        self._icon  = None
        icon_size   = self.panel_height - 8   # 4 px padding top and bottom
        try:
            raw = pygame.image.load(resource_path(self.IMAGE_PATH)).convert_alpha()
            self._icon = pygame.transform.scale(raw, (icon_size, icon_size))
        except FileNotFoundError:
            self._icon = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_count(self):
        """Return total iron ore held across inventory and hotbar."""
        inv_total = self.player.inventory.get_total("iron_ore")

        # Hotbar has no get_total, so we sum slots directly
        hotbar_total = sum(
            slot["quantity"]
            for slot in self.player.hotbar.slots
            if slot and slot["item_id"] == "iron_ore"
        )
        return inv_total + hotbar_total

    def has_enough(self):
        """Return True if the player can afford to place a dome."""
        return self._get_count() >= self.GOAL

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(self):
        if not self.visible:
            return

        count = self._get_count()

        # Sit directly below DayUI: DayUI is at y=20 with height=100, plus a
        # small 10 px gap → y = 130.
        x = self.screen.get_width() - self.panel_width - 20
        y = 130

        # --- Background ---
        bg_rect = pygame.Rect(x, y, self.panel_width, self.panel_height)
        pygame.draw.rect(self.screen, (30, 30, 30), bg_rect)
        pygame.draw.rect(self.screen, (100, 100, 100), bg_rect, 2)

        # --- Icon (or orange fallback square) ---
        icon_h   = self._icon.get_height() if self._icon else 24
        icon_x   = x + 8
        icon_y   = y + (self.panel_height - icon_h) // 2

        if self._icon:
            self.screen.blit(self._icon, (icon_x, icon_y))
            text_x = icon_x + self._icon.get_width() + 8
        else:
            pygame.draw.rect(self.screen, (200, 120, 30),
                             pygame.Rect(icon_x, icon_y, 24, 24))
            text_x = icon_x + 32

        # --- Counter text ---
        if count > self.CAP_DISPLAY:
            display = f"99+/{self.GOAL}"
        else:
            display = f"{count}/{self.GOAL}"

        # Green once goal is met, white otherwise
        color     = (80, 220, 80) if count >= self.GOAL else ui_config.WHITE
        text_surf = self.font.render(display, True, color)
        text_rect = text_surf.get_rect(midleft=(text_x, y + self.panel_height // 2))
        self.screen.blit(text_surf, text_rect)

        # Show build hint to the right of the counter when goal is met
        if count >= self.GOAL:
            hint_font = ui_config.get_font(12)
            hint_surf = hint_font.render("Press 'B'", True, (80, 220, 80))
            hint_rect = hint_surf.get_rect(midleft=(text_rect.right + 10, y + self.panel_height // 2))
            self.screen.blit(hint_surf, hint_rect)


class HotbarUI:
    def __init__(self, screen, hotbar):
        self.screen = screen
        self.hotbar = hotbar
        self.visible = True
        
        # Load background image
        self.bg_image = None
        try:
            self.bg_image = pygame.image.load(resource_path("assets/ui/hotbar_bg.png")).convert_alpha()
        except FileNotFoundError:
            self.bg_image = None
        
        # Visual settings
        self.slot_size = 64
        self.slot_gap = 0
        self.hotbar_width = (self.slot_size + self.slot_gap) * self.hotbar.num_slots - self.slot_gap
        self.hotbar_height = self.slot_size + 20  # Extra space for slot numbers
        
        # Scale background image to fit
        if self.bg_image:
            self.bg_image = pygame.transform.scale(
                self.bg_image, 
                (self.hotbar_width + 40, self.hotbar_height + 10)
            )
        
        # Position at bottom center of screen
        self.padding_bottom = 50
        
        # Colors (fallback if no image)
        self.bg_color = (40, 40, 40, 200)  # Semi-transparent dark gray
        self.slot_color = (60, 60, 60)
        self.selected_color = (255, 255, 255) # Selected slot highlight
        self.border_color = (100, 100, 100)
        
        # Fonts
        self.number_font = ui_config.get_font(15)
        self.qty_font = ui_config.get_font(12)

    def show(self):
        self.visible = True
    
    def hide(self):
        self.visible = False
    
    def get_position(self):
        x = (self.screen.get_width() - self.hotbar_width) // 2
        y = self.screen.get_height() - self.hotbar_height - self.padding_bottom
        return x, y
    
    def draw(self):
        if not self.visible:
            return
        
        x, y = self.get_position()
        offset_x = -20
        offset_y = -5
        
        if self.bg_image:
            self.screen.blit(self.bg_image, (x + offset_x, y + offset_y))
        else:
            bg_surface = pygame.Surface((self.hotbar_width, self.hotbar_height), pygame.SRCALPHA)
            bg_surface.fill(self.bg_color)
            self.screen.blit(bg_surface, (x + offset_x, y + offset_y))
        
        for i in range(self.hotbar.num_slots):
            slot_x = x + i * (self.slot_size + self.slot_gap)
            slot_y = y + 10
            
            slot_rect = pygame.Rect(slot_x, slot_y, self.slot_size, self.slot_size)
            
            if not self.bg_image:
                pygame.draw.rect(self.screen, self.slot_color, slot_rect)
            
            if i == self.hotbar.selected_slot:
                pygame.draw.rect(self.screen, self.selected_color, slot_rect, 3)
            elif not self.bg_image:
                pygame.draw.rect(self.screen, self.border_color, slot_rect, 2)
            
            number_text = self.number_font.render(str(i + 1), True, ui_config.WHITE)
            number_rect = number_text.get_rect(centerx=slot_rect.centerx, bottom=slot_rect.top - 2)
            self.screen.blit(number_text, number_rect)
            
            slot_data = self.hotbar.get_slot(i)
            if slot_data:
                self.draw_item_in_slot(slot_data, slot_rect)
    
    def draw_item_in_slot(self, slot, rect):
        item = get_item(slot["item_id"])
        if not item:
            return

        item_image = load_item_image(slot["item_id"], self.slot_size)

        if item_image:
            self.screen.blit(item_image, item_image.get_rect(center=rect.center))
        else:
            name = ui_config.get_font(10).render(item.name[:6], True, ui_config.WHITE)
            self.screen.blit(name, name.get_rect(center=rect.center))

        if slot["quantity"] > 1:
            qty_text = str(slot["quantity"])
            qty = self.qty_font.render(qty_text, True, ui_config.WHITE)
            qty_shadow = self.qty_font.render(qty_text, True, (0, 0, 0))
            self.screen.blit(qty_shadow, (rect.right - 18, rect.bottom - 18))
            self.screen.blit(qty, (rect.right - 19, rect.bottom - 19))


class HealthBarUI(UIElement):
    def __init__(self, player, screen):
        super().__init__()
        self.player = player
        self.screen = screen
        self.visible = True
        
        self.bar_width = 200
        self.bar_height = 30
        self.padding = 5
        
        self.bg_color = (40, 40, 40)
        self.bar_color = (220, 50, 50)
        self.border_color = (100, 100, 100)
        
        self.font = ui_config.get_font(12)

    def show(self):
        self.visible = True
    
    def hide(self):
        self.visible = False
    
    def draw(self):
        if not self.visible:
            return
        
        x = self.screen.get_width() - self.bar_width - 20
        y = 180  # shifted down 50px to make room for IronOreCounterUI
        
        bg_rect = pygame.Rect(x, y, self.bar_width, self.bar_height)
        pygame.draw.rect(self.screen, self.bg_color, bg_rect)
        
        health_percent = self.player.current_health / self.player.max_health
        fill_width = int((self.bar_width - self.padding * 2) * health_percent)
        fill_rect = pygame.Rect(x + self.padding, y + self.padding, 
                                fill_width, self.bar_height - self.padding * 2)
        pygame.draw.rect(self.screen, self.bar_color, fill_rect)
        
        pygame.draw.rect(self.screen, self.border_color, bg_rect, 2)
        
        text = f"HP: {int(self.player.current_health)}/{int(self.player.max_health)}"
        text_surface = self.font.render(text, True, ui_config.WHITE)
        text_rect = text_surface.get_rect(center=(x + self.bar_width // 2, y + self.bar_height // 2))
        self.screen.blit(text_surface, text_rect)


class OxygenBarUI(UIElement):
    def __init__(self, player, screen):
        super().__init__()
        self.player = player
        self.screen = screen
        self.visible = True
        
        self.bar_width = 200
        self.bar_height = 30
        self.padding = 5
        
        self.bg_color = (40, 40, 40)
        self.bar_color = (50, 150, 220)
        self.border_color = (100, 100, 100)
        
        self.font = ui_config.get_font(12)

    def show(self):
        self.visible = True
    
    def hide(self):
        self.visible = False
    
    def draw(self):
        if not self.visible:
            return
        
        x = self.screen.get_width() - self.bar_width - 20
        y = 220  # shifted down 50px to make room for IronOreCounterUI
        
        bg_rect = pygame.Rect(x, y, self.bar_width, self.bar_height)
        pygame.draw.rect(self.screen, self.bg_color, bg_rect)
        
        oxygen_percent = self.player.current_oxygen / self.player.max_oxygen
        fill_width = int((self.bar_width - self.padding * 2) * oxygen_percent)
        fill_rect = pygame.Rect(x + self.padding, y + self.padding, 
                                fill_width, self.bar_height - self.padding * 2)
        pygame.draw.rect(self.screen, self.bar_color, fill_rect)
        
        pygame.draw.rect(self.screen, self.border_color, bg_rect, 2)
        
        text = f"O2: {int(self.player.current_oxygen)}/{int(self.player.max_oxygen)}"
        text_surface = self.font.render(text, True, ui_config.WHITE)
        text_rect = text_surface.get_rect(center=(x + self.bar_width // 2, y + self.bar_height // 2))
        self.screen.blit(text_surface, text_rect)


class HungerBarUI(UIElement):
    def __init__(self, player, screen):
        super().__init__()
        self.player = player
        self.screen = screen
        self.visible = True
        
        self.bar_width = 200
        self.bar_height = 30
        self.padding = 5
        
        self.bg_color = (40, 40, 40)
        self.bar_color = (220, 180, 50)
        self.border_color = (100, 100, 100)
        
        self.font = ui_config.get_font(12)

    def show(self):
        self.visible = True
    
    def hide(self):
        self.visible = False
    
    def draw(self):
        if not self.visible:
            return
        
        x = self.screen.get_width() - self.bar_width - 20
        y = 260  # shifted down 50px to make room for IronOreCounterUI
        
        bg_rect = pygame.Rect(x, y, self.bar_width, self.bar_height)
        pygame.draw.rect(self.screen, self.bg_color, bg_rect)
        
        hunger_percent = self.player.current_hunger / self.player.max_hunger
        fill_width = int((self.bar_width - self.padding * 2) * hunger_percent)
        fill_rect = pygame.Rect(x + self.padding, y + self.padding, 
                                fill_width, self.bar_height - self.padding * 2)
        pygame.draw.rect(self.screen, self.bar_color, fill_rect)
        
        pygame.draw.rect(self.screen, self.border_color, bg_rect, 2)
        
        text = f"Hunger: {int(self.player.current_hunger)}/{int(self.player.max_hunger)}"
        text_surface = self.font.render(text, True, ui_config.WHITE)
        text_rect = text_surface.get_rect(center=(x + self.bar_width // 2, y + self.bar_height // 2))
        self.screen.blit(text_surface, text_rect)


class OxygenWarningUI(UIElement):
    """Displays a pulsing 'OXYGEN LOW' warning at the top of the screen."""

    WARN_THRESHOLD = 20
    CRIT_THRESHOLD = 10

    def __init__(self, player, screen):
        super().__init__()
        self.player = player
        self.screen = screen
        self.visible = True

        self.font   = ui_config.get_font(70)
        self._pulse = 0.0
        self._vignette_surf = None  # Cached surface, rebuilt on resize

    def _draw_vignette(self, o2):
        """Red corner vignette that fades in from o2=15 down to full at o2=10."""

        VIGNETTE_START = 15
        VIGNETTE_FULL  = 10
        MAX_ALPHA      = 100   # 50% opacity at full strength

        if o2 >= VIGNETTE_START:
            return

        # t = 0.0 at o2=15, 1.0 at o2=10
        t = 1.0 - max(0.0, min(1.0, (o2 - VIGNETTE_FULL) / (VIGNETTE_START - VIGNETTE_FULL)))
        vignette_alpha = int(MAX_ALPHA * t)

        if vignette_alpha <= 0:
            return

        sw, sh = self.screen.get_size()

        # Rebuild cached surface only when screen size changes
        if self._vignette_surf is None or self._vignette_surf.get_size() != (sw, sh):
            surf = pygame.Surface((sw, sh), pygame.SRCALPHA)

            # Build vignette: concentric ellipses from edge (opaque) inward (transparent)
            steps = 80
            for i in range(steps, 0, -1):
                ratio = i / steps
                a     = int(255 * ratio)
                w     = int(sw * ratio * 1.5)  # Extend beyond edges for stronger corners
                h     = int(sh * ratio * 1.5)
                x     = (sw - w) // 2
                y     = (sh - h) // 2
                pygame.draw.ellipse(surf, (180, 0, 0, a), (x, y, w, h))

            # Punch a transparent hole in the centre so only the edges/corners glow
            cx_w = int(sw * 0.9)
            cx_h = int(sh * 0.9)
            cx   = (sw - cx_w) // 2
            cy   = (sh - cx_h) // 2
            pygame.draw.ellipse(surf, (0, 0, 0, 0), (cx, cy, cx_w, cx_h))

            self._vignette_surf = surf

        self._vignette_surf.set_alpha(vignette_alpha)
        self.screen.blit(self._vignette_surf, (0, 0))

    def draw(self, dt=0):
        import math
        o2 = self.player.current_oxygen

        # Vignette is independent — starts earlier than the text warning
        self._draw_vignette(o2)

        if o2 >= self.WARN_THRESHOLD:
            return

        if o2 < self.CRIT_THRESHOLD:
            base_color = (255, 0, 0)
        else:
            base_color = (220, 200, 50)

        self._pulse += dt * 4.0
        alpha = int(167 + 88 * math.sin(self._pulse))

        text_surf = self.font.render("OXYGEN LOW", True, base_color)
        text_rect = text_surf.get_rect(
            centerx=self.screen.get_width() // 2,
            top=80
        )

        # Apply alpha via a temporary surface so the font renders cleanly
        alpha_surf = pygame.Surface(text_surf.get_size(), pygame.SRCALPHA)
        alpha_surf.blit(text_surf, (0, 0))
        alpha_surf.set_alpha(alpha)

        self.screen.blit(alpha_surf, text_rect)


class PickupNotificationUI(UIElement):
    """Shows '+N item_name' toast notifications in the bottom-right corner."""

    DISPLAY_TIME = 2.5   # Seconds each notification stays visible
    FADE_TIME    = 0.5   # Seconds to fade out
    MAX_VISIBLE  = 5     # Max stacked notifications on screen

    def __init__(self, screen):
        super().__init__()
        self.screen = screen
        self.font   = ui_config.get_font(14)
        self._queue = []  # List of {text, timer, alpha}

    def notify(self, item_name, count):
        """Call this whenever an item is picked up."""
        text = f"+{count} {item_name}"

        # If the same item is already showing, just reset its timer
        for entry in self._queue:
            if entry["text"] == text:
                entry["timer"] = self.DISPLAY_TIME
                entry["alpha"] = 255
                return

        self._queue.append({"text": text, "timer": self.DISPLAY_TIME, "alpha": 255})

        # Keep only the most recent MAX_VISIBLE
        if len(self._queue) > self.MAX_VISIBLE:
            self._queue.pop(0)

    def update(self, dt):
        for entry in self._queue:
            entry["timer"] -= dt
            # Fade out during the last FADE_TIME seconds
            if entry["timer"] < self.FADE_TIME:
                entry["alpha"] = int(255 * max(0, entry["timer"] / self.FADE_TIME))

        self._queue = [e for e in self._queue if e["timer"] > 0]

    def draw(self):
        if not self._queue:
            return

        padding_right  = 20
        padding_bottom = 120   # Sits above the hotbar
        line_height    = 22

        for i, entry in enumerate(reversed(self._queue)):
            text_surf = self.font.render(entry["text"], True, (200, 200, 200))
            text_surf.set_alpha(entry["alpha"])

            x = self.screen.get_width()  - text_surf.get_width() - padding_right
            y = self.screen.get_height() - padding_bottom - i * line_height

            self.screen.blit(text_surf, (x, y))
