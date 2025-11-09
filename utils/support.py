from os import walk
import pygame

def import_folder(path):
    images = []
    for _, __, img_files in walk(path):
        for image in img_files:
            full_path = path + '/' + image
            image_surface = pygame.image.load(full_path).convert_alpha()
            images.append(image_surface)
    return images
