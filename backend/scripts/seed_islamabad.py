"""
Seed 200+ real Islamabad/Rawalpindi meals with Gemini embeddings.

Usage (from backend/ directory):
    python -m scripts.seed_islamabad
    python scripts/seed_islamabad.py
"""
import sys
import os
import time

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from google import genai
from google.genai.types import EmbedContentConfig
from app.core.database import SessionLocal
from app.models.meal import Meal

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    print("ERROR: GOOGLE_API_KEY not set in .env")
    sys.exit(1)

client = genai.Client(api_key=GOOGLE_API_KEY)
EMBEDDING_MODEL = "text-embedding-004"
EMBEDDING_DIM = 1536

# Image pools by food type (Unsplash)
IMG = {
    "biryani":    "https://images.unsplash.com/photo-1563379091339-03b21bc4a4f8?q=80&w=400",
    "karahi":     "https://images.unsplash.com/photo-1603894584214-5d30baf39446?q=80&w=400",
    "nihari":     "https://images.unsplash.com/photo-1545243424-0ce743321e11?q=80&w=400",
    "burger":     "https://images.unsplash.com/photo-1550547660-d9450f859349?q=80&w=400",
    "pizza":      "https://images.unsplash.com/photo-1513104890138-7c749659a591?q=80&w=400",
    "chai":       "https://images.unsplash.com/photo-1571115177098-24ec42ed204d?q=80&w=400",
    "pulao":      "https://images.unsplash.com/photo-1633945274405-b6c8069047b0?q=80&w=400",
    "kabab":      "https://images.unsplash.com/photo-1544025162-d76694265947?q=80&w=400",
    "paratha":    "https://images.unsplash.com/photo-1589811520-5f0e4a97abf8?q=80&w=400",
    "pasta":      "https://images.unsplash.com/photo-1555949258-eb67b1ef0ceb?q=80&w=400",
    "shawarma":   "https://images.unsplash.com/photo-1565299585323-38d6b0865b47?q=80&w=400",
    "breakfast":  "https://images.unsplash.com/photo-1533089860892-a7c6f0a88666?q=80&w=400",
    "fish":       "https://images.unsplash.com/photo-1519984388953-d2406bc725e1?q=80&w=400",
    "rice":       "https://images.unsplash.com/photo-1516714435131-44d6b64dc6a2?q=80&w=400",
    "sweet":      "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?q=80&w=400",
    "coffee":     "https://images.unsplash.com/photo-1509042239860-f550ce710b93?q=80&w=400",
    "sandwich":   "https://images.unsplash.com/photo-1528735602780-2552fd46c7af?q=80&w=400",
    "wrap":       "https://images.unsplash.com/photo-1565299507177-b0ac66763828?q=80&w=400",
    "daal":       "https://images.unsplash.com/photo-1585937421612-70a008356fbe?q=80&w=400",
    "haleem":     "https://images.unsplash.com/photo-1574484284002-952d92456975?q=80&w=400",
}

