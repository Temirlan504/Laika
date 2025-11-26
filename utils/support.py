from os import walk
import pygame
from utils.settings import TILE_SIZE

def import_folder(path):
    images = []
    for _, __, img_files in walk(path):
        for image in img_files:
            full_path = path + '/' + image
            image_surface = pygame.image.load(full_path).convert_alpha()
            image_surface = pygame.transform.scale(image_surface, (TILE_SIZE, TILE_SIZE))
            images.append(image_surface)
    return images
