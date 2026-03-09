import pygame
import random
from utils.support import resource_path

class AmbientMusicSystem:
    def __init__(self):
        self.tracks = [
            "assets/music/ambient1.ogg",
            "assets/music/ambient2.ogg",
            "assets/music/ambient3.ogg",
        ]
        self.min_silence = 60_000
        self.max_silence = 180_000
        self.volume = 0.4
        self.enabled = True
        self.next_play_time = pygame.time.get_ticks() + random.randint(
            self.min_silence, self.max_silence
        )

    def update(self):
        if not self.enabled or pygame.mixer.music.get_busy():
            return
        if pygame.time.get_ticks() >= self.next_play_time:
            track = resource_path(random.choice(self.tracks))
            pygame.mixer.music.load(track)
            pygame.mixer.music.set_volume(self.volume)
            pygame.mixer.music.play()
            track_length = int(pygame.mixer.Sound(track).get_length() * 1000)
            self.next_play_time = (
                pygame.time.get_ticks()
                + track_length
                + random.randint(self.min_silence, self.max_silence)
            )

    def stop(self):
        pygame.mixer.music.stop()
        self.enabled = False

    def resume(self):
        self.enabled = True
        # Reset timer so it doesn't play immediately on resume
        self.next_play_time = pygame.time.get_ticks() + random.randint(
            self.min_silence // 2, self.min_silence
        )