# fmt: off
MEALS = [
    # ── F-7 Markaz & Supermarket (33.7196, 73.0729) ─────────────────────────
    {"name": "Monal Peshwari Karahi", "price": 1800, "location": "Monal Restaurant, F-7, Islamabad", "description": "Tender mutton cooked in butter with tomatoes, ginger julienne, and green chillies. Islamabad's iconic rooftop karahi with panoramic views.", "image_url": IMG["karahi"], "latitude": 33.7200, "longitude": 73.0731},
    {"name": "Burns Road Nihari", "price": 600, "location": "Bundu Khan, F-7 Markaz, Islamabad", "description": "Slow-cooked beef nihari simmered overnight, topped with ginger strips, fried onions, and lemon. Authentic Karachi-style recipe.", "image_url": IMG["nihari"], "latitude": 33.7193, "longitude": 73.0722},
    {"name": "KFC Zinger Burger", "price": 650, "location": "KFC, F-7 Markaz, Islamabad", "description": "Crispy fried chicken fillet with lettuce and mayo in a sesame bun. KFC's signature hot and spicy coating.", "image_url": IMG["burger"], "latitude": 33.7198, "longitude": 73.0735},
    {"name": "Nandos Quarter Chicken", "price": 950, "location": "Nandos, F-7 Markaz, Islamabad", "description": "Flame-grilled quarter chicken marinated in Nando's signature PERi-PERi sauce, served with peri-salted chips.", "image_url": IMG["karahi"], "latitude": 33.7194, "longitude": 73.0728},
    {"name": "Hardee's Thickburger", "price": 790, "location": "Hardee's, F-7 Markaz, Islamabad", "description": "100% Angus beef patty with natural casing bacon, aged cheddar, lettuce, tomato, and mayo. No shortcuts on quality.", "image_url": IMG["burger"], "latitude": 33.7197, "longitude": 73.0730},
    {"name": "Charcoal BBQ Seekh Kabab", "price": 450, "location": "Charcoal BBQ, F-7, Islamabad", "description": "Minced beef and lamb mixed with spices, hand-shaped on skewers and grilled over charcoal. Served with mint raita.", "image_url": IMG["kabab"], "latitude": 33.7201, "longitude": 73.0725},
    {"name": "Pizza Hut Pepperoni", "price": 1350, "location": "Pizza Hut, F-7, Islamabad", "description": "Classic hand-tossed pepperoni pizza with mozzarella cheese and tomato sauce. A universal crowd-pleaser.", "image_url": IMG["pizza"], "latitude": 33.7192, "longitude": 73.0720},
    {"name": "Gloria Jean's Cappuccino", "price": 450, "location": "Gloria Jean's Coffees, F-7, Islamabad", "description": "Rich espresso topped with velvety steamed milk foam. A smooth, balanced cup to start the day right.", "image_url": IMG["coffee"], "latitude": 33.7196, "longitude": 73.0733},
    {"name": "Tuscany Courtyard Pasta", "price": 1200, "location": "Tuscany Courtyard, F-7, Islamabad", "description": "Al dente penne in a creamy rosé sauce with grilled chicken and sun-dried tomatoes. Islamabad's favourite Italian.", "image_url": IMG["pasta"], "latitude": 33.7199, "longitude": 73.0727},
    {"name": "Lal Qila Chicken Karahi", "price": 1100, "location": "Lal Qila Restaurant, F-7, Islamabad", "description": "Tender chicken pieces tossed in a tomato-onion masala with green chillies and coriander. Rich and aromatic.", "image_url": IMG["karahi"], "latitude": 33.7195, "longitude": 73.0726},
    {"name": "Street Side Paratha Roll", "price": 150, "location": "Paratha Wala, F-7 Supermarket, Islamabad", "description": "Flaky desi ghee paratha rolled with chicken tikka filling, sliced onions, and tangy tamarind chutney.", "image_url": IMG["paratha"], "latitude": 33.7191, "longitude": 73.0729},
    {"name": "Howdy's Beef Burger", "price": 550, "location": "Howdy's, F-7, Islamabad", "description": "Smashed beef patty with caramelised onions, special sauce, and pickles on a brioche bun. Street-style gourmet.", "image_url": IMG["burger"], "latitude": 33.7202, "longitude": 73.0724},
    {"name": "Shalimar Restaurant Haleem", "price": 400, "location": "Shalimar Restaurant, F-7, Islamabad", "description": "Thick wheat and lentil haleem slow-cooked with beef shank. Garnished with crispy fried onions and lemon.", "image_url": IMG["haleem"], "latitude": 33.7188, "longitude": 73.0731},
    {"name": "Kuch Khas Shinwari Karahi", "price": 1300, "location": "Kuch Khas, F-7, Islamabad", "description": "Namkeen shinwari-style karahi with minimal spices, letting the fresh mutton flavour shine through.", "image_url": IMG["karahi"], "latitude": 33.7205, "longitude": 73.0728},
    {"name": "Zaiqa Daal Makhni", "price": 350, "location": "Zaiqa Restaurant, F-7, Islamabad", "description": "Creamy black lentils simmered overnight in butter and cream. Rich, filling, and perfect with naan.", "image_url": IMG["daal"], "latitude": 33.7190, "longitude": 73.0722},
    {"name": "Wah Taj Breakfast Platter", "price": 480, "location": "Wah Taj, F-7, Islamabad", "description": "Full desi breakfast with halwa, puri, channay, omelette, and fresh naan. Fuels the entire morning.", "image_url": IMG["breakfast"], "latitude": 33.7197, "longitude": 73.0736},
    {"name": "Jinnah Sweets Gulab Jamun", "price": 200, "location": "Jinnah Sweet Shop, F-7, Islamabad", "description": "Soft milk-solid dumplings soaked in rose-flavoured sugar syrup. Served warm, perfect with chai.", "image_url": IMG["sweet"], "latitude": 33.7194, "longitude": 73.0721},
    {"name": "Rawal Dam Fish & Chips", "price": 900, "location": "Rawal Restaurant, F-7, Islamabad", "description": "Beer-battered Rohu fish fillets served with crispy fries, coleslaw, and tartare sauce.", "image_url": IMG["fish"], "latitude": 33.7203, "longitude": 73.0730},
    {"name": "Domino's BBQ Chicken Pizza", "price": 1100, "location": "Domino's, F-7, Islamabad", "description": "Loaded with BBQ chicken chunks, red onions, and peppers on a tangy BBQ base with mozzarella.", "image_url": IMG["pizza"], "latitude": 33.7189, "longitude": 73.0725},
    {"name": "Jade Garden Fried Rice", "price": 800, "location": "Jade Garden, F-7, Islamabad", "description": "Wok-tossed egg fried rice with spring onions, soy sauce, and vegetables. Fast, reliable Chinese.", "image_url": IMG["rice"], "latitude": 33.7206, "longitude": 73.0729},
    {"name": "Naqshbandi Paye Nashta", "price": 500, "location": "Naqshbandi Restaurant, F-7, Islamabad", "description": "Slow-cooked goat trotters in thick spiced shorba. The ultimate Islamabad winter breakfast.", "image_url": IMG["nihari"], "latitude": 33.7187, "longitude": 73.0733},
    {"name": "Desi Chai Karak F-7", "price": 80, "location": "Chai Wala, F-7 Supermarket, Islamabad", "description": "Strong double-boiled Pakistani doodh patti tea with elaichi and ginger. The national drink.", "image_url": IMG["chai"], "latitude": 33.7196, "longitude": 73.0728},

    # ── F-6 Markaz & Kohsar Market (33.7289, 73.0910) ───────────────────────
    {"name": "Saveurs du Liban Hummus Platter", "price": 900, "location": "Saveurs du Liban, F-6, Islamabad", "description": "Silky Lebanese hummus drizzled with olive oil and paprika, served with warm pita triangles and olives.", "image_url": IMG["sandwich"], "latitude": 33.7291, "longitude": 73.0912},
    {"name": "Chatkhara Chhole Bhature", "price": 280, "location": "Chatkhara, F-6 Markaz, Islamabad", "description": "Spiced chickpeas in a tangy tomato gravy served with puffed fried bhature. A North Indian classic.", "image_url": IMG["daal"], "latitude": 33.7285, "longitude": 73.0908},
    {"name": "Chaaye Khana Masala Chai", "price": 120, "location": "Chaaye Khana, F-6, Islamabad", "description": "A beautifully spiced masala chai with house-ground spice blend served in a vintage kulhad. Islamabad's most Instagrammed chai.", "image_url": IMG["chai"], "latitude": 33.7293, "longitude": 73.0915},
    {"name": "Mr. Burger Double Smash", "price": 650, "location": "Mr. Burger, F-6, Islamabad", "description": "Two thin smashed beef patties with American cheese, pickles, caramelised onions, and special sauce.", "image_url": IMG["burger"], "latitude": 33.7287, "longitude": 73.0907},
    {"name": "Kababjees Mixed Grill Platter", "price": 1600, "location": "Kababjees, F-6, Islamabad", "description": "A platter of seekh kabab, chapli kabab, boti kabab, and chicken tikka served with naan and raita.", "image_url": IMG["kabab"], "latitude": 33.7290, "longitude": 73.0911},
    {"name": "Kohsar Market Aloo Samosa", "price": 60, "location": "Street Stall, Kohsar Market, F-6, Islamabad", "description": "Crispy fried pastry filled with spiced potatoes and peas. The best cheap snack in Islamabad.", "image_url": IMG["breakfast"], "latitude": 33.7288, "longitude": 73.0909},
    {"name": "Cafe Aylanto Chicken Penne", "price": 1100, "location": "Cafe Aylanto, F-6, Islamabad", "description": "Penne tossed in a smoky tomato cream sauce with grilled chicken, capers, and fresh basil.", "image_url": IMG["pasta"], "latitude": 33.7294, "longitude": 73.0913},
    {"name": "Bake N Brew Waffle", "price": 420, "location": "Bake N Brew, F-6, Islamabad", "description": "Golden crispy waffle topped with whipped cream, strawberry compote, and maple syrup.", "image_url": IMG["sweet"], "latitude": 33.7286, "longitude": 73.0906},
    {"name": "The Pantry Eggs Benedict", "price": 750, "location": "The Pantry, F-6, Islamabad", "description": "Poached eggs on toasted English muffin with Canadian ham and hollandaise sauce. Brunch royalty.", "image_url": IMG["breakfast"], "latitude": 33.7292, "longitude": 73.0914},
    {"name": "Usmania Restaurant Biryani F-6", "price": 450, "location": "Usmania Restaurant, F-6, Islamabad", "description": "Fragrant basmati rice layered with spiced chicken, fried onions, and saffron. Classic Islamabad biryani.", "image_url": IMG["biryani"], "latitude": 33.7284, "longitude": 73.0905},
    {"name": "Pizza Roma Quattro Stagioni", "price": 1300, "location": "Pizza Roma, F-6, Islamabad", "description": "Four-seasons Italian pizza divided into four toppings: mushroom, ham, artichoke, and olives.", "image_url": IMG["pizza"], "latitude": 33.7295, "longitude": 73.0916},
    {"name": "Crunch Corner Loaded Fries", "price": 380, "location": "Crunch Corner, F-6, Islamabad", "description": "Crispy fries loaded with cheddar cheese sauce, jalapeños, grilled chicken, and sriracha drizzle.", "image_url": IMG["burger"], "latitude": 33.7283, "longitude": 73.0904},
    {"name": "Bun Kabab Street F-6", "price": 120, "location": "Bun Kabab Stall, F-6 Markaz, Islamabad", "description": "Spicy lentil patty in a soft bun with egg, mint chutney, and tamarind sauce. Islamabad street food at its finest.", "image_url": IMG["burger"], "latitude": 33.7289, "longitude": 73.0910},
    {"name": "Karachi Broast Half Chicken", "price": 500, "location": "Karachi Broast, F-6, Islamabad", "description": "Pressure-fried half chicken with a crispy golden coating and blend of secret spices. Served with garlic sauce.", "image_url": IMG["karahi"], "latitude": 33.7296, "longitude": 73.0917},

    # ── F-10 Markaz (33.6996, 73.0192) ──────────────────────────────────────
    {"name": "Jamil Sweets Dahi Bhallay", "price": 150, "location": "Jamil Sweets, F-10 Markaz, Islamabad", "description": "Soft lentil dumplings soaked in sweet-tangy yoghurt topped with chickpeas, papri, and tamarind chutney.", "image_url": IMG["sweet"], "latitude": 33.6998, "longitude": 73.0194},
    {"name": "Al Bara Broast Whole Chicken", "price": 1100, "location": "Al Bara Broast, F-10, Islamabad", "description": "Full pressure-broasted chicken with crispy skin and juicy meat. Generous portions, great value.", "image_url": IMG["karahi"], "latitude": 33.6994, "longitude": 73.0190},
    {"name": "Burger Lab Crispy Chicken", "price": 580, "location": "Burger Lab, F-10, Islamabad", "description": "Double-fried crispy chicken thigh in buttermilk batter with coleslaw and house pickles.", "image_url": IMG["burger"], "latitude": 33.6999, "longitude": 73.0195},
    {"name": "Al-Basha Shawarma", "price": 250, "location": "Al-Basha, F-10 Markaz, Islamabad", "description": "Slow-roasted chicken shawarma with garlic toum, pickled turnips, and cucumber wrapped in thin Arabic bread.", "image_url": IMG["shawarma"], "latitude": 33.6995, "longitude": 73.0189},
    {"name": "Capital Nihari F-10", "price": 500, "location": "Capital Nihari, F-10, Islamabad", "description": "Rich beef nihari cooked all night in bone marrow broth. Intensely flavoured with a thick, velvety gravy.", "image_url": IMG["nihari"], "latitude": 33.7000, "longitude": 73.0196},
    {"name": "Manpasand Sajji", "price": 1500, "location": "Manpasand Restaurant, F-10, Islamabad", "description": "Whole Balochi-style lamb marinated in salt and spices, slow-roasted on a spit. Tender, smoky, unforgettable.", "image_url": IMG["kabab"], "latitude": 33.6993, "longitude": 73.0188},
    {"name": "Pamir Kabab Chapli Kabab", "price": 350, "location": "Pamir Kabab, F-10, Islamabad", "description": "Peshawari-style flat chapli kabab with minced beef, tomatoes, coriander, and pomegranate seeds.", "image_url": IMG["kabab"], "latitude": 33.7001, "longitude": 73.0197},
    {"name": "Grill Inn BBQ Mix Grill", "price": 1200, "location": "Grill Inn, F-10, Islamabad", "description": "Mixed BBQ platter with chicken tikka, lamb chops, seekh kabab, and reshmi kabab. A carnivore's feast.", "image_url": IMG["kabab"], "latitude": 33.6992, "longitude": 73.0187},
    {"name": "Lahori Kabab Achar Gosht", "price": 550, "location": "Lahori Kabab, F-10, Islamabad", "description": "Tangy and spicy achar gosht with tender mutton pieces in a pickle-spiced masala. Pairs perfectly with naan.", "image_url": IMG["karahi"], "latitude": 33.7002, "longitude": 73.0198},
    {"name": "Sohail Chai Doodh Patti", "price": 70, "location": "Sohail Chai, F-10, Islamabad", "description": "Old-school desi doodh patti brewed in an open pot. Thick, sweet, and milky. Pakistan's comfort drink.", "image_url": IMG["chai"], "latitude": 33.6991, "longitude": 73.0186},
    {"name": "Desi Darbar Maash Daal", "price": 280, "location": "Desi Darbar, F-10, Islamabad", "description": "Slow-cooked white lentils with butter and tarka of cumin and garlic. Simple, hearty, and satisfying.", "image_url": IMG["daal"], "latitude": 33.7003, "longitude": 73.0199},
    {"name": "Green Valley Grilled Sandwich", "price": 320, "location": "Green Valley, F-10, Islamabad", "description": "Grilled chicken and cheese sandwich with mustard aioli, lettuce, and tomatoes on sourdough.", "image_url": IMG["sandwich"], "latitude": 33.6990, "longitude": 73.0185},
    {"name": "Bismillah Paye Nashta", "price": 380, "location": "Bismillah Hotel, F-10, Islamabad", "description": "Goat trotters in thick spiced broth, a classic morning dish served with fresh naan. Open from 6am.", "image_url": IMG["nihari"], "latitude": 33.7004, "longitude": 73.0200},
    {"name": "Student Karahi Half", "price": 750, "location": "Student Karahi, F-10, Islamabad", "description": "Budget half chicken karahi in a tomato-based gravy with minimal oil. Popular with office workers.", "image_url": IMG["karahi"], "latitude": 33.6989, "longitude": 73.0184},
    {"name": "Quetta Kabab Seekh F-10", "price": 400, "location": "Quetta Kabab, F-10, Islamabad", "description": "Juicy seekh kababs from Quetta-style recipe with beef and lamb mix, grilled over charcoal.", "image_url": IMG["kabab"], "latitude": 33.7005, "longitude": 73.0201},

    # ── G-9 Markaz (33.6880, 73.0236) ────────────────────────────────────────
    {"name": "Muhammadi Nihari Beef", "price": 600, "location": "Muhammadi Nihari, G-9 Markaz, Islamabad", "description": "Islamabad's most celebrated nihari. Slow-cooked overnight beef shin in a deep, bone-marrow-rich gravy.", "image_url": IMG["nihari"], "latitude": 33.6882, "longitude": 73.0238},
    {"name": "Cheezious Crown Crust Pizza", "price": 1250, "location": "Cheezious, G-9 Markaz, Islamabad", "description": "Large pizza with a cheesy stuffed crown crust, spicy chicken chunks, olives, and bell peppers.", "image_url": IMG["pizza"], "latitude": 33.6878, "longitude": 73.0234},
    {"name": "Peshawar Namkeen Karahi G-9", "price": 900, "location": "Frontier Kabab, G-9, Islamabad", "description": "Peshawari-style white karahi with minimal spices, cooked in pure fat. The purist's karahi.", "image_url": IMG["karahi"], "latitude": 33.6884, "longitude": 73.0240},
    {"name": "Dera Restaurant Sajji G-9", "price": 1400, "location": "Dera Restaurant, G-9, Islamabad", "description": "Balochi sajji with whole lamb marinated in salt and spices, roasted on an open flame until smoky.", "image_url": IMG["kabab"], "latitude": 33.6876, "longitude": 73.0232},
    {"name": "G-9 Bun Kabab", "price": 120, "location": "Bun Kabab Corner, G-9, Islamabad", "description": "Classic Karachi-style bun kabab with a masala lentil patty, egg, and signature green chutney.", "image_url": IMG["burger"], "latitude": 33.6886, "longitude": 73.0242},
    {"name": "Kashmiri Chai G-9", "price": 120, "location": "Kashmiri Chai Wala, G-9, Islamabad", "description": "Pink salty Kashmiri tea brewed with special leaves, topped with crushed pistachios and cream.", "image_url": IMG["chai"], "latitude": 33.6874, "longitude": 73.0230},
    {"name": "Anday Wala Desi Omelette", "price": 100, "location": "Anday Wala, G-9, Islamabad", "description": "Three-egg desi omelette with onions, tomatoes, green chillies, and coriander. Quick, fresh, and cheap.", "image_url": IMG["breakfast"], "latitude": 33.6888, "longitude": 73.0244},
    {"name": "Irani Paratha with Omelette", "price": 150, "location": "Irani Paratha Stall, G-9, Islamabad", "description": "Flaky layered paratha cooked on a tawa served alongside a masala omelette. The budget breakfast king.", "image_url": IMG["paratha"], "latitude": 33.6872, "longitude": 73.0228},
    {"name": "DFC Burger Meal Deal", "price": 480, "location": "DFC, G-9, Islamabad", "description": "Crispy fried chicken burger with coleslaw and a side of thick-cut fries. Great value meal deal.", "image_url": IMG["burger"], "latitude": 33.6890, "longitude": 73.0246},
    {"name": "Roshan Restaurant Biryani G-9", "price": 400, "location": "Roshan Restaurant, G-9, Islamabad", "description": "Chicken biryani with long-grain basmati, whole spices, and a generous serving of raita and salad.", "image_url": IMG["biryani"], "latitude": 33.6870, "longitude": 73.0226},
    {"name": "Bhatti Wala Boti Kabab", "price": 350, "location": "Bhatti Wala Kabab, G-9, Islamabad", "description": "Tender beef boti pieces marinated in spices and grilled over charcoal. Juicy and smoky.", "image_url": IMG["kabab"], "latitude": 33.6892, "longitude": 73.0248},
    {"name": "Pakwan Chicken Tikka G-9", "price": 700, "location": "Pakwan Restaurant, G-9, Islamabad", "description": "Tandoor-grilled chicken tikka marinated in yoghurt and spices. Juicy inside, charred outside.", "image_url": IMG["kabab"], "latitude": 33.6868, "longitude": 73.0224},
    {"name": "Capital Restaurant Haleem G-9", "price": 350, "location": "Capital Restaurant, G-9, Islamabad", "description": "Thick, hearty haleem with beef and wheat, topped with fried onions, ginger, and lemon. Filling and warming.", "image_url": IMG["haleem"], "latitude": 33.6894, "longitude": 73.0250},
    {"name": "Siddique Broast Spicy Wings", "price": 600, "location": "Siddique Broast, G-9, Islamabad", "description": "Pressure-fried chicken wings coated in spicy seasoning. Crispy, juicy, and addictively good.", "image_url": IMG["karahi"], "latitude": 33.6866, "longitude": 73.0222},
    {"name": "Roadside Samosa Chaat G-9", "price": 80, "location": "Street Stall, G-9 Markaz, Islamabad", "description": "Crushed samosa topped with spiced chickpeas, yoghurt, tamarind chutney, and masala. A beloved street snack.", "image_url": IMG["sweet"], "latitude": 33.6896, "longitude": 73.0252},

    # ── Blue Area (33.7154, 73.0734) ─────────────────────────────────────────
    {"name": "Savour Foods Chicken Pulao", "price": 450, "location": "Savour Foods, Blue Area, Islamabad", "description": "The legendary Islamabad pulao. Fragrant white rice with tender chicken pieces, subtle spices, and a side of shami kabab.", "image_url": IMG["pulao"], "latitude": 33.7156, "longitude": 73.0736},
    {"name": "Savour Foods Mutton Pulao", "price": 600, "location": "Savour Foods, Blue Area, Islamabad", "description": "Savour's prized mutton version — slow-braised mutton on aromatic pulao rice. Islamabad's most famous lunch.", "image_url": IMG["pulao"], "latitude": 33.7154, "longitude": 73.0734},
    {"name": "KFC Zinger Box Blue Area", "price": 750, "location": "KFC, Blue Area, Islamabad", "description": "Zinger burger with fries, coleslaw, and a soft drink. The office lunch go-to for Islamabad's corporate crowd.", "image_url": IMG["burger"], "latitude": 33.7158, "longitude": 73.0738},
    {"name": "Subway Teriyaki Chicken Sub", "price": 780, "location": "Subway, Blue Area, Islamabad", "description": "Six-inch sub with teriyaki-glazed chicken, lettuce, cucumber, and bell peppers on honey oat bread.", "image_url": IMG["sandwich"], "latitude": 33.7152, "longitude": 73.0732},
    {"name": "Gloria Jean's Vanilla Latte", "price": 420, "location": "Gloria Jean's, Blue Area, Islamabad", "description": "Smooth espresso with steamed vanilla-infused milk. A warm afternoon treat in Islamabad's business district.", "image_url": IMG["coffee"], "latitude": 33.7160, "longitude": 73.0740},
    {"name": "Dunkin Donuts Glazed Ring", "price": 250, "location": "Dunkin Donuts, Blue Area, Islamabad", "description": "Classic glazed donut with a sweet sugar coating. Light, fluffy, and the perfect sugar boost.", "image_url": IMG["sweet"], "latitude": 33.7150, "longitude": 73.0730},
    {"name": "Blue Area Shawarma Roll", "price": 280, "location": "Shawarma Hut, Blue Area, Islamabad", "description": "Shredded chicken shawarma with garlic toum, pickles, and french fries wrapped in Arabic bread.", "image_url": IMG["shawarma"], "latitude": 33.7162, "longitude": 73.0742},
    {"name": "Aloo Puri Nashta Blue Area", "price": 180, "location": "Puri Nashta, Blue Area, Islamabad", "description": "Crispy puffed puris served with spiced aloo, chana, and halwa. The classic Pakistani breakfast combo.", "image_url": IMG["breakfast"], "latitude": 33.7148, "longitude": 73.0728},
    {"name": "Waheed Kabab Seekh", "price": 380, "location": "Waheed Kabab House, Blue Area, Islamabad", "description": "Fresh minced beef seekh kababs from the charcoal grill. Served with naan, raita, and salad.", "image_url": IMG["kabab"], "latitude": 33.7164, "longitude": 73.0744},
    {"name": "Blue Area Tandoori Paratha", "price": 60, "location": "Nanbai, Blue Area, Islamabad", "description": "Freshly baked tandoori paratha with a crispy exterior and soft, layered inside. Pairs with anything.", "image_url": IMG["paratha"], "latitude": 33.7146, "longitude": 73.0726},
    {"name": "Quetta Restaurant Karahi", "price": 1000, "location": "Quetta Restaurant, Blue Area, Islamabad", "description": "Balochi-style namkeen karahi with fresh mutton cooked in its own juices and natural fat.", "image_url": IMG["karahi"], "latitude": 33.7166, "longitude": 73.0746},
    {"name": "The Noodle Box Pad Thai", "price": 950, "location": "The Noodle Box, Blue Area, Islamabad", "description": "Stir-fried rice noodles with shrimp, bean sprouts, peanuts, and a tangy tamarind sauce.", "image_url": IMG["pasta"], "latitude": 33.7144, "longitude": 73.0724},

    # ── NUST vicinity — H-12 (33.6415, 72.9908) ──────────────────────────────
    {"name": "NUST Cafeteria Daal Chawal", "price": 150, "location": "NUST Cafeteria, H-12, Islamabad", "description": "Comforting yellow daal on white rice with a drizzle of tarka. The student staple — cheap and filling.", "image_url": IMG["daal"], "latitude": 33.6417, "longitude": 72.9910},
    {"name": "H-12 Bun Kabab", "price": 120, "location": "Bun Kabab Stall, H-12, Islamabad", "description": "Spicy lentil bun kabab with a desi-style fried egg and mint chutney. Under PKR 150 and keeps you going.", "image_url": IMG["burger"], "latitude": 33.6413, "longitude": 72.9906},
    {"name": "Zam Zam Biryani H-12", "price": 220, "location": "Zam Zam, H-12, Islamabad", "description": "Student-budget chicken biryani with generous portions of spiced rice and a piece of chicken.", "image_url": IMG["biryani"], "latitude": 33.6419, "longitude": 72.9912},
    {"name": "Broast Corner Spicy Wings H-12", "price": 350, "location": "Broast Corner, H-12, Islamabad", "description": "Pressure-fried spicy chicken wings with hot sauce. Fast and satisfying after a long lecture.", "image_url": IMG["karahi"], "latitude": 33.6411, "longitude": 72.9904},
    {"name": "Desi Dhaba Karhi Pakora", "price": 250, "location": "Desi Dhaba, H-12, Islamabad", "description": "Gram-flour pakoras floating in a tangy yoghurt-based kadhi. Nostalgic home-style comfort food.", "image_url": IMG["daal"], "latitude": 33.6421, "longitude": 72.9914},
    {"name": "Al Noor Shawarma H-12", "price": 200, "location": "Al Noor, H-12, Islamabad", "description": "Chicken shawarma roll with garlic sauce, pickled cucumber, and a hint of chilli. Quick campus meal.", "image_url": IMG["shawarma"], "latitude": 33.6409, "longitude": 72.9902},
    {"name": "Village Restaurant Saag H-12", "price": 280, "location": "Village Restaurant, H-12, Islamabad", "description": "Mustard greens cooked with butter and garlic. Served with makki ki roti for a traditional Punjab meal.", "image_url": IMG["daal"], "latitude": 33.6423, "longitude": 72.9916},
    {"name": "NUST Bakery Bread Omelette", "price": 120, "location": "Campus Bakery, H-12, Islamabad", "description": "Double bread slices toasted with a spiced egg omelette inside. Cheap, quick, and dangerously good.", "image_url": IMG["breakfast"], "latitude": 33.6407, "longitude": 72.9900},
    {"name": "Fresh Juice Corner Mix Fruit", "price": 150, "location": "Juice Corner, H-12, Islamabad", "description": "Fresh-pressed mix of seasonal fruits — mango, guava, and orange. Energising and affordable.", "image_url": IMG["sweet"], "latitude": 33.6425, "longitude": 72.9918},
    {"name": "Chai Point Adrak Chai", "price": 60, "location": "Chai Point, H-12, Islamabad", "description": "Strong ginger tea brewed in milk. Campus essential — fuels late-night study sessions.", "image_url": IMG["chai"], "latitude": 33.6405, "longitude": 72.9898},
    {"name": "BBQ Delight Chicken Tikka H-12", "price": 450, "location": "BBQ Delight, H-12, Islamabad", "description": "Marinated chicken tikka pieces off the grill. A step up from canteen food for a post-exam treat.", "image_url": IMG["kabab"], "latitude": 33.6427, "longitude": 72.9920},
    {"name": "Handi Chicken Handi H-12", "price": 500, "location": "Handi Restaurant, H-12, Islamabad", "description": "Slow-cooked chicken handi in a rich cream and butter sauce. Restaurant-quality near campus.", "image_url": IMG["karahi"], "latitude": 33.6403, "longitude": 72.9896},
    {"name": "Cheezious Margarita H-12", "price": 850, "location": "Cheezious, H-12, Islamabad", "description": "Classic margarita pizza on a thin crust with fresh tomato sauce, mozzarella, and basil leaves.", "image_url": IMG["pizza"], "latitude": 33.6429, "longitude": 72.9922},
    {"name": "Pakwaan Sajji H-12", "price": 900, "location": "Pakwaan, H-12, Islamabad", "description": "Whole roasted chicken in Balochi style with minimal spices, crusty skin, and juicy interior.", "image_url": IMG["kabab"], "latitude": 33.6401, "longitude": 72.9894},

    # ── COMSATS / Park Road (33.6835, 72.9793) ───────────────────────────────
    {"name": "COMSATS Canteen Biryani", "price": 180, "location": "COMSATS Canteen, Park Road, Islamabad", "description": "No-frills chicken biryani served in generous portions. The most affordable biryani near Park Road.", "image_url": IMG["biryani"], "latitude": 33.6837, "longitude": 72.9795},
    {"name": "Anday Wala Scrambled Eggs Park Rd", "price": 100, "location": "Anday Wala, Park Road, Islamabad", "description": "Fluffy scrambled eggs tossed with green chillies, tomatoes, and onions. Cheap, fast, and satisfying.", "image_url": IMG["breakfast"], "latitude": 33.6833, "longitude": 72.9791},
    {"name": "Ustaad Karahi Park Road", "price": 700, "location": "Ustaad Karahi, Park Road, Islamabad", "description": "Fresh chicken karahi prepared to order. The best karahi stop on the Islamabad-Murree road.", "image_url": IMG["karahi"], "latitude": 33.6839, "longitude": 72.9797},
    {"name": "Shawarma Hut Chicken Roll", "price": 220, "location": "Shawarma Hut, Park Road, Islamabad", "description": "Garlic-rich chicken shawarma in a thin wrap. A popular quick bite for COMSATS students.", "image_url": IMG["shawarma"], "latitude": 33.6831, "longitude": 72.9789},
    {"name": "Student Pulao Park Road", "price": 200, "location": "Dhabba, Park Road, Islamabad", "description": "Simple and filling chicken pulao for the budget-conscious student. Serves a crowd at the right price.", "image_url": IMG["pulao"], "latitude": 33.6841, "longitude": 72.9799},
    {"name": "Nashta Corner Puri Omelette", "price": 160, "location": "Nashta Corner, Park Road, Islamabad", "description": "Puri with masala omelette — the classic Pakistani morning combo for under PKR 200.", "image_url": IMG["breakfast"], "latitude": 33.6829, "longitude": 72.9787},
    {"name": "Tikka Inn Seekh Kabab Park Rd", "price": 380, "location": "Tikka Inn, Park Road, Islamabad", "description": "Charcoal-grilled seekh kababs made fresh to order. Great for evening roadside dining.", "image_url": IMG["kabab"], "latitude": 33.6843, "longitude": 72.9801},
    {"name": "Budget Biryani Corner", "price": 170, "location": "Budget Biryani, Park Road, Islamabad", "description": "No-frills, high-quantity biryani. Trusted by students for years. Comes with raita and salad.", "image_url": IMG["biryani"], "latitude": 33.6827, "longitude": 72.9785},
    {"name": "Kabul Restaurant Chapli Kabab", "price": 400, "location": "Kabul Restaurant, Park Road, Islamabad", "description": "Authentic Peshawari chapli kabab made with beef, fresh tomatoes, and pomegranate seeds.", "image_url": IMG["kabab"], "latitude": 33.6845, "longitude": 72.9803},
    {"name": "Dilpasand Halwa Puri", "price": 160, "location": "Dilpasand Sweets, Park Road, Islamabad", "description": "Suji halwa with crispy puris and channay. The beloved Sunday morning treat, available all week here.", "image_url": IMG["breakfast"], "latitude": 33.6825, "longitude": 72.9783},
    {"name": "Rehmat Broast Park Road", "price": 400, "location": "Rehmat Broast, Park Road, Islamabad", "description": "Pressure-fried chicken with a crispy golden coat. COMSATS students' top broast pick.", "image_url": IMG["karahi"], "latitude": 33.6847, "longitude": 72.9805},
    {"name": "Paratha Roll Achar Chicken", "price": 180, "location": "Paratha Corner, Park Road, Islamabad", "description": "Spicy achar chicken wrapped in a flaky paratha. A filling campus snack that hits all the right notes.", "image_url": IMG["paratha"], "latitude": 33.6823, "longitude": 72.9781},

    # ── Saddar / Rawalpindi (33.5951, 73.0616) ───────────────────────────────
    {"name": "Nagina Bun Kabab Saddar", "price": 180, "location": "Nagina Bun Kabab, Saddar, Rawalpindi", "description": "The original Rawalpindi bun kabab — spicy lentil patty, fried egg, mint chutney in a soft bun.", "image_url": IMG["burger"], "latitude": 33.5953, "longitude": 73.0618},
    {"name": "Rajput Nihari Saddar", "price": 550, "location": "Rajput Nihari, Saddar, Rawalpindi", "description": "Traditional beef nihari recipe passed down generations. Rich, spiced shorba with naan.", "image_url": IMG["nihari"], "latitude": 33.5949, "longitude": 73.0614},
    {"name": "Kartarpura Lassi", "price": 150, "location": "Lassi Wala, Kartarpura, Rawalpindi", "description": "Traditional thick and creamy sweet lassi served chilled in a large clay glass. Rawalpindi's best.", "image_url": IMG["sweet"], "latitude": 33.6126, "longitude": 73.0679},
    {"name": "Raja Sahib Paye", "price": 400, "location": "Raja Sahib, Saddar, Rawalpindi", "description": "Slow-cooked goat trotters in a thick, spiced broth. An early morning Rawalpindi tradition.", "image_url": IMG["nihari"], "latitude": 33.5955, "longitude": 73.0620},
    {"name": "Saddar Tawa Chicken", "price": 500, "location": "Tawa Chicken, Saddar, Rawalpindi", "description": "Spicy shredded chicken tossed on a hot iron tawa with masalas. Intense flavour, served with roti.", "image_url": IMG["karahi"], "latitude": 33.5947, "longitude": 73.0612},
    {"name": "Punjab Sweets Jalebi", "price": 100, "location": "Punjab Sweets, Saddar, Rawalpindi", "description": "Freshly fried spiral jalebis soaked in hot sugar syrup. Crispy, syrupy, and completely irresistible.", "image_url": IMG["sweet"], "latitude": 33.5957, "longitude": 73.0622},
    {"name": "Bismillah Biryani Saddar", "price": 350, "location": "Bismillah Hotel, Saddar, Rawalpindi", "description": "Old-school Rawalpindi chicken biryani with whole spices and a rich masala base. No frills, all flavour.", "image_url": IMG["biryani"], "latitude": 33.5945, "longitude": 73.0610},
    {"name": "Peshawari Inn Kabab Karahi", "price": 850, "location": "Peshawari Inn, Saddar, Rawalpindi", "description": "Namkeen karahi with fresh beef and minimal spices. A Peshawari classic in the heart of Rawalpindi.", "image_url": IMG["karahi"], "latitude": 33.5959, "longitude": 73.0624},
    {"name": "Lalazar Mutton Pulao", "price": 550, "location": "Lalazar Restaurant, Saddar, Rawalpindi", "description": "Aromatic mutton pulao cooked with whole spices and slow-braised mutton shoulder. Rich and fragrant.", "image_url": IMG["pulao"], "latitude": 33.5943, "longitude": 73.0608},
    {"name": "Rawalpindi Chapli Kabab", "price": 300, "location": "Rawalpindi Kabab, Saddar, Rawalpindi", "description": "Wide, flat chapli kabab with egg, coriander, and tomato. Rawalpindi's street favourite.", "image_url": IMG["kabab"], "latitude": 33.5961, "longitude": 73.0626},
    {"name": "Saddar Chhole Stall", "price": 150, "location": "Liaquat Bagh, Saddar, Rawalpindi", "description": "Spiced chickpeas with ginger-tamarind chutney and crispy papri. Budget street food at its best.", "image_url": IMG["daal"], "latitude": 33.5941, "longitude": 73.0606},
    {"name": "Grills and Wills BBQ Rawalpindi", "price": 1100, "location": "Grills and Wills, Saddar, Rawalpindi", "description": "Mixed BBQ platter with chicken wings, seekh kabab, and chops. Rawalpindi's favourite evening grill.", "image_url": IMG["kabab"], "latitude": 33.5963, "longitude": 73.0628},
    {"name": "Cantt Bakery Cream Roll", "price": 120, "location": "Cantt Bakery, Saddar, Rawalpindi", "description": "Flaky pastry roll filled with sweetened whipped cream. A Rawalpindi bakery institution.", "image_url": IMG["sweet"], "latitude": 33.5939, "longitude": 73.0604},
    {"name": "Grilled Fish Saddar", "price": 700, "location": "Fish Corner, Saddar, Rawalpindi", "description": "Fresh Rohu marinated in tandoori spices and grilled to perfection. Served with chutney and salad.", "image_url": IMG["fish"], "latitude": 33.5965, "longitude": 73.0630},

    # ── E-11 / F-11 / G-10 / Jinnah Super (various) ─────────────────────────
    {"name": "Burning Brownie Choco Lava", "price": 380, "location": "Burning Brownie, E-11, Islamabad", "description": "Warm chocolate lava cake with a molten centre, served with vanilla ice cream. Pure dessert indulgence.", "image_url": IMG["sweet"], "latitude": 33.7017, "longitude": 72.9986},
    {"name": "Dine Inn Chicken Qorma", "price": 550, "location": "Dine Inn, E-11, Islamabad", "description": "Aromatic chicken qorma in a yoghurt and nut-based gravy with whole spices. Homestyle and comforting.", "image_url": IMG["karahi"], "latitude": 33.7013, "longitude": 72.9982},
    {"name": "Cha Dao Oolong Tea", "price": 350, "location": "Cha Dao, E-11, Islamabad", "description": "Premium Taiwanese oolong steeped to perfection. Light, floral, and a sophisticated break from doodh patti.", "image_url": IMG["chai"], "latitude": 33.7019, "longitude": 72.9988},
    {"name": "Roots Cafe Avocado Toast", "price": 650, "location": "Roots Cafe, E-11, Islamabad", "description": "Sourdough toast topped with smashed avocado, poached eggs, and chilli flakes. Islamabad's brunch elite.", "image_url": IMG["sandwich"], "latitude": 33.7011, "longitude": 72.9980},
    {"name": "Charcoal BBQ Mutton Chops", "price": 1600, "location": "Charcoal BBQ, F-11, Islamabad", "description": "Marinated mutton chops slow-grilled on a charcoal fire until perfectly charred and juicy.", "image_url": IMG["kabab"], "latitude": 33.7095, "longitude": 72.9996},
    {"name": "El Momento Pasta Arrabiata", "price": 1100, "location": "El Momento, F-11, Islamabad", "description": "Penne in a spicy tomato arrabiata sauce with garlic, olives, and fresh basil. Vibrant and bold.", "image_url": IMG["pasta"], "latitude": 33.7091, "longitude": 72.9992},
    {"name": "Cosa Nostra Tiramisu F-11", "price": 680, "location": "Cosa Nostra, F-11, Islamabad", "description": "Classic Italian tiramisu with espresso-soaked savoiardi, mascarpone cream, and dusted cocoa.", "image_url": IMG["sweet"], "latitude": 33.7097, "longitude": 72.9998},
    {"name": "Caspian Kebab Koobideh", "price": 1200, "location": "Caspian Restaurant, G-11, Islamabad", "description": "Persian-style minced lamb koobideh grilled on flat skewers, served with saffron rice and grilled tomato.", "image_url": IMG["kabab"], "latitude": 33.6802, "longitude": 72.9902},
    {"name": "Spice Bazaar Chicken Biryani G-11", "price": 500, "location": "Spice Bazaar, G-11, Islamabad", "description": "Fragrant chicken biryani with saffron, whole spices, and caramelised onions. A reliable G-11 go-to.", "image_url": IMG["biryani"], "latitude": 33.6798, "longitude": 72.9898},
    {"name": "Reem Mutton Karahi G-11", "price": 1300, "location": "Reem Restaurant, G-11, Islamabad", "description": "Fresh mutton karahi made on order in a cast-iron wok. Bold, buttery, and best with tandoori roti.", "image_url": IMG["karahi"], "latitude": 33.6806, "longitude": 72.9906},
    {"name": "Afreen Halwa Puri G-10", "price": 250, "location": "Afreen Restaurant, G-10, Islamabad", "description": "Generous suji halwa with crispy puris and channay. Trusted by G-10 families for Sunday breakfast.", "image_url": IMG["breakfast"], "latitude": 33.6893, "longitude": 73.0053},
    {"name": "The Spice Tree Butter Chicken", "price": 850, "location": "The Spice Tree, G-10, Islamabad", "description": "Creamy tomato-butter chicken tikka masala with aromatic whole spices. Rich and lightly spiced.", "image_url": IMG["karahi"], "latitude": 33.6889, "longitude": 73.0049},
    {"name": "Kabul Village Chapli Kabab G-10", "price": 450, "location": "Kabul Village, G-10, Islamabad", "description": "Authentic Afghan-style chapli kabab with minced beef, walnuts, and pomegranate seeds.", "image_url": IMG["kabab"], "latitude": 33.6897, "longitude": 73.0057},
    {"name": "Jinnah Super Broast", "price": 750, "location": "Broast House, Jinnah Super, Islamabad", "description": "Quarter broasted chicken with coleslaw and garlic dip. A lunchtime staple in Jinnah Super Market.", "image_url": IMG["karahi"], "latitude": 33.7137, "longitude": 73.0586},
    {"name": "Coffee Republic Iced Coffee", "price": 480, "location": "Coffee Republic, Jinnah Super, Islamabad", "description": "Cold brew over ice with a splash of cream. Smooth, strong, and perfect for a warm Islamabad afternoon.", "image_url": IMG["coffee"], "latitude": 33.7133, "longitude": 73.0582},
    {"name": "Gaylord Fish Tikka", "price": 900, "location": "Gaylord Restaurant, Jinnah Super, Islamabad", "description": "Marinated Rohu fish tikka grilled in a tandoor until smoky. Served with mint chutney and lemon.", "image_url": IMG["fish"], "latitude": 33.7139, "longitude": 73.0588},
    {"name": "Ambrosia Special Biryani", "price": 600, "location": "Ambrosia, Jinnah Super, Islamabad", "description": "Special biryani with layered saffron rice, caramelised onions, and slow-cooked chicken.", "image_url": IMG["biryani"], "latitude": 33.7131, "longitude": 73.0580},
    {"name": "Desi Dhaba Achar Gosht", "price": 550, "location": "Desi Dhaba, Jinnah Super, Islamabad", "description": "Tangy achar gosht with mutton in a sharp pickle-spiced gravy. A Punjabi classic done right.", "image_url": IMG["karahi"], "latitude": 33.7141, "longitude": 73.0590},
    {"name": "The Hive Chicken Pita", "price": 750, "location": "The Hive, Jinnah Super, Islamabad", "description": "Grilled chicken stuffed in warm pita with Greek tzatziki, rocket, and roasted pepper strips.", "image_url": IMG["sandwich"], "latitude": 33.7129, "longitude": 73.0578},
    {"name": "Moshi Sushi Salmon Roll", "price": 1400, "location": "Moshi Sushi, F-11, Islamabad", "description": "Fresh salmon and cucumber maki roll with pickled ginger, wasabi, and soy sauce. Islamabad's top sushi.", "image_url": IMG["fish"], "latitude": 33.7093, "longitude": 72.9994},
    {"name": "Yalla Mediterranean Falafel", "price": 650, "location": "Yalla, G-11, Islamabad", "description": "Crispy falafel balls with tahini, sumac-spiced salad, and warm pita. A refreshing Middle Eastern option.", "image_url": IMG["sandwich"], "latitude": 33.6804, "longitude": 72.9904},
    {"name": "Nans Artisan Sourdough", "price": 350, "location": "Nans Bakery, F-11, Islamabad", "description": "Freshly baked open-crumb sourdough loaf with a crisp crust. Best with butter and seasonal jam.", "image_url": IMG["sandwich"], "latitude": 33.7089, "longitude": 72.9990},
    {"name": "Pindi Wala Saag Chicken", "price": 400, "location": "Pindi Wala, G-10, Islamabad", "description": "Chicken cooked in fresh mustard greens masala. A rustic Punjabi recipe served with makki naan.", "image_url": IMG["daal"], "latitude": 33.6885, "longitude": 73.0045},

    # ── I-8 Markaz (33.6711, 73.0542) ────────────────────────────────────────
    {"name": "I-8 Broast Express Quarter", "price": 520, "location": "Broast Express, I-8 Markaz, Islamabad", "description": "Pressure-fried quarter chicken with a crispy seasoned crust. Quick and filling after a long commute.", "image_url": IMG["karahi"], "latitude": 33.6713, "longitude": 73.0544},
    {"name": "Khan Baba Chapli Kabab I-8", "price": 320, "location": "Khan Baba, I-8 Markaz, Islamabad", "description": "Wide minced beef chapli kabab with tomato, egg, and pomegranate seeds cooked on a flat iron pan.", "image_url": IMG["kabab"], "latitude": 33.6709, "longitude": 73.0540},
    {"name": "Al Madina Shawarma I-8", "price": 230, "location": "Al Madina, I-8 Markaz, Islamabad", "description": "Chicken shawarma with creamy garlic sauce and pickled vegetables in a warm Arabic flatbread.", "image_url": IMG["shawarma"], "latitude": 33.6715, "longitude": 73.0546},
    {"name": "I-8 Chai Paratha Combo", "price": 130, "location": "Dhaba, I-8 Markaz, Islamabad", "description": "Plain desi ghee paratha with a glass of strong doodh patti. The simplest pleasure in Islamabad.", "image_url": IMG["paratha"], "latitude": 33.6707, "longitude": 73.0538},
    {"name": "Nihari King Beef Nihari I-8", "price": 580, "location": "Nihari King, I-8, Islamabad", "description": "Slow-cooked overnight nihari with marrow bones. The I-8 neighbourhood's go-to morning dish.", "image_url": IMG["nihari"], "latitude": 33.6717, "longitude": 73.0548},
    {"name": "Pizza Palace Tikka Pizza I-8", "price": 900, "location": "Pizza Palace, I-8, Islamabad", "description": "Pakistani-style tikka pizza topped with marinated chicken pieces, onions, and green chillies.", "image_url": IMG["pizza"], "latitude": 33.6705, "longitude": 73.0536},
    {"name": "Student Daal Chawal I-8", "price": 160, "location": "Dhabba, I-8, Islamabad", "description": "Budget-friendly yellow daal on steamed rice. A daily staple for the working class of I-8.", "image_url": IMG["daal"], "latitude": 33.6719, "longitude": 73.0550},
    {"name": "Haleem House I-8", "price": 380, "location": "Haleem House, I-8, Islamabad", "description": "Hearty wheat and lentil haleem slow-cooked with beef shank. Topped with crispy onions and lime.", "image_url": IMG["haleem"], "latitude": 33.6703, "longitude": 73.0534},

    # ── I-9 / I-10 Industrial Area (33.6600, 73.0400) ────────────────────────
    {"name": "Frontier Kabab Tikka I-9", "price": 650, "location": "Frontier Kabab, I-9, Islamabad", "description": "Tandoor-fresh chicken tikka marinated in desi spices. Trusted by the I-9 industrial crowd for decades.", "image_url": IMG["kabab"], "latitude": 33.6602, "longitude": 73.0402},
    {"name": "Sajji Point Whole Chicken", "price": 1200, "location": "Sajji Point, I-9, Islamabad", "description": "Whole chicken marinated in salt and spices and roasted on a spit. Simple Balochi flavour at its purest.", "image_url": IMG["kabab"], "latitude": 33.6598, "longitude": 73.0398},
    {"name": "Budget Biryani I-10", "price": 160, "location": "Budget Biryani, I-10, Islamabad", "description": "No-frills chicken biryani popular with factory workers. Big portions, low price, reliable taste.", "image_url": IMG["biryani"], "latitude": 33.6604, "longitude": 73.0404},
    {"name": "Anday Paratha I-10 Nashta", "price": 110, "location": "Nashta Stall, I-10, Islamabad", "description": "Fried egg on a freshly made paratha. The universal Pakistani morning fuel for labourers and students.", "image_url": IMG["breakfast"], "latitude": 33.6596, "longitude": 73.0396},
    {"name": "Bari Wala Haleem I-9", "price": 350, "location": "Bari Wala, I-9, Islamabad", "description": "Thick, grainy haleem with beef and lentils. Sold by the kilo — great takeaway option.", "image_url": IMG["haleem"], "latitude": 33.6606, "longitude": 73.0406},

    # ── G-6 / G-7 / Aabpara (33.7040, 73.0620) ──────────────────────────────
    {"name": "Aabpara Market Nihari", "price": 500, "location": "Nihari Wala, Aabpara, Islamabad", "description": "Morning nihari right at the market. Thick bone-in beef with rich tallow-based gravy and naan.", "image_url": IMG["nihari"], "latitude": 33.7042, "longitude": 73.0622},
    {"name": "Kohsar Sweets Barfi", "price": 300, "location": "Kohsar Sweets, G-6, Islamabad", "description": "Milk-solid barfi flavoured with cardamom and rose water. Perfect for gifting or a sweet craving.", "image_url": IMG["sweet"], "latitude": 33.7038, "longitude": 73.0618},
    {"name": "G-7 Karahi Wala", "price": 950, "location": "Karahi Wala, G-7, Islamabad", "description": "Freshly prepared chicken karahi in a tomato and onion masala. Open from lunch to midnight.", "image_url": IMG["karahi"], "latitude": 33.7044, "longitude": 73.0624},
    {"name": "Aabpara Bun Kabab", "price": 110, "location": "Bun Kabab Stall, Aabpara, Islamabad", "description": "Spicy lentil kabab in a soft bun — quick and cheap for government workers in G-6.", "image_url": IMG["burger"], "latitude": 33.7036, "longitude": 73.0616},
    {"name": "Punjab Pulao G-7", "price": 420, "location": "Punjab Pulao, G-7, Islamabad", "description": "Fragrant chicken pulao in the Savour tradition — long-grain rice with whole spices and a shami kabab.", "image_url": IMG["pulao"], "latitude": 33.7046, "longitude": 73.0626},
    {"name": "Tea Time Doodh Patti G-6", "price": 70, "location": "Tea Stall, G-6, Islamabad", "description": "Classic doodh patti brewed in an open pot. The cheapest and most satisfying drink in the capital.", "image_url": IMG["chai"], "latitude": 33.7034, "longitude": 73.0614},

    # ── DHA Phase 2 / Expressway (33.5750, 73.0900) ──────────────────────────
    {"name": "DHA Grill House Steakhouse", "price": 2200, "location": "DHA Grill, Phase 2, Rawalpindi", "description": "Premium beef steak grilled to order with pepper sauce, mashed potatoes, and grilled vegetables.", "image_url": IMG["kabab"], "latitude": 33.5752, "longitude": 73.0902},
    {"name": "Cafe 26 Chicken Wrap DHA", "price": 680, "location": "Cafe 26, DHA Phase 2, Rawalpindi", "description": "Grilled chicken, avocado, and Caesar dressing wrapped in a whole-wheat tortilla. Fresh and satisfying.", "image_url": IMG["wrap"], "latitude": 33.5748, "longitude": 73.0898},
    {"name": "Bella Italia Margherita DHA", "price": 1100, "location": "Bella Italia, DHA Phase 2, Rawalpindi", "description": "Thin-crust Margherita pizza with San Marzano tomato, fresh mozzarella, and basil. Proper Italian.", "image_url": IMG["pizza"], "latitude": 33.5754, "longitude": 73.0904},
    {"name": "DHA Chai Wala Karak", "price": 90, "location": "Chai Wala, DHA Phase 2, Rawalpindi", "description": "Strong karak chai with condensed milk. Hugely popular evening ritual in DHA.", "image_url": IMG["chai"], "latitude": 33.5746, "longitude": 73.0896},
    {"name": "Roadside BBQ Boti DHA", "price": 400, "location": "BBQ Stall, DHA Expressway, Rawalpindi", "description": "Charcoal-grilled beef boti skewers with mint chutney. An evening must-stop on the DHA expressway.", "image_url": IMG["kabab"], "latitude": 33.5756, "longitude": 73.0906},

    # ── Bahria Town Phase 7 / 8 (33.5300, 73.1500) ──────────────────────────
    {"name": "Bahria Broast Chicken", "price": 580, "location": "Bahria Broast, Phase 7, Rawalpindi", "description": "Crispy pressure-fried chicken with Bahria's signature spice mix. A suburb staple.", "image_url": IMG["karahi"], "latitude": 33.5302, "longitude": 73.1502},
    {"name": "Kebab Express Bahria", "price": 450, "location": "Kebab Express, Phase 8, Rawalpindi", "description": "Mixed kebab platter with seekh, chicken tikka, and boti. Great for family dinners.", "image_url": IMG["kabab"], "latitude": 33.5298, "longitude": 73.1498},
    {"name": "Lums Cafe Burger Bahria", "price": 560, "location": "Lums Cafe, Phase 7, Rawalpindi", "description": "Juicy beef patty burger with caramelised onions and cheddar. A favourite hangout spot in Bahria.", "image_url": IMG["burger"], "latitude": 33.5304, "longitude": 73.1504},
    {"name": "Pizza One Bahria Phase 8", "price": 980, "location": "Pizza One, Phase 8, Rawalpindi", "description": "Pakistani-style pizza chain with a generous tikka topping and a thick, doughy crust.", "image_url": IMG["pizza"], "latitude": 33.5296, "longitude": 73.1496},
    {"name": "Bahria Chai Corner", "price": 80, "location": "Chai Corner, Phase 7, Rawalpindi", "description": "Budget-friendly karak chai stop in Bahria Town. Pulls in crowds from all nearby blocks.", "image_url": IMG["chai"], "latitude": 33.5306, "longitude": 73.1506},

    # ── F-8 Markaz (33.6932, 73.0323) ────────────────────────────────────────
    {"name": "Butt Karahi F-8 Chicken", "price": 950, "location": "Butt Karahi, F-8, Islamabad", "description": "F-8's most famous karahi house. Freshly cooked chicken karahi in butter and tomatoes with ginger.", "image_url": IMG["karahi"], "latitude": 33.6934, "longitude": 73.0325},
    {"name": "Subway Italian BMT F-8", "price": 780, "location": "Subway, F-8, Islamabad", "description": "Six-inch BMT with salami, pepperoni, ham, and all the fresh veggies. A filling lunch in F-8.", "image_url": IMG["sandwich"], "latitude": 33.6930, "longitude": 73.0321},
    {"name": "F-8 Paratha Roll Classic", "price": 160, "location": "Roll Corner, F-8 Markaz, Islamabad", "description": "Chicken keema roll in a crispy paratha with mint chutney and sliced onions. Quick evening bite.", "image_url": IMG["paratha"], "latitude": 33.6936, "longitude": 73.0327},
    {"name": "Desi Karahi F-8 Mutton", "price": 1050, "location": "Desi Karahi, F-8, Islamabad", "description": "Mutton karahi made to order with ginger julienne and green chillies. Aromatic and generous.", "image_url": IMG["karahi"], "latitude": 33.6928, "longitude": 73.0319},
    {"name": "Student Biryani F-8", "price": 250, "location": "Student Biryani, F-8 Markaz, Islamabad", "description": "Authentic spicy Karachi-style biryani with tender chicken and a perfectly cooked potato. Great value.", "image_url": IMG["biryani"], "latitude": 33.6938, "longitude": 73.0329},
    {"name": "Coffee Cloud F-8 Espresso", "price": 380, "location": "Coffee Cloud, F-8, Islamabad", "description": "Single-origin espresso with a rich crema. A specialty coffee shop tucked into F-8 Markaz.", "image_url": IMG["coffee"], "latitude": 33.6926, "longitude": 73.0317},

    # ── H-9 / H-8 / Sector H vicinity (33.6600, 73.0100) ────────────────────
    {"name": "PIMS Cafeteria Daal", "price": 130, "location": "PIMS Cafeteria, H-8, Islamabad", "description": "Reliable daal chawal at hospital prices. Comforting and affordable for staff and visitors alike.", "image_url": IMG["daal"], "latitude": 33.6602, "longitude": 73.0102},
    {"name": "H-8 Broast Spicy Wings", "price": 380, "location": "Broast Wala, H-8, Islamabad", "description": "Crispy fried spicy chicken wings with tangy dipping sauce. Popular with Quaid-e-Azam University students.", "image_url": IMG["karahi"], "latitude": 33.6598, "longitude": 73.0098},
    {"name": "QAU Biryani Special", "price": 200, "location": "QAU Canteen, H-9, Islamabad", "description": "Campus-special biryani served in generous portions. The cheapest biryani in Islamabad with real flavour.", "image_url": IMG["biryani"], "latitude": 33.7407, "longitude": 73.1367},
    {"name": "QAU Chai Dhaba", "price": 55, "location": "Chai Dhaba, QAU, Islamabad", "description": "The cheapest and strongest desi chai on campus. A student essential through every exam season.", "image_url": IMG["chai"], "latitude": 33.7403, "longitude": 73.1363},
    {"name": "QAU Bun Kabab Stall", "price": 100, "location": "Bun Kabab Stall, QAU, Islamabad", "description": "Masala bun kabab with tamarind chutney. The most affordable snack on the QAU campus.", "image_url": IMG["burger"], "latitude": 33.7409, "longitude": 73.1369},

    # ── Centaurus / Zero Point (33.7270, 73.0900) ────────────────────────────
    {"name": "Hotspot Centaurus Wrap", "price": 750, "location": "Hotspot, Centaurus Mall, Islamabad", "description": "Grilled chicken wrap with Caesar dressing, romaine lettuce, and parmesan shavings.", "image_url": IMG["wrap"], "latitude": 33.7272, "longitude": 73.0902},
    {"name": "Johnny Rockets Centaurus", "price": 1100, "location": "Johnny Rockets, Centaurus Mall, Islamabad", "description": "Classic American diner burger with thick beef patty, American cheese, and their famous special sauce.", "image_url": IMG["burger"], "latitude": 33.7268, "longitude": 73.0898},
    {"name": "McDonald's Centaurus McFlurry", "price": 380, "location": "McDonald's, Centaurus Mall, Islamabad", "description": "Creamy McFlurry with Oreo crumbles. A sweet break during Centaurus Mall shopping.", "image_url": IMG["sweet"], "latitude": 33.7274, "longitude": 73.0904},
    {"name": "Quetta Pulao Zero Point", "price": 500, "location": "Quetta Pulao, Zero Point, Islamabad", "description": "Fragrant white pulao with tender mutton, whole spices, and a side of shami kabab and raita.", "image_url": IMG["pulao"], "latitude": 33.7266, "longitude": 73.0896},
    {"name": "Centaurus Food Court Pizza", "price": 1200, "location": "Pizza Express, Centaurus, Islamabad", "description": "Wood-fired pizza with a thin crust and classic tomato-mozzarella base. Casual Italian in the mall.", "image_url": IMG["pizza"], "latitude": 33.7276, "longitude": 73.0906},

    # ── Rawalpindi Cantt / Lalkurti (33.6000, 73.0500) ─────────────────────
    {"name": "Cantt Mutton Karahi", "price": 1100, "location": "Karahi House, Cantt, Rawalpindi", "description": "Fresh mutton karahi prepared in a large wok over a high flame. The Cantt crowd's dinner staple.", "image_url": IMG["karahi"], "latitude": 33.6002, "longitude": 73.0502},
    {"name": "Lalkurti Nihari", "price": 520, "location": "Nihari Wala, Lalkurti, Rawalpindi", "description": "Old Rawalpindi-style beef nihari with a rich, oily gravy and large naan. Served from 5am.", "image_url": IMG["nihari"], "latitude": 33.5998, "longitude": 73.0498},
    {"name": "Cantt Bakery Plum Cake", "price": 200, "location": "Cantt Bakery, Rawalpindi", "description": "Classic plum cake from a century-old bakery. Dense, fruity, and reminiscent of colonial-era baking.", "image_url": IMG["sweet"], "latitude": 33.6004, "longitude": 73.0504},
    {"name": "Cantt Broast Family Pack", "price": 1400, "location": "Cantt Broast, Rawalpindi", "description": "Full broast family pack with a whole chicken, fries, coleslaw, and garlic bread. Great for groups.", "image_url": IMG["karahi"], "latitude": 33.5996, "longitude": 73.0496},
    {"name": "Peshawari Naan Cantt", "price": 25, "location": "Nanbai, Cantt, Rawalpindi", "description": "Freshly baked giant Peshawari naan with a crispy exterior and soft interior. The bread of the north.", "image_url": IMG["paratha"], "latitude": 33.6006, "longitude": 73.0506},

    # ── Raja Bazar / Banni Chowk, Rawalpindi (33.6070, 73.0480) ────────────
    {"name": "Raja Bazar Halwa Puri", "price": 160, "location": "Halwa Puri Wala, Raja Bazar, Rawalpindi", "description": "Suji halwa with puris and spiced channay. The classic Rawalpindi Sunday morning breakfast.", "image_url": IMG["breakfast"], "latitude": 33.6072, "longitude": 73.0482},
    {"name": "Javed Nihari Banni Chowk", "price": 500, "location": "Javed Nihari, Banni Chowk, Rawalpindi", "description": "An institution in Rawalpindi. Beef nihari cooked all night in heavy copper pots. Sold out by 9am.", "image_url": IMG["nihari"], "latitude": 33.6068, "longitude": 73.0478},
    {"name": "Chopstix Chinese Fried Rice", "price": 750, "location": "Chopstix, Raja Bazar, Rawalpindi", "description": "Wok-tossed chicken fried rice with vegetables, soy sauce, and scrambled egg. Quick Chinese fix.", "image_url": IMG["rice"], "latitude": 33.6074, "longitude": 73.0484},
    {"name": "Banni Chowk Pulao", "price": 380, "location": "Pulao Wala, Banni Chowk, Rawalpindi", "description": "Traditional white pulao with mutton and whole spices. An affordable and filling Rawalpindi classic.", "image_url": IMG["pulao"], "latitude": 33.6066, "longitude": 73.0476},

    # ── Extra picks across Islamabad ─────────────────────────────────────────
    {"name": "Islamabad Club Prawn Biryani", "price": 1600, "location": "Islamabad Club, G-6, Islamabad", "description": "Premium prawn biryani with tiger prawns, saffron rice, and caramelised onions. A rare Islamabad treat.", "image_url": IMG["biryani"], "latitude": 33.7050, "longitude": 73.0630},
    {"name": "Monal Mutton Pulao", "price": 900, "location": "Monal Restaurant, F-7, Islamabad", "description": "Tender slow-braised mutton pulao served at Islamabad's famous hilltop restaurant with a city-view terrace.", "image_url": IMG["pulao"], "latitude": 33.7204, "longitude": 73.0733},
    {"name": "Sanaullah Halwa Puri F-10", "price": 200, "location": "Sanaullah, F-10, Islamabad", "description": "Popular F-10 halwa puri spot. Crispy puris, sweet suji halwa, and spiced channay in one plate.", "image_url": IMG["breakfast"], "latitude": 33.7006, "longitude": 73.0202},
    {"name": "Dumpukht Mutton Handi", "price": 1500, "location": "Dumpukht, F-6, Islamabad", "description": "Slow dum-cooked mutton handi sealed with dough and baked. Intensely aromatic and melt-in-the-mouth.", "image_url": IMG["karahi"], "latitude": 33.7297, "longitude": 73.0918},
    {"name": "Charsi Tikka G-9 Special", "price": 800, "location": "Charsi Tikka, G-9, Islamabad", "description": "Famous G-9 chicken tikka marinated overnight in a secret yoghurt blend and grilled in a tandoor.", "image_url": IMG["kabab"], "latitude": 33.6864, "longitude": 73.0220},
    {"name": "Islamabad Waffle House Nutella", "price": 450, "location": "Waffle House, F-7, Islamabad", "description": "Golden crispy waffle generously spread with Nutella and topped with banana slices and powdered sugar.", "image_url": IMG["sweet"], "latitude": 33.7186, "longitude": 73.0720},
]
# fmt: on


