import argparse
import json
import os
import random
from typing import Dict, List, Tuple

SECTORS: Dict[str, Tuple[float, float]] = {
    "F-6": (33.7269, 73.0671),
    "F-7": (33.7294, 73.0536),
    "F-8": (33.6932, 73.0323),
    "F-10": (33.6996, 73.0192),
    "F-11": (33.7152, 73.0102),
    "E-11": (33.7015, 72.9984),
    "G-8": (33.6719, 73.0432),
    "G-9": (33.6880, 73.0236),
    "G-10": (33.6766, 73.0136),
    "G-11": (33.6647, 73.0125),
    "H-8": (33.6640, 73.0780),
    "H-9": (33.6457, 73.0780),
    "H-10": (33.6560, 73.0910),
    "I-8": (33.6505, 73.1066),
    "I-9": (33.6403, 73.0925),
    "I-10": (33.6327, 73.0817),
    "Blue Area": (33.7154, 73.0734),
    "Saddar": (33.5951, 73.0616),
    "Commercial Market": (33.7214, 73.0602),
    "Bahria Town": (33.5400, 73.1200),
    "DHA": (33.5567, 73.0703),
    "Giga Mall": (33.5408, 73.1214),
    "Rawalpindi Cantt": (33.6074, 73.0660),
    "Kartarpura": (33.6126, 73.0679),
    "PWD": (33.5714, 73.1098),
    "Soan Garden": (33.5498, 73.1086),
    "Chaklala": (33.6203, 73.1027),
    "Bani Gala": (33.7238, 73.1536),
    "G-6": (33.7216, 73.0739),
    "G-7": (33.7078, 73.0510),
}

UNIVERSITIES = [
    "NUST H-12",
    "FAST H-11",
    "COMSATS Park Road",
    "Quaid-i-Azam University",
    "Bahria University E-8",
    "Air University E-9",
    "IIUI H-10",
]

MEAL_TYPES = [
    "Biryani",
    "Karahi",
    "Burger",
    "Roll",
    "Wrap",
    "Pulao",
    "Nihari",
    "Tikka",
    "BBQ Platter",
    "Pasta",
    "Pizza",
    "Shawarma",
    "Paratha",
    "Sandwich",
    "Daal Bowl",
    "Samosa Chaat",
    "Dahi Bhallay",
    "Chana Chaat",
    "Fried Chicken",
    "Grilled Fish",
    "Kebab",
    "Loaded Fries",
    "Lassi",
    "Fresh Juice",
    "Falooda",
]

ADJECTIVES = [
    "Spicy",
    "Smoky",
    "Signature",
    "Classic",
    "Special",
    "Royal",
    "House",
    "Street",
    "Zesty",
    "Mint",
    "Butter",
    "Crispy",
    "Creamy",
    "Loaded",
]

OUTLETS = [
    "Cafe",
    "Kitchen",
    "Eatery",
    "Corner",
    "Spot",
    "Dhaba",
    "Bistro",
    "Stall",
    "House",
    "Grill",
]

IMAGE_URLS = [
    "https://images.unsplash.com/photo-1563379091339-03b21bc4a4f8?q=80&w=400",
    "https://images.unsplash.com/photo-1513104890138-7c749659a591?q=80&w=400",
    "https://images.unsplash.com/photo-1633945274405-b6c8069047b0?q=80&w=400",
    "https://images.unsplash.com/photo-1550547660-d9450f859349?q=80&w=400",
    "https://images.unsplash.com/photo-1603894584214-5d30baf39446?q=80&w=400",
    "https://images.unsplash.com/photo-1596797038530-2c39bb9ed0b1?q=80&w=400",
    "https://images.unsplash.com/photo-1589113103503-49453adfd15d?q=80&w=400",
    "https://images.unsplash.com/photo-1521390188846-e2a3a97453a0?q=80&w=400",
]

