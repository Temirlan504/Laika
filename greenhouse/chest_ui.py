import pygame
from ui.ui_config import ui_config

class ChestUI:
    def __init__(self, screen, player_inventory, chest_inventory):
        self.screen = screen
        self.player_inventory = player_inventory
        self.chest_inventory = chest_inventory
        self.visible = True

        self.slot_size = 48
        self.padding = 6
        self.cols = 6

        self.dragging = False
        self.drag_source_inventory = None
        self.drag_source_slot = None

        self.font = ui_config.get_font(16)

        self.player_panel = pygame.Rect(100, 100, 320, 300)
        self.chest_panel  = pygame.Rect(460, 100, 320, 300)

    def close(self):
        self.visible = False

    # ----------------- SLOT HELPERS -----------------

    def get_slot_at_pos(self, pos, panel, inventory):
        for i in range(inventory.size):
            rect = self.get_slot_rect(panel, i)
            if rect.collidepoint(pos):
                return i
        return None

    def get_slot_rect(self, panel, index):
        row = index // self.cols
        col = index % self.cols

        x = panel.x + 10 + col * (self.slot_size + self.padding)
        y = panel.y + 40 + row * (self.slot_size + self.padding)

        return pygame.Rect(x, y, self.slot_size, self.slot_size)
    
    
    # ----------------- DRAG & DROP -----------------
    def handle_mouse_down(self, pos):
        if not self.visible:
            return

        # Player inventory
        slot = self.get_slot_at_pos(pos, self.player_panel, self.player_inventory)
        if slot is not None:
            if self.player_inventory.get_slot(slot):
                self.start_drag(self.player_inventory, slot)
                return

        # Chest inventory
        slot = self.get_slot_at_pos(pos, self.chest_panel, self.chest_inventory)
        if slot is not None:
            if self.chest_inventory.get_slot(slot):
                self.start_drag(self.chest_inventory, slot)

    def start_drag(self, inventory, slot_index):
        self.dragging = True
        self.drag_source_inventory = inventory
        self.drag_source_slot = slot_index

    def handle_mouse_up(self, pos):
        if not self.dragging:
            return

        source = self.drag_source_inventory
        source_slot = self.drag_source_slot
        slot_data = source.get_slot(source_slot)

        if not slot_data:
            self.cancel_drag()
            return

        # Drop onto player inventory
        target_slot = self.get_slot_at_pos(pos, self.player_panel, self.player_inventory)
        if target_slot is not None:
            self.try_drop(source, self.player_inventory, source_slot, target_slot)
            self.cancel_drag()
            return

        # Drop onto chest inventory
        target_slot = self.get_slot_at_pos(pos, self.chest_panel, self.chest_inventory)
        if target_slot is not None:
            self.try_drop(source, self.chest_inventory, source_slot, target_slot)
            self.cancel_drag()
            return

        # Dropped nowhere → cancel
        self.cancel_drag()

    def try_drop(self, source, target, from_slot, to_slot):
        from_data = source.get_slot(from_slot)
        to_data = target.get_slot(to_slot)

        # Empty target → move
        if to_data is None:
            target.set_slot(to_slot, from_data)
            source.set_slot(from_slot, None)
            return

        # Same item → stack
        if from_data["item_id"] == to_data["item_id"]:
            from items import get_item
            item = get_item(from_data["item_id"])
            space = item.max_stack - to_data["quantity"]
            if space > 0:
                moved = min(space, from_data["quantity"])
                to_data["quantity"] += moved
                from_data["quantity"] -= moved
                if from_data["quantity"] <= 0:
                    source.set_slot(from_slot, None)
                return

        # Otherwise → swap
        source.set_slot(from_slot, to_data)
        target.set_slot(to_slot, from_data)

    def cancel_drag(self):
        self.dragging = False
        self.drag_source_inventory = None
        self.drag_source_slot = None

    # ----------------- DRAW -----------------

    def draw_panel(self, panel, title, inventory):
        pygame.draw.rect(self.screen, ui_config.BLACK, panel)
        pygame.draw.rect(self.screen, ui_config.WHITE, panel, 2)

        title_surf = self.font.render(title, True, ui_config.WHITE)
        self.screen.blit(title_surf, (panel.x + 10, panel.y + 10))

        for i in range(inventory.size):
            rect = self.get_slot_rect(panel, i)
            pygame.draw.rect(self.screen, ui_config.DARK_GRAY, rect)
            pygame.draw.rect(self.screen, ui_config.WHITE, rect, 1)

            slot = inventory.get_slot(i)
            if slot:
                txt = self.font.render(
                    f"{slot['item_id']} x{slot['quantity']}",
                    True,
                    ui_config.WHITE
                )
                self.screen.blit(txt, (rect.x + 4, rect.y + 4))

    def draw(self):
        if not self.visible:
            return

        self.draw_panel(self.player_panel, "INVENTORY", self.player_inventory)
        self.draw_panel(self.chest_panel, "CHEST", self.chest_inventory)

        if self.dragging:
            slot = self.drag_source_inventory.get_slot(self.drag_source_slot)
            if slot:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                txt = self.font.render(
                    f"{slot['item_id']} x{slot['quantity']}",
                    True,
                    ui_config.WHITE
                )
                bg = txt.get_rect(center=(mouse_x, mouse_y))
                pygame.draw.rect(self.screen, ui_config.BLACK, bg.inflate(6, 6))
                self.screen.blit(txt, bg)
