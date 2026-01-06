# utils/fade_effect.py
import pygame

class FadeEffect:
    def __init__(self, screen, speed=300):
        self.screen = screen
        self.speed = speed  # alpha per second

        self.alpha = 0
        self.target_alpha = 0
        self.active = False

        self.surface = pygame.Surface(screen.get_size())
        self.surface.fill((0, 0, 0))
        self.surface.set_alpha(self.alpha)

        self.on_fade_in_complete = None
        self.on_fade_out_complete = None

    def fade_in(self, callback=None):
        self.target_alpha = 255
        self.active = True
        self.on_fade_in_complete = callback

    def fade_out(self, callback=None):
        self.target_alpha = 0
        self.active = True
        self.on_fade_out_complete = callback

    def update(self, dt):
        if not self.active:
            return

        if self.alpha < self.target_alpha:
            self.alpha += self.speed * dt
            if self.alpha >= self.target_alpha:
                self.alpha = self.target_alpha
                self.active = False
                if self.target_alpha == 255 and self.on_fade_in_complete:
                    self.on_fade_in_complete()

        elif self.alpha > self.target_alpha:
            self.alpha -= self.speed * dt
            if self.alpha <= self.target_alpha:
                self.alpha = self.target_alpha
                self.active = False
                if self.target_alpha == 0 and self.on_fade_out_complete:
                    self.on_fade_out_complete()

        self.surface.set_alpha(int(self.alpha))

    def draw(self):
        if self.alpha > 0:
            self.screen.blit(self.surface, (0, 0))

    @property
    def blocking(self):
        return self.active or self.alpha > 0