def get_embedding(text: str) -> list:
    try:
        config = EmbedContentConfig(output_dimensionality=EMBEDDING_DIM)
        result = client.models.embed_content(model=EMBEDDING_MODEL, contents=text, config=config)
        return list(result.embeddings[0].values)
    except Exception as e:
        print(f"    WARNING: embedding failed ({e}), using zero vector")
        return [0.0] * EMBEDDING_DIM


def seed():
    db = SessionLocal()
    try:
        added = 0
        skipped = 0
        total = len(MEALS)
        print(f"Starting seed — {total} meals to process\n")

        for i, m in enumerate(MEALS, 1):
            exists = (
                db.query(Meal)
                .filter(Meal.name == m["name"], Meal.location == m["location"])
                .first()
            )
            if exists:
                print(f"  [{i}/{total}] SKIP  {m['name']}")
                skipped += 1
                continue

            text = f"{m['name']} at {m['location']}. {m['description']}"
            emb = get_embedding(text)
            time.sleep(0.25)  # stay within Gemini free-tier rate limits

            meal = Meal(
                name=m["name"],
                price=m["price"],
                location=m["location"],
                description=m["description"],
                image_url=m.get("image_url"),
                latitude=m.get("latitude"),
                longitude=m.get("longitude"),
                embedding=emb,
                confidence=95.0,
            )
            db.add(meal)
            db.commit()
            added += 1
            print(f"  [{i}/{total}] OK    {m['name']} — PKR {m['price']}")

        print(f"\nDone. Added: {added}  |  Skipped (already in DB): {skipped}")
    except Exception as e:
        print(f"\nERROR: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
