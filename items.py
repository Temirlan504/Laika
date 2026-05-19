"""
Item definitions for the game.
Each item has: name, type, max_stack, description, and optional properties.
"""

class ItemType:
    RESOURCE = "resource"
    TOOL = "tool"
    SEED = "seed"
    FOOD = "food"
    MATERIAL = "material"

class Item:
    def __init__(self, item_id, name, item_type, max_stack=64, description="", **kwargs):
        self.id = item_id
        self.name = name
        self.type = item_type
        self.max_stack = max_stack
        self.description = description
        
        # Optional properties
        for key, value in kwargs.items():
            setattr(self, key, value)

# Item database
ITEMS = {
    # Resources
    "iron_ore": Item(
        "iron_ore",
        "Iron Ore",
        ItemType.RESOURCE,
        max_stack=64,
        description="Raw iron ore from meteorites"
    ),
    "ice_shard": Item(
        "ice_shard",
        "Ice Shard",
        ItemType.RESOURCE,
        max_stack=64,
        description="A crystalline shard chipped from a frozen glacier"
    ),
    
    # Seeds
    "potato_seed": Item(
        "potato_seed",
        "Potato Seed",
        ItemType.SEED,
        max_stack=64,
        description="Plant these in tilled soil",
        plant_type="potato"
    ),
    "tomato_seed": Item(
        "tomato_seed",
        "Tomato Seed",
        ItemType.SEED,
        max_stack=64,
        description="Plant these in tilled soil",
        plant_type="tomato"
    ),
    "carrot_seed": Item(
        "carrot_seed",
        "Carrot Seed",
        ItemType.SEED,
        max_stack=64,
        description="Plant these in tilled soil",
        plant_type="carrot"
    ),
    
    # Food
    "potato": Item(
        "potato",
        "Potato",
        ItemType.FOOD,
        max_stack=64,
        description="Restores hunger",
        hunger_restore=20,
        health_restore=5
    ),
    "tomato": Item(
        "tomato",
        "Tomato",
        ItemType.FOOD,
        max_stack=64,
        description="Restores hunger",
        hunger_restore=15,
        health_restore=3
    ),
    "carrot": Item(
        "carrot",
        "Carrot",
        ItemType.FOOD,
        max_stack=64,
        description="Restores hunger",
        hunger_restore=10,
        health_restore=2
    ),
    
    # Tools (non-stackable)
    "hoe": Item(
        "hoe",
        "Hoe",
        ItemType.TOOL,
        max_stack=1,
        description="Till soil for planting"
    ),
    "pickaxe": Item(
        "pickaxe",
        "Pickaxe",
        ItemType.TOOL,
        max_stack=1,
        description="Mine meteorites for resources"
    ),
    "watering_can": Item(
        "watering_can",
        "Watering Can",
        ItemType.TOOL,
        max_stack=1,
        description="Water your crops"
    )
}

def get_item(item_id):
    """Get item definition by ID"""
    return ITEMS.get(item_id)
