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


class NightOverlay:
    def __init__(self, clock_system, screen):
        self.clock = clock_system
        self.screen = screen

        self.max_alpha = 140  # how dark midnight is (tweak this)
        self.alpha = 0

        # Night color (bluish)
        self.surface = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        self.surface.fill((20, 30, 60))

    def update(self):
        hour = self.clock.hour
        minute = self.clock.minute
        self.alpha = self._calculate_alpha(hour, minute)

    def _calculate_alpha(self, hour, minute):
        time = hour + minute / 60.0

        # 16:00 → 00:00 (fade IN)
        if 16 <= time < 24:
            t = (time - 16) / 8.0   # 0 → 1
            return int(t * self.max_alpha)

        # 00:00 → 06:00 (fade OUT)
        if 0 <= time < 6:
            t = time / 6.0          # 0 → 1
            return int((1 - t) * self.max_alpha)

        # Daytime
        return 0

    def draw(self):
        if self.alpha <= 0:
            return

        self.surface.set_alpha(self.alpha)
        self.screen.blit(self.surface, (0, 0))
