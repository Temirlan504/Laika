import pygame
from utils.settings import LAYERS
from greenhouse.plant import Plant
from utils.timer import Timer

class SoilTile(pygame.sprite.Sprite):
    def __init__(self, rect, groups, z_index=LAYERS['ground']):
        super().__init__(groups)
        self.rect = rect
        self.image = pygame.Surface(rect.size, pygame.SRCALPHA)
        self.z_index = z_index

        self.state = "dry"
        self.plant = None

        # Timer for plant growth (in milliseconds)
        self.growth_timer = Timer(1500000000, self.advance_plant)

    def hoe(self):
        if self.state == "dry" :
            print("HOE")
            self.state = "hoed"
            self.update_visual()

    def water(self):
        if self.state == "hoed":
            print("WATER")
            self.state = "watered"
            self.update_visual()

    def plant_seed(self):
        if self.state == "watered" and self.plant is None:
            print("PLANTED SEED")
            self.plant = Plant("test_crop")
            self.update_visual()
            self.growth_timer.activate()

    def advance_plant(self):
        if self.plant and self.state == "watered":
            self.plant.grow()
            self.update_visual()

            # continue growing until fully grown
            if not self.plant.is_fully_grown:
                self.growth_timer.activate()

    def update_visual(self):
        self.image.fill((0, 0, 0, 0))  # clear

        if self.state == "hoed":
            pygame.draw.rect(self.image, (120, 90, 50), self.image.get_rect())

        elif self.state == "watered":
            pygame.draw.rect(self.image, (60, 80, 120), self.image.get_rect())

        # 🌱 planted seed placeholder
        if self.plant:
            center = self.image.get_rect().center

            if self.plant.growth_stage == 0:
                self.image.set_at(center, (0, 255, 0))  # seed
            elif self.plant.growth_stage == 1:
                pygame.draw.circle(self.image, (0, 200, 0), center, 2)
            elif self.plant.growth_stage == 2:
                pygame.draw.circle(self.image, (0, 180, 0), center, 4)
            elif self.plant.growth_stage == 3:
                pygame.draw.circle(self.image, (0, 150, 0), center, 6)

    def update(self):
        self.growth_timer.update()

class SoilLayer:
    def __init__(self, soil_sprites):
        self.soil_sprites = soil_sprites

    def get_tile_at_pos(self, pos):
        for soil in self.soil_sprites:
            if soil.rect.collidepoint(pos):
                return soil
        return None

    def handle_event(self, event_type, pos):
        soil = self.get_tile_at_pos(pos)
        if soil is None:
            return

        if event_type == 'hoe':
            soil.hoe()
        elif event_type == 'water':
            soil.water()
        elif event_type == 'plant':
            soil.plant_seed()
