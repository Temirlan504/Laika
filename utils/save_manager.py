import json
import os
from datetime import datetime
from pathlib import Path
from utils.support import resource_path

class SaveManager:
    """
    Centralized save/load system for the game.
    Handles player data, world state, greenhouses, and buildings.
    """
    
    def __init__(self, save_directory=None):
        if save_directory is None:
            save_directory = os.path.join(os.getenv('APPDATA', '.'), 'Laika', 'saves')
        self.save_directory = Path(save_directory)
        self.save_directory.mkdir(parents=True, exist_ok=True)
        
    def get_save_slots(self):
        """Get list of available save slots with metadata"""
        slots = []
        for i in range(1, 4):  # 3 save slots
            slot_file = self.save_directory / f"save_slot_{i}.json"
            if slot_file.exists():
                try:
                    with open(slot_file, 'r') as f:
                        data = json.load(f)
                        slots.append({
                            'slot': i,
                            'exists': True,
                            'timestamp': data.get('metadata', {}).get('timestamp', 'Unknown'),
                            'day': data.get('world', {}).get('day', 0),
                            'playtime': data.get('metadata', {}).get('playtime', 0)
                        })
                except Exception as e:
                    print(f"Error reading save slot {i}: {e}")
                    slots.append({'slot': i, 'exists': False})
            else:
                slots.append({'slot': i, 'exists': False})
        return slots
    
    def save_game(self, game, slot=1):
        self.current_slot = slot
        
        # Ensure save directory exists
        self.save_directory.mkdir(exist_ok=True)
        
        try:
            save_data = {
                'metadata': self._save_metadata(game),
                'player': self._save_player(game.player),
                'world': self._save_world(game),
                'greenhouses': self._save_greenhouses(game),
                'buildings': self._save_buildings(game),
                'death_chests': self._save_death_chests(game)
            }
            
            # Write to file
            slot_file = self.save_directory / f"save_slot_{slot}.json"
            with open(slot_file, 'w') as f:
                json.dump(save_data, f, indent=2)
            
            print(f"Game saved to slot {slot}")
            return True
            
        except Exception as e:
            print(f"Error saving game: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def load_game(self, game, slot=1):
        """
        Load game state from a JSON file.
        
        Args:
            game: Main game object to populate
            slot: Save slot number (1-3)
        
        Returns:
            bool: True if load succeeded, False otherwise
        """
        self.current_slot = slot
        slot_file = self.save_directory / f"save_slot_{slot}.json"
        
        if not slot_file.exists():
            print(f"Save slot {slot} does not exist")
            return False
        
        try:
            with open(slot_file, 'r') as f:
                save_data = json.load(f)
            
            # Load in order: world first, then player, then structures
            self._load_world(game, save_data.get('world', {}))
            self._load_player(game.player, save_data.get('player', {}))
            self._load_greenhouses(game, save_data.get('greenhouses', {}))
            
            # Store buildings data for later loading (after level state is created)
            game._pending_buildings = save_data.get('buildings', [])
            game._pending_death_chests = save_data.get('death_chests', [])
            
            print(f"Game loaded from slot {slot}")
            return True
            
        except Exception as e:
            print(f"Error loading game: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def delete_save(self, slot):
        """Delete a save slot"""
        slot_file = self.save_directory / f"save_slot_{slot}.json"
        if slot_file.exists():
            os.remove(slot_file)
            print(f"Deleted save slot {slot}")
            return True
        return False
    
    # ==================== SAVE METHODS ====================
    
    def _save_metadata(self, game):
        """Save metadata about the save file"""
        return {
            'version': '1.0',
            'timestamp': datetime.now().isoformat(),
            'playtime': getattr(game, 'playtime', 0)  # You can track this if needed
        }
    
    def _save_player(self, player):
        """Save player state"""
        return {
            'position': {
                'x': player.rect.centerx,
                'y': player.rect.centery
            },
            'health': player.current_health,
            'hunger': player.current_hunger,
            'oxygen': player.current_oxygen,
            'max_health': player.max_health,
            'max_hunger': player.max_hunger,
            'max_oxygen': player.max_oxygen,
            'selected_tool': player.selected_tool,
            'selected_seed': player.selected_seed,
            'inventory': player.inventory.serialize(),
            'hotbar': player.hotbar.serialize()  # This is correct
        }
    
    def _save_world(self, game):
        """Save world state (time, day, etc.)"""
        return {
            'day': game.day_cycle.day,
            'time': {
                'hour': game.clock_system.hour,
                'minute': game.clock_system.minute
            }
        }
    
    def _save_greenhouses(self, game):
        """Save all greenhouse data"""
        greenhouses = {}
        
        for greenhouse_id, greenhouse_data in game.greenhouse_data.items():
            soil_data = {}
            
            # Save each soil plot
            for pos_key, soil_info in greenhouse_data.get('soil', {}).items():
                # Convert tuple keys to string format "x,y"
                if isinstance(pos_key, tuple):
                    str_key = f"{pos_key[0]},{pos_key[1]}"
                else:
                    str_key = str(pos_key)
                
                # Serialize plant object if it exists
                plant_data = None
                plant = soil_info.get('plant')
                if plant is not None:
                    plant_data = {
                        'plant_type': plant.plant_type,
                        'growth_stage': plant.growth_stage
                    }
                
                # Soil data matches what greenhouse.py expects:
                # {'state': ..., 'plant': ...}
                soil_data[str_key] = {
                    'state': soil_info.get('state', 'empty'),
                    'plant': plant_data
                }
            
            # Save chest data if it exists (greenhouse.py uses 'chests' plural)
            chests_data = {}
            if 'chests' in greenhouse_data:
                # Save all chests for this greenhouse
                for chest_id, chest_inventory in greenhouse_data['chests'].items():
                    chests_data[chest_id] = chest_inventory
            
            greenhouses[greenhouse_id] = {
                'soil': soil_data,
                'chests': chests_data
            }
        
        return greenhouses
    
    def _save_buildings(self, game):
        """Save placed buildings (domes)"""
        buildings = []
        
        # Access the level state to get dome sprites
        level_state = game.state_machine.state_instances.get('level')
        if level_state and hasattr(level_state, 'dome_sprites'):
            for dome in level_state.dome_sprites:
                buildings.append({
                    'type': 'greenhouse_dome',
                    'greenhouse_id': dome.greenhouse_id,
                    'position': {
                        'x': dome.rect.centerx,
                        'y': dome.rect.centery
                    }
                })
        
        return buildings
    
    def _save_death_chests(self, game):
        """Save all death chest data including position and inventory."""
        if not hasattr(game, 'death_chests'):
            return []

        result = []
        level_state = game.state_machine.state_instances.get('level')
        if not level_state:
            return result

        # Find each chest sprite to get its world position
        chest_sprites = {}
        if hasattr(level_state, 'all_sprites'):
            from sprites import DeathChest
            for sprite in level_state.all_sprites:
                if isinstance(sprite, DeathChest) and hasattr(sprite, 'chest_id'):
                    chest_sprites[sprite.chest_id] = sprite

        for chest_id, chest in game.death_chests.items():
            sprite = chest_sprites.get(chest_id)
            if not sprite:
                continue
            result.append({
                'chest_id': chest_id,
                'position': {
                    'x': sprite.rect.centerx,
                    'y': sprite.rect.centery
                },
                'inventory': chest.serialize()
            })

        return result


    # ==================== LOAD METHODS ====================
    
    def _load_player(self, player, data):
        """Load player state"""
        if not data:
            return
        
        # Position
        pos = data.get('position', {})
        if pos:
            player.rect.centerx = pos.get('x', player.rect.centerx)
            player.rect.centery = pos.get('y', player.rect.centery)
            player.hitbox.center = player.rect.center
        
        # Stats
        player.current_health = data.get('health', player.max_health)
        player.current_hunger = data.get('hunger', player.max_hunger)
        player.current_oxygen = data.get('oxygen', player.max_oxygen)
        player.max_health = data.get('max_health', 100)
        player.max_hunger = data.get('max_hunger', 100)
        player.max_oxygen = data.get('max_oxygen', 100)
        
        # Tools
        player.selected_tool = data.get('selected_tool', 'pickaxe')
        player.selected_seed = data.get('selected_seed', 'potato_seed')
        
        # Inventory
        inventory_data = data.get('inventory', [])
        if inventory_data:
            player.inventory.deserialize(inventory_data)
        
        # Hotbar - FIXED: Only pass the data, not the key name
        hotbar_data = data.get('hotbar', [None] * 9)
        player.hotbar.deserialize(hotbar_data)
    
    def _load_world(self, game, data):
        """Load world state"""
        if not data:
            return
        
        # Day
        game.day_cycle.day = data.get('day', 0)
        
        # Time
        time_data = data.get('time', {})
        if time_data:
            hour = time_data.get('hour', 6)
            minute = time_data.get('minute', 0)
            game.clock_system.set_time(hour, minute)
    
    def _load_greenhouses(self, game, data):
        """Load all greenhouse data"""
        if not data:
            return
        
        from greenhouse.plant import Plant
        
        for greenhouse_id_str, greenhouse_info in data.items():
            # Convert string ID back to integer if it's a number
            try:
                greenhouse_id = int(greenhouse_id_str)
            except ValueError:
                greenhouse_id = greenhouse_id_str
            
            # Initialize greenhouse in game data if not exists
            if greenhouse_id not in game.greenhouse_data:
                game.greenhouse_data[greenhouse_id] = {'soil': {}}
            
            # Load soil data
            soil_data = greenhouse_info.get('soil', {})
            for pos_key, soil_info in soil_data.items():
                # Convert string key back to tuple if needed (format: "x,y")
                if ',' in str(pos_key):
                    parts = pos_key.split(',')
                    actual_key = (int(parts[0]), int(parts[1]))
                else:
                    actual_key = pos_key
                
                # Recreate Plant object from saved data
                plant = None
                plant_data = soil_info.get('plant')
                if plant_data is not None:
                    plant = Plant(plant_data['plant_type'])
                    plant.growth_stage = plant_data.get('growth_stage', 0)
                
                game.greenhouse_data[greenhouse_id]['soil'][actual_key] = {
                    'state': soil_info.get('state', 'empty'),
                    'plant': plant
                }
            
            # Load chests data (greenhouse.py uses 'chests' plural)
            chests_data = greenhouse_info.get('chests', {})
            if chests_data:
                game.greenhouse_data[greenhouse_id]['chests'] = chests_data
    
    def _load_buildings(self, game, data):
        """Load placed buildings"""
        if not data:
            return
        
        import pygame
        from sprites import GreenhouseDome
        from building.door import DoorInteractionZone
        
        # Get the level state
        level_state = game.state_machine.state_instances.get('level')
        if not level_state:
            print("Warning: Cannot load buildings, level state not found")
            return
        
        # Load dome image
        dome_image = pygame.image.load(resource_path("assets/dome.png")).convert_alpha()
        dome_image = pygame.transform.scale(dome_image, (612, 429))
        
        # Spawn each building
        for building_data in data:
            if building_data.get('type') == 'greenhouse_dome':
                pos = building_data.get('position', {})
                center_x = pos.get('x', 0)
                center_y = pos.get('y', 0)
                greenhouse_id = building_data.get('greenhouse_id')
                
                # Convert greenhouse_id to integer if it's stored as a string
                if isinstance(greenhouse_id, str) and greenhouse_id.isdigit():
                    greenhouse_id = int(greenhouse_id)
                
                # Create the dome
                dome = GreenhouseDome(
                    center_pos=(center_x, center_y),
                    image=dome_image,
                    groups=[
                        level_state.all_sprites,
                        level_state.collision_sprites,
                        level_state.dome_sprites
                    ]
                )
                
                # Override the auto-generated ID with the saved one
                dome.greenhouse_id = greenhouse_id
                
                # Create door interaction zone
                door_world_pos = (
                    pygame.Vector2(dome.rect.center) + dome.door_offset
                )
                door_rect = pygame.Rect(0, 0, 96, 48)
                door_rect.center = door_world_pos
                
                zone = DoorInteractionZone(
                    rect=door_rect,
                    owner=dome,
                    text="Press E to Enter"
                )
                level_state.interaction_zones.add(zone)
                
                print(f"Loaded greenhouse dome at ({center_x}, {center_y})")
    
    def _load_death_chests(self, game, data):
        """Restore death chests into the world."""
        if not data:
            return

        import pygame
        from sprites import DeathChest
        from greenhouse.chest import Chest

        level_state = game.state_machine.state_instances.get('level')
        if not level_state:
            print("[WARN] Cannot load death chests — level state not found")
            return

        if not hasattr(game, 'death_chests'):
            game.death_chests = {}

        for entry in data:
            chest_id = entry['chest_id']
            pos = entry['position']
            center = (pos['x'], pos['y'])

            # Recreate chest with saved inventory
            chest = Chest(chest_id)
            chest.load(entry.get('inventory'))
            game.death_chests[chest_id] = chest

            # Spawn the sprite
            chest_sprite = DeathChest(
                pos=center,
                groups=[level_state.all_sprites, level_state.collision_sprites]
            )
            chest_sprite.chest_id = chest_id

            # Register interaction zone
            zone_rect = pygame.Rect(0, 0, 96, 48)
            zone_rect.center = center
            level_state._register_death_chest_zone(chest_sprite, zone_rect)

            print(f"[LOAD] Death chest '{chest_id}' restored at {center}")
    
    def load_pending_buildings(self, game):
        """Load buildings that were deferred during game load"""
        if hasattr(game, '_pending_buildings'):
            buildings_data = game._pending_buildings
            self._load_buildings(game, buildings_data)
            del game._pending_buildings
            print(f"Loaded {len(buildings_data)} pending buildings")
        
        if hasattr(game, '_pending_death_chests'):
            death_chests_data = game._pending_death_chests
            self._load_death_chests(game, death_chests_data)
            del game._pending_death_chests
            print(f"Loaded {len(death_chests_data)} pending death chests")
    
    def auto_save(self, game):
        """Perform an auto-save (uses slot 0 as auto-save slot)"""
        return self.save_game(game, slot=0)
    
    def has_auto_save(self):
        """Check if auto-save exists"""
        auto_save_file = self.save_directory / "save_slot_0.json"
        return auto_save_file.exists()