DESCRIPTIONS = [
    "A crowd favorite with bold flavors and generous portions.",
    "Budget-friendly and filling, ideal for students.",
    "Served fresh with house-made sauces and sides.",
    "Slow-cooked and spiced for a rich, comforting taste.",
    "Light, flavorful, and perfect for a quick bite.",
    "A popular pick with a loyal local following.",
]


def jitter_coords(lat: float, lng: float) -> Tuple[float, float]:
    lat_offset = random.uniform(-0.004, 0.004)
    lng_offset = random.uniform(-0.004, 0.004)
    return round(lat + lat_offset, 6), round(lng + lng_offset, 6)


def make_name() -> str:
    adj = random.choice(ADJECTIVES)
    meal = random.choice(MEAL_TYPES)
    outlet = random.choice(OUTLETS)
    return f"{adj} {meal} {outlet}"


def make_price(meal: str) -> int:
    base = {
        "Biryani": (220, 550),
        "Karahi": (800, 1600),
        "Burger": (180, 550),
        "Roll": (150, 400),
        "Wrap": (200, 450),
        "Pulao": (250, 600),
        "Nihari": (400, 900),
        "Tikka": (300, 700),
        "BBQ Platter": (800, 1600),
        "Pasta": (450, 900),
        "Pizza": (650, 1800),
        "Shawarma": (180, 450),
        "Paratha": (120, 320),
        "Sandwich": (180, 450),
        "Daal Bowl": (150, 350),
        "Samosa Chaat": (140, 280),
        "Dahi Bhallay": (140, 280),
        "Chana Chaat": (140, 280),
        "Fried Chicken": (350, 950),
        "Grilled Fish": (600, 1500),
        "Kebab": (250, 700),
        "Loaded Fries": (220, 550),
        "Lassi": (120, 250),
        "Fresh Juice": (120, 300),
        "Falooda": (200, 450),
    }
    for key, (low, high) in base.items():
        if key in meal:
            return random.randint(low, high)
    return random.randint(200, 800)


def make_location() -> Tuple[str, float, float]:
    if random.random() < 0.2:
        area = random.choice(UNIVERSITIES)
        sector_key = "H-10"
    else:
        area = random.choice(list(SECTORS.keys()))
        sector_key = area

    base_lat, base_lng = SECTORS.get(sector_key, SECTORS["F-8"])
    lat, lng = jitter_coords(base_lat, base_lng)

    if area in UNIVERSITIES:
        location = f"{area}, Islamabad"
    else:
        suffix = "Islamabad" if area not in ["Saddar", "Rawalpindi Cantt", "Kartarpura"] else "Rawalpindi"
        location = f"{area} Markaz, {suffix}" if "-" in area else f"{area}, {suffix}"

    return location, lat, lng


def build_dataset(count: int) -> List[Dict[str, object]]:
    dataset: List[Dict[str, object]] = []
    seen = set()

    while len(dataset) < count:
        name = make_name()
        if name in seen:
            continue
        seen.add(name)

        location, lat, lng = make_location()
        price = make_price(name)

        dataset.append(
            {
                "name": name,
                "price": price,
                "location": location,
                "description": random.choice(DESCRIPTIONS),
                "image_url": random.choice(IMAGE_URLS),
                "latitude": lat,
                "longitude": lng,
            }
        )

    return dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a meals dataset for Foodly.")
    parser.add_argument("--count", type=int, default=200, help="Number of meals to generate.")
    parser.add_argument(
        "--output",
        type=str,
        default=os.path.join(os.path.dirname(__file__), "data", "islamabad_meals.json"),
        help="Output JSON path.",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducible output.")
    args = parser.parse_args()

    random.seed(args.seed)
    dataset = build_dataset(args.count)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(dataset, handle, indent=2, ensure_ascii=True)

    print(f"Wrote {len(dataset)} meals to {args.output}")


if __name__ == "__main__":
    main()
