import os
import sys
import pygame
from utils.settings import TILE_SIZE

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        base = sys._MEIPASS
    else:
        # Go up one level from utils/ to reach project root
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative_path)

def import_folder(path):
    images = []
    abs_path = resource_path(path)
    for _, __, img_files in os.walk(abs_path):
        for image in sorted(img_files):          # sorted = consistent frame order
            full_path = os.path.join(abs_path, image)
            image_surface = pygame.image.load(full_path).convert_alpha()
            image_surface = pygame.transform.scale(image_surface, (TILE_SIZE, TILE_SIZE))
            images.append(image_surface)
    return images

# Shared item image cache across all UI files
_item_image_cache: dict[str, pygame.Surface] = {}

def load_item_image(item_id: str, slot_size: int) -> pygame.Surface | None:
    cache_key = f"{item_id}_{slot_size}"
    if cache_key in _item_image_cache:
        return _item_image_cache[cache_key]

    possible_paths = [
        f"assets/items/{item_id}.png",
        f"assets/items/tools/{item_id}.png",
        f"assets/items/seeds/{item_id}.png",
        f"assets/items/crops/{item_id}.png",
        f"assets/items/resources/{item_id}.png",
    ]
    image_size = int(slot_size * 0.7)
    _item_image_cache[cache_key] = None
    for path in possible_paths:
        try:
            img = pygame.image.load(resource_path(path)).convert_alpha()
            _item_image_cache[cache_key] = pygame.transform.scale(img, (image_size, image_size))
            break
        except FileNotFoundError:
            continue
        except Exception as e:
            print(f"[ITEM_IMAGE] Error loading {path}: {e}")
    return _item_image_cache[cache_key]