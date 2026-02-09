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

        self.font = ui_config.get_font(16)

        self.player_panel = pygame.Rect(100, 100, 320, 300)
        self.chest_panel  = pygame.Rect(460, 100, 320, 300)

    def close(self):
        self.visible = False

    # ----------------- INPUT -----------------

    def handle_mouse_click(self, pos):
        if not self.visible:
            return

        # Player → Chest
        slot = self.get_slot_at_pos(pos, self.player_panel, self.player_inventory)
        if slot is not None:
            self.transfer(self.player_inventory, self.chest_inventory, slot)
            return

        # Chest → Player
        slot = self.get_slot_at_pos(pos, self.chest_panel, self.chest_inventory)
        if slot is not None:
            self.transfer(self.chest_inventory, self.player_inventory, slot)

    def transfer(self, source, target, index):
        slot = source.get_slot(index)
        if not slot:
            return

        if target.add_item(slot["item_id"], slot["quantity"]):
            source.set_slot(index, None)

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
