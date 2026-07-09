"""
Dish Dataset — the 14 flavor dimensions and the 40-dish catalog.

Every other module imports DIMENSIONS/DIM_LABELS from here, so this is the
single source of truth for dish/vector shape.
"""

# Canonical dimension order. Every flavor vector (dish or target) is a dict
# keyed by these 14 strings — order here only matters for vec(...) below.
DIMENSIONS = [
    "spice", "acidity", "richness", "warmth", "crunch", "umami", "sweetness",
    "bitterness", "saltiness", "freshness", "moisture", "aroma", "chewiness",
    "temp_contrast",
]

DIM_LABELS = {
    "spice": "Spice",
    "acidity": "Acidity",
    "richness": "Richness",
    "warmth": "Warmth",
    "crunch": "Crunch",
    "umami": "Umami",
    "sweetness": "Sweetness",
    "bitterness": "Bitterness",
    "saltiness": "Saltiness",
    "freshness": "Freshness",
    "moisture": "Juiciness",
    "aroma": "Aroma",
    "chewiness": "Chewiness",
    "temp_contrast": "Temp Contrast",
}


def vec(*values):
    """Builds a flavor-vector dict from 14 positional 0-10 scores, in DIMENSIONS order."""
    return dict(zip(DIMENSIONS, values))


