import pygame
from items import get_item
from ui.ui_config import ui_config
from utils.support import resource_path, load_item_image

class ChestUI:
    def __init__(self, screen, player_inventory, chest_inventory, player_hotbar):
        self.screen = screen
        self.player_inventory = player_inventory
        self.player_hotbar = player_hotbar
        self.chest_inventory = chest_inventory
        self.visible = True

        self.slot_size = 64
        self.padding = 13
        self.cols = 6
        self.rows = 6

        self.dragging = False
        self.drag_source_inventory = None
        self.drag_source_slot = None

        self.font = ui_config.get_font(16)
        self.title_font = ui_config.get_font(24)
        self.item_font = ui_config.get_font(12)
        self.qty_font = ui_config.get_font(16)

        # Load background images
        self.inventory_bg_image = ui_config.get_image('inventory_bg')
        self.chest_bg_image = ui_config.get_image('chest_bg')

        # Load hotbar background image
        self.hotbar_bg_image = None
        try:
            raw = pygame.image.load(resource_path("assets/ui/hotbar_bg.png")).convert_alpha()
            # Scale to fit the 9-slot row
            hotbar_row_w = self.player_hotbar.num_slots * (self.slot_size + self.padding) - self.padding + 40
            hotbar_row_h = self.slot_size + 20
            self.hotbar_bg_image = pygame.transform.scale(
                raw,
                (hotbar_row_w + 30, hotbar_row_h + 10)
            )
        except FileNotFoundError:
            self.hotbar_bg_image = None

        self.panel_width = 600
        self.panel_height = 600
        
        # Scale background images if they exist
        if self.inventory_bg_image:
            self.player_bg_scaled = pygame.transform.scale(self.inventory_bg_image, (self.panel_width, self.panel_height))
        else:
            self.player_bg_scaled = None

        if self.chest_bg_image:
            self.chest_bg_scaled = pygame.transform.scale(self.chest_bg_image, (self.panel_width, self.panel_height))
        else:
            self.chest_bg_scaled = self.player_bg_scaled

        self.player_panel = pygame.Rect(0, 0, self.panel_width, self.panel_height)
        self.chest_panel  = pygame.Rect(0, 0, self.panel_width, self.panel_height)

        self.update_panel_positions()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def update_panel_positions(self):
        sw = self.screen.get_width()
        sh = self.screen.get_height()
        spacing   = 40
        total_w   = self.panel_width * 2 + spacing
        start_x   = (sw - total_w) // 2
        center_y  = (sh - self.panel_height) // 2

        self.player_panel.x = start_x
        self.player_panel.y = center_y
        self.chest_panel.x  = start_x + self.panel_width + spacing
        self.chest_panel.y  = center_y

    def close(self):
        self.visible = False

    # ------------------------------------------------------------------
    # Slot rect helpers
    # ------------------------------------------------------------------

    def get_slot_rect(self, panel, index):
        row = index // self.cols
        col = index % self.cols
        x = panel.x + 70 + col * (self.slot_size + self.padding)
        y = panel.y + 70 + row * (self.slot_size + self.padding)
        return pygame.Rect(x, y, self.slot_size, self.slot_size)

    def get_hotbar_slot_rect(self, index):
        """Hotbar row sits inside the player panel near the bottom."""
        slots_w = self.player_hotbar.num_slots * (self.slot_size + self.padding) - self.padding
        start_x = self.player_panel.x + (self.panel_width - slots_w) // 2
        y = self.player_panel.y + self.panel_height - self.slot_size + 80
        x = start_x + index * (self.slot_size + self.padding)
        return pygame.Rect(x, y, self.slot_size, self.slot_size)

    def get_slot_at_pos(self, pos, panel, inventory):
        for i in range(inventory.size):
            if self.get_slot_rect(panel, i).collidepoint(pos):
                return i
        return None

    # ------------------------------------------------------------------
    # Drag & drop
    # ------------------------------------------------------------------

    def start_drag(self, inventory, slot_index):
        self.dragging = True
        self.drag_source_inventory = inventory
        self.drag_source_slot = slot_index

    def cancel_drag(self):
        self.dragging = False
        self.drag_source_inventory = None
        self.drag_source_slot = None

    def handle_mouse_down(self, pos):
        if not self.visible:
            return

        # Hotbar row (inside player panel)
        for i in range(self.player_hotbar.num_slots):
            if self.get_hotbar_slot_rect(i).collidepoint(pos):
                if self.player_hotbar.get_slot(i):
                    self.start_drag(self.player_hotbar, i)
                return

        # Player inventory
        slot = self.get_slot_at_pos(pos, self.player_panel, self.player_inventory)
        if slot is not None and self.player_inventory.get_slot(slot):
            self.start_drag(self.player_inventory, slot)
            return

        # Chest inventory
        slot = self.get_slot_at_pos(pos, self.chest_panel, self.chest_inventory)
        if slot is not None and self.chest_inventory.get_slot(slot):
            self.start_drag(self.chest_inventory, slot)

    def handle_mouse_up(self, pos):
        if not self.dragging:
            return

        source      = self.drag_source_inventory
        source_slot = self.drag_source_slot
        slot_data   = source.get_slot(source_slot)

        if not slot_data:
            self.cancel_drag()
            return

        # Drop onto hotbar row
        for i in range(self.player_hotbar.num_slots):
            if self.get_hotbar_slot_rect(i).collidepoint(pos):
                self.try_drop(source, self.player_hotbar, source_slot, i)
                self.cancel_drag()
                return

        # Drop onto player inventory
        target = self.get_slot_at_pos(pos, self.player_panel, self.player_inventory)
        if target is not None:
            self.try_drop(source, self.player_inventory, source_slot, target)
            self.cancel_drag()
            return

        # Drop onto chest inventory
        target = self.get_slot_at_pos(pos, self.chest_panel, self.chest_inventory)
        if target is not None:
            self.try_drop(source, self.chest_inventory, source_slot, target)
            self.cancel_drag()
            return

        self.cancel_drag()

    def try_drop(self, source, target, from_slot, to_slot):
        from_data = source.get_slot(from_slot)
        to_data   = target.get_slot(to_slot)

        if to_data is None:
            target.set_slot(to_slot, from_data)
            source.set_slot(from_slot, None)
            return

        if from_data["item_id"] == to_data["item_id"]:
            item  = get_item(from_data["item_id"])
            space = item.max_stack - to_data["quantity"]
            if space > 0:
                moved = min(space, from_data["quantity"])
                to_data["quantity"]   += moved
                from_data["quantity"] -= moved
                if from_data["quantity"] <= 0:
                    source.set_slot(from_slot, None)
            return

        # Swap
        source.set_slot(from_slot, to_data)
        target.set_slot(to_slot, from_data)

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw_item_in_slot(self, slot, rect, alpha=255):
        item = get_item(slot["item_id"])
        if not item:
            return

        item_image = load_item_image(slot["item_id"], self.slot_size)

        if item_image:
            image_rect = item_image.get_rect(center=rect.center)
            if alpha < 255:
                temp = item_image.copy()
                temp.set_alpha(alpha)
                self.screen.blit(temp, image_rect)
            else:
                self.screen.blit(item_image, image_rect)
        else:
            name_text = item.name[:6] + ".." if len(item.name) > 8 else item.name
            name = self.item_font.render(name_text, True, ui_config.WHITE)
            self.screen.blit(name, (rect.x + 4, rect.y + 4))

        qty_text = str(slot["quantity"])
        qty = self.qty_font.render(qty_text, True, ui_config.WHITE)
        self.screen.blit(qty, (rect.right - 22, rect.bottom - 22))

    def draw_panel(self, panel, title, inventory, bg_image):
        if bg_image:
            self.screen.blit(bg_image, (panel.x, panel.y))
        else:
            pygame.draw.rect(self.screen, ui_config.DARK_GRAY, panel)
            pygame.draw.rect(self.screen, ui_config.WHITE, panel, 2)
            title_surf = self.title_font.render(title, True, ui_config.WHITE)
            self.screen.blit(title_surf, title_surf.get_rect(centerx=panel.centerx, y=panel.y + 15))

        for i in range(inventory.size):
            if self.dragging and self.drag_source_inventory is inventory and i == self.drag_source_slot:
                continue
            rect = self.get_slot_rect(panel, i)
            if not bg_image:
                pygame.draw.rect(self.screen, ui_config.DARK_GRAY, rect)
                pygame.draw.rect(self.screen, ui_config.WHITE, rect, 1)
            slot = inventory.get_slot(i)
            if slot:
                self.draw_item_in_slot(slot, rect)

    def draw(self):
        if not self.visible:
            return

        self.update_panel_positions()
        self.draw_panel(self.player_panel, "INVENTORY", self.player_inventory, self.player_bg_scaled)
        self.draw_panel(self.chest_panel,  "CHEST",     self.chest_inventory,  self.chest_bg_scaled)

        # Hotbar row inside player panel
        if self.hotbar_bg_image:
            hotbar_rect = self.hotbar_bg_image.get_rect(
                centerx=self.player_panel.centerx,
                y=self.player_panel.bottom - self.slot_size + 60
            )
            self.screen.blit(self.hotbar_bg_image, hotbar_rect)

        for i in range(self.player_hotbar.num_slots):
            rect = self.get_hotbar_slot_rect(i)
            if not self.hotbar_bg_image:
                pygame.draw.rect(self.screen, (50, 50, 50), rect)
                pygame.draw.rect(self.screen, (100, 100, 100), rect, 2)
                if i == self.player_hotbar.selected_slot:
                    pygame.draw.rect(self.screen, (255, 255, 255), rect, 2)
            slot = self.player_hotbar.get_slot(i)
            if slot and not (self.dragging and self.drag_source_inventory is self.player_hotbar and self.drag_source_slot == i):
                self.draw_item_in_slot(slot, rect)

        # Dragged item follows mouse
        if self.dragging and self.drag_source_slot is not None:
            slot = self.drag_source_inventory.get_slot(self.drag_source_slot)
            if slot:
                mx, my = pygame.mouse.get_pos()
                drag_rect = pygame.Rect(0, 0, self.slot_size, self.slot_size)
                drag_rect.center = (mx, my)
                self.draw_item_in_slot(slot, drag_rect, alpha=200)
