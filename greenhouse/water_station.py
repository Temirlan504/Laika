import pygame

# 1 shard = 1 ml, max = 5,000 ml (5 L)
WATER_MAX_ML = 5_000
SHARD_TO_ML = 5 # 1 ice shard == 5 ml
WATERING_CAN_FILL_ML = 1_000   # how many ml fill the can per refill action


class WaterBar:
    """
    A simple rectangular progress bar drawn at a fixed screen position.
    Position is set from a Tiled marker (water_station_bar) via set_pos().
    """

    BAR_W  = 80
    BAR_H  = 10
    BG_COL    = (40,  40,  60)
    FILL_COL  = (60, 130, 210)
    BORDER_COL = (180, 200, 230)

    def __init__(self):
        self._world_pos = None   # set once map is loaded

    def set_world_pos(self, x, y):
        """Store the world-space centre of the bar marker."""
        self._world_pos = (x, y)

    def draw(self, screen, water_ml, camera_offset):
        if self._world_pos is None:
            return

        wx, wy = self._world_pos
        sx = wx - camera_offset.x - self.BAR_W // 2
        sy = wy - camera_offset.y - self.BAR_H // 2

        # Background
        bg_rect = pygame.Rect(sx, sy, self.BAR_W, self.BAR_H)
        pygame.draw.rect(screen, self.BG_COL, bg_rect, border_radius=3)

        # Fill
        fill_w = int(self.BAR_W * (water_ml / WATER_MAX_ML))
        if fill_w > 0:
            fill_rect = pygame.Rect(sx, sy, fill_w, self.BAR_H)
            pygame.draw.rect(screen, self.FILL_COL, fill_rect, border_radius=3)

        # Border
        pygame.draw.rect(screen, self.BORDER_COL, bg_rect, width=1, border_radius=3)

        # Label  (e.g. "4200 ml")
        font = pygame.font.SysFont(None, 14)
        label = font.render(f"{water_ml} ml", True, (220, 230, 255))
        screen.blit(label, (sx, sy - 14))


class WaterStation:
    def __init__(self):
        self.water_ml: int = 0
        self.bar = WaterBar()

    # ------------------------------------------------------------------
    # Marker position (called by greenhouse.py after map load)
    # ------------------------------------------------------------------
    def set_bar_pos(self, x, y):
        self.bar.set_world_pos(x, y)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def deposit_shards(self, player) -> int:
        """
        Remove every ice_shard from inventory + hotbar and add water.
        Returns the number of ml added (0 if nothing deposited).
        """
        total_shards = 0

        # Count + remove from inventory
        inv_count = player.inventory.get_total("ice_shard")
        if inv_count:
            player.inventory.remove_item("ice_shard", inv_count)
            total_shards += inv_count

        # Count + remove from hotbar
        for i, slot in enumerate(player.hotbar.slots):
            if slot and slot["item_id"] == "ice_shard":
                total_shards += slot["quantity"]
                player.hotbar.slots[i] = None

        if total_shards == 0:
            print("[WATER] No ice shards to deposit.")
            return 0

        ml_added = total_shards * SHARD_TO_ML
        self.water_ml = min(WATER_MAX_ML, self.water_ml + ml_added)
        print(f"[WATER] Deposited {total_shards} shards → +{ml_added} ml  (tank: {self.water_ml} ml)")
        return ml_added

    def fill_watering_can(self, player) -> bool:
        item_id = player.hotbar.get_selected_item_id()
        if item_id != "watering_can":
            print("[WATER] Select your watering can first.")
            return False
 
        if self.water_ml <= 0:
            print("[WATER] Tank is empty!")
            return False
 
        space = player.watering_can_max_ml - player.watering_can_ml
        if space <= 0:
            print("[WATER] Watering can is already full.")
            return False
 
        drawn = min(space, self.water_ml)
        self.water_ml          -= drawn
        player.watering_can_ml += drawn
        print(
            f"[WATER] Can filled +{drawn} ml  "
            f"(can: {player.watering_can_ml}/{player.watering_can_max_ml} ml | "
            f"tank: {self.water_ml} ml)"
        )
        return True

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------
    def draw(self, screen, camera_offset):
        self.bar.draw(screen, self.water_ml, camera_offset)