DISHES = [
    # North Indian
    {"id": "butter-chicken", "name": "Butter Chicken", "cuisine": "North Indian", "prep_time_minutes": 35, "meal_type": ["lunch", "dinner"], "vector": vec(5, 4, 9, 8, 1, 8, 4, 0, 6, 1, 7, 8, 3, 0)},
    {"id": "paneer-tikka", "name": "Paneer Tikka", "cuisine": "North Indian", "prep_time_minutes": 25, "meal_type": ["snack", "dinner"], "vector": vec(6, 3, 6, 8, 5, 6, 1, 1, 5, 2, 4, 8, 5, 0)},
    {"id": "chole-bhature", "name": "Chole Bhature", "cuisine": "North Indian", "prep_time_minutes": 40, "meal_type": ["breakfast", "lunch"], "vector": vec(7, 4, 8, 8, 4, 6, 1, 1, 6, 1, 5, 7, 5, 0)},
    {"id": "dal-makhani", "name": "Dal Makhani", "cuisine": "North Indian", "prep_time_minutes": 45, "meal_type": ["lunch", "dinner"], "vector": vec(3, 2, 9, 8, 0, 7, 2, 0, 5, 1, 7, 6, 2, 0)},
    {"id": "rogan-josh", "name": "Rogan Josh", "cuisine": "North Indian", "prep_time_minutes": 50, "meal_type": ["dinner"], "vector": vec(7, 3, 8, 9, 0, 8, 1, 1, 6, 1, 6, 9, 5, 0)},

    # South Indian
    {"id": "masala-dosa", "name": "Masala Dosa", "cuisine": "South Indian", "prep_time_minutes": 20, "meal_type": ["breakfast"], "vector": vec(4, 3, 4, 7, 7, 5, 1, 0, 5, 2, 3, 6, 3, 0)},
    {"id": "idli-sambar", "name": "Idli Sambar", "cuisine": "South Indian", "prep_time_minutes": 15, "meal_type": ["breakfast"], "vector": vec(3, 4, 2, 7, 1, 5, 1, 1, 4, 4, 6, 5, 2, 0)},
    {"id": "chettinad-chicken", "name": "Chettinad Chicken Curry", "cuisine": "South Indian", "prep_time_minutes": 45, "meal_type": ["lunch", "dinner"], "vector": vec(9, 4, 7, 9, 0, 8, 0, 2, 6, 1, 6, 9, 5, 0)},
    {"id": "rava-upma", "name": "Rava Upma", "cuisine": "South Indian", "prep_time_minutes": 15, "meal_type": ["breakfast"], "vector": vec(3, 1, 3, 7, 3, 3, 1, 0, 4, 3, 3, 4, 2, 0)},
    {"id": "medu-vada", "name": "Medu Vada", "cuisine": "South Indian", "prep_time_minutes": 20, "meal_type": ["breakfast", "snack"], "vector": vec(4, 2, 5, 7, 7, 4, 0, 0, 5, 2, 2, 5, 4, 0)},

    # Chinese
    {"id": "hakka-noodles", "name": "Hakka Noodles", "cuisine": "Chinese", "prep_time_minutes": 20, "meal_type": ["lunch", "dinner"], "vector": vec(5, 3, 5, 7, 4, 7, 2, 0, 7, 2, 4, 6, 5, 0)},
    {"id": "veg-manchurian", "name": "Veg Manchurian", "cuisine": "Chinese", "prep_time_minutes": 25, "meal_type": ["snack", "dinner"], "vector": vec(6, 4, 5, 7, 6, 7, 3, 0, 6, 2, 4, 6, 4, 0)},
    {"id": "chilli-chicken", "name": "Chilli Chicken", "cuisine": "Chinese", "prep_time_minutes": 25, "meal_type": ["snack", "dinner"], "vector": vec(8, 5, 6, 8, 6, 8, 2, 0, 7, 1, 4, 7, 5, 0)},
    {"id": "veg-fried-rice", "name": "Veg Fried Rice", "cuisine": "Chinese", "prep_time_minutes": 20, "meal_type": ["lunch", "dinner"], "vector": vec(3, 2, 4, 7, 3, 6, 1, 0, 6, 3, 3, 5, 3, 0)},
    {"id": "hot-sour-soup", "name": "Hot and Sour Soup", "cuisine": "Chinese", "prep_time_minutes": 15, "meal_type": ["snack"], "vector": vec(6, 7, 3, 8, 2, 6, 1, 1, 5, 3, 8, 6, 1, 0)},

    # Italian
    {"id": "margherita-pizza", "name": "Margherita Pizza", "cuisine": "Italian", "prep_time_minutes": 20, "meal_type": ["lunch", "dinner"], "vector": vec(2, 4, 6, 7, 4, 6, 2, 0, 5, 3, 4, 6, 5, 0)},
    {"id": "penne-arrabbiata", "name": "Penne Arrabbiata", "cuisine": "Italian", "prep_time_minutes": 20, "meal_type": ["lunch", "dinner"], "vector": vec(6, 6, 5, 7, 1, 6, 2, 1, 5, 3, 5, 6, 4, 0)},
    {"id": "fettuccine-alfredo", "name": "Fettuccine Alfredo", "cuisine": "Italian", "prep_time_minutes": 20, "meal_type": ["dinner"], "vector": vec(1, 1, 9, 7, 0, 6, 1, 0, 5, 1, 6, 5, 4, 0)},
    {"id": "bruschetta", "name": "Bruschetta", "cuisine": "Italian", "prep_time_minutes": 15, "meal_type": ["snack"], "vector": vec(1, 6, 2, 3, 6, 4, 2, 0, 4, 8, 4, 6, 2, 0)},
    {"id": "minestrone-soup", "name": "Minestrone Soup", "cuisine": "Italian", "prep_time_minutes": 30, "meal_type": ["lunch", "dinner"], "vector": vec(2, 4, 3, 7, 1, 5, 2, 1, 4, 5, 8, 4, 2, 0)},

    # Continental
    {"id": "grilled-chicken-steak", "name": "Grilled Chicken Steak", "cuisine": "Continental", "prep_time_minutes": 30, "meal_type": ["dinner"], "vector": vec(3, 2, 6, 8, 2, 7, 1, 1, 5, 2, 5, 6, 5, 0)},
    {"id": "caesar-salad", "name": "Caesar Salad", "cuisine": "Continental", "prep_time_minutes": 15, "meal_type": ["lunch"], "vector": vec(1, 5, 5, 2, 7, 5, 1, 2, 5, 8, 3, 4, 3, 0)},
    {"id": "mushroom-soup", "name": "Mushroom Soup", "cuisine": "Continental", "prep_time_minutes": 25, "meal_type": ["snack"], "vector": vec(1, 1, 6, 8, 0, 6, 1, 1, 4, 2, 8, 5, 1, 0)},
    {"id": "fish-and-chips", "name": "Fish and Chips", "cuisine": "Continental", "prep_time_minutes": 30, "meal_type": ["lunch", "dinner"], "vector": vec(2, 3, 7, 7, 8, 6, 1, 0, 6, 2, 4, 5, 3, 0)},
    {"id": "roasted-veg-platter", "name": "Roasted Vegetable Platter", "cuisine": "Continental", "prep_time_minutes": 30, "meal_type": ["lunch", "dinner"], "vector": vec(2, 2, 3, 7, 4, 4, 2, 2, 3, 6, 4, 5, 3, 0)},

    # Fast Food
    {"id": "cheese-burger", "name": "Cheese Burger", "cuisine": "Fast Food", "prep_time_minutes": 15, "meal_type": ["lunch", "dinner", "snack"], "vector": vec(2, 3, 8, 7, 4, 7, 2, 0, 6, 2, 5, 6, 5, 0)},
    {"id": "french-fries", "name": "French Fries", "cuisine": "Fast Food", "prep_time_minutes": 15, "meal_type": ["snack"], "vector": vec(1, 0, 6, 7, 8, 3, 1, 0, 6, 1, 2, 4, 2, 0)},
    {"id": "chicken-nuggets", "name": "Chicken Nuggets", "cuisine": "Fast Food", "prep_time_minutes": 15, "meal_type": ["snack"], "vector": vec(2, 1, 6, 7, 7, 5, 1, 0, 5, 1, 3, 4, 4, 0)},
    {"id": "loaded-nachos", "name": "Loaded Nachos", "cuisine": "Fast Food", "prep_time_minutes": 15, "meal_type": ["snack"], "vector": vec(6, 4, 7, 7, 7, 6, 1, 0, 6, 2, 3, 5, 3, 0)},
    {"id": "veg-frankie", "name": "Veg Frankie", "cuisine": "Fast Food", "prep_time_minutes": 15, "meal_type": ["snack", "lunch"], "vector": vec(5, 3, 5, 6, 5, 4, 1, 0, 5, 3, 3, 5, 4, 0)},

    # Desserts
    {"id": "gulab-jamun", "name": "Gulab Jamun", "cuisine": "Desserts", "prep_time_minutes": 10, "meal_type": ["dessert"], "vector": vec(0, 0, 7, 6, 0, 0, 10, 0, 0, 0, 7, 6, 3, 0)},
    {"id": "chocolate-brownie", "name": "Chocolate Brownie", "cuisine": "Desserts", "prep_time_minutes": 10, "meal_type": ["dessert"], "vector": vec(0, 0, 8, 4, 2, 0, 9, 2, 1, 0, 5, 7, 5, 0)},
    {"id": "tiramisu", "name": "Tiramisu", "cuisine": "Desserts", "prep_time_minutes": 10, "meal_type": ["dessert"], "vector": vec(0, 1, 8, 2, 1, 0, 8, 2, 0, 1, 6, 6, 2, 0)},
    {"id": "ice-cream-sundae", "name": "Ice Cream Sundae", "cuisine": "Desserts", "prep_time_minutes": 5, "meal_type": ["dessert"], "vector": vec(0, 1, 7, 1, 2, 0, 9, 0, 0, 3, 6, 4, 1, 6)},
    {"id": "rasmalai", "name": "Rasmalai", "cuisine": "Desserts", "prep_time_minutes": 10, "meal_type": ["dessert"], "vector": vec(0, 0, 6, 3, 0, 0, 9, 0, 0, 2, 8, 6, 1, 0)},

    # Beverages
    {"id": "masala-chai", "name": "Masala Chai", "cuisine": "Beverages", "prep_time_minutes": 5, "meal_type": ["beverage"], "vector": vec(3, 0, 4, 9, 0, 0, 5, 2, 0, 1, 9, 8, 0, 0)},
    {"id": "cold-coffee", "name": "Cold Coffee", "cuisine": "Beverages", "prep_time_minutes": 5, "meal_type": ["beverage"], "vector": vec(0, 1, 6, 1, 0, 0, 6, 4, 0, 3, 9, 6, 0, 0)},
    {"id": "mango-lassi", "name": "Mango Lassi", "cuisine": "Beverages", "prep_time_minutes": 5, "meal_type": ["beverage"], "vector": vec(0, 2, 5, 2, 0, 0, 7, 0, 0, 5, 9, 6, 0, 0)},
    {"id": "nimbu-pani", "name": "Nimbu Pani", "cuisine": "Beverages", "prep_time_minutes": 5, "meal_type": ["beverage"], "vector": vec(1, 8, 0, 1, 0, 0, 4, 0, 2, 9, 9, 3, 0, 0)},
    {"id": "iced-lemon-tea", "name": "Iced Lemon Tea", "cuisine": "Beverages", "prep_time_minutes": 5, "meal_type": ["beverage"], "vector": vec(0, 5, 1, 1, 0, 0, 4, 1, 0, 7, 9, 4, 0, 0)},
]
