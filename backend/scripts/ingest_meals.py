import sys
import os
import json
from google import genai
from google.genai.types import EmbedContentConfig
from dotenv import load_dotenv

# Add the app directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.core.database import engine, SessionLocal
from app.models.meal import Meal

load_dotenv()

# Configure Gemini using new SDK
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    print("GOOGLE_API_KEY not found in environment variables.")
    sys.exit(1)

client = genai.Client(api_key=GOOGLE_API_KEY)

SEED_DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "islamabad_meals.json")
EMBEDDING_DIMENSIONS = 1536
EMBEDDING_MODEL = "text-embedding-004"

MOCK_MEALS = [
    {
        "name": "Student Biryani",
        "price": 250,
        "location": "F-8 Markaz, Islamabad",
        "description": "Authentic spicy Karachi-style biryani with a tender chicken piece and a perfectly cooked potato. Great value for money.",
        "image_url": "https://images.unsplash.com/photo-1563379091339-03b21bc4a4f8?q=80&w=400",
        "latitude": 33.6932,
        "longitude": 73.0323
    },
    {
        "name": "Cheezious Crown Crust",
        "price": 1250,
        "location": "G-9 Markaz, Islamabad",
        "description": "Premium large pizza with a unique cheesy crown crust, loaded with spicy chicken chunks, olives, and bell peppers.",
        "image_url": "https://images.unsplash.com/photo-1513104890138-7c749659a591?q=80&w=400",
        "latitude": 33.6880,
        "longitude": 73.0236
    },
    {
        "name": "Savour Foods Pulao",
        "price": 450,
        "location": "Blue Area, Islamabad",
        "description": "The legendary Savour pulao served with two shami kababs, fresh salad, and raita. The ultimate Islamabad comfort food.",
        "image_url": "https://images.unsplash.com/photo-1633945274405-b6c8069047b0?q=80&w=400",
        "latitude": 33.7154,
        "longitude": 73.0734
    },
    {
        "name": "Nagina Burger (Anday Wala)",
        "price": 180,
        "location": "Saddar, Rawalpindi",
        "description": "Classic street-style bun kabab with a spicy lentil patty, fried egg, and tangy mint chutney.",
        "image_url": "https://images.unsplash.com/photo-1550547660-d9450f859349?q=80&w=400",
        "latitude": 33.5951,
        "longitude": 73.0616
    },
    {
        "name": "Refreshing Sweet Lassi",
        "price": 150,
        "location": "Kartarpura, Rawalpindi",
        "description": "Traditional thick and creamy sweet lassi served in a large chilled glass. Perfect for beating the heat.",
        "image_url": "https://images.unsplash.com/photo-1571115177098-24ec42ed204d?q=80&w=400",
        "latitude": 33.6126,
        "longitude": 73.0679
    },
    {
        "name": "Chicken Karahi (Half)",
        "price": 950,
        "location": "Butt Karahi, F-8",
        "description": "Freshly prepared chicken karahi cooked in butter and tomatoes with ginger and green chilies.",
        "image_url": "https://images.unsplash.com/photo-1603894584214-5d30baf39446?q=80&w=400",
        "latitude": 33.6937,
        "longitude": 73.0328
    },
    {
        "name": "Beef Nihari",
        "price": 600,
        "location": "Muhammadi Nihari, G-9",
        "description": "Slow-cooked beef nihari with rich, spicy gravy, topped with ginger, lemon, and fried onions.",
        "image_url": "https://images.unsplash.com/photo-1545243424-0ce743321e11?q=80&w=400",
        "latitude": 33.6882,
        "longitude": 73.0242
    },
    {
        "name": "Special Afghani Burger",
        "price": 350,
        "location": "E-11 Markaz",
        "description": "Huge Afghan-style wrap with fries, sausage, egg, and special Afghan sauces wrapped in a flatbread.",
        "image_url": "https://images.unsplash.com/photo-1521390188846-e2a3a97453a0?q=80&w=400",
        "latitude": 33.7015,
        "longitude": 72.9984
    },
    {
        "name": "Tawa Chicken",
        "price": 400,
        "location": "Arif Chatkhara, Commercial Market",
        "description": "Spicy shredded chicken cooked on a tawa with plenty of masalas and oil. Very flavorful and intense.",
        "image_url": "https://images.unsplash.com/photo-1596797038530-2c39bb9ed0b1?q=80&w=400",
        "latitude": 33.7214,
        "longitude": 73.0602
    },
    {
        "name": "Dahi Bhallay",
        "price": 150,
        "location": "Jamil Sweets, F-10",
        "description": "Soft lentil dumplings in sweet and tangy yogurt with papri, chickpeas, and special spices.",
        "image_url": "https://images.unsplash.com/photo-1589113103503-49453adfd15d?q=80&w=400",
        "latitude": 33.6996,
        "longitude": 73.0192
    }
]

def load_seed_data():
    if os.path.exists(SEED_DATA_PATH):
        with open(SEED_DATA_PATH, "r", encoding="utf-8") as handle:
            return json.load(handle)
    return MOCK_MEALS

def get_embedding(text_to_embed):
    """Generate embeddings using Gemini with a safe fallback."""
    try:
        config = EmbedContentConfig(output_dimensionality=EMBEDDING_DIMENSIONS)
        result = client.models.embed_content(model=EMBEDDING_MODEL, contents=text_to_embed, config=config)
        return list(result.embeddings[0].values)
    except Exception as e:
        print(f"Error getting embedding: {e}")
        return [0.0] * EMBEDDING_DIMENSIONS

def ingest_data():
    db = SessionLocal()
    try:
        seed_meals = load_seed_data()
        print(f"Starting ingestion of {len(seed_meals)} meals...")
        
        # Clear existing meals to avoid duplicates during testing
        db.query(Meal).delete()
        db.commit()
        
        for meal_data in seed_meals:
            print(f"Processing: {meal_data['name']}")
            
            # Create a combined string for semantic embedding
            # We include name, location, and description to make the search richer
            search_context = f"{meal_data['name']} at {meal_data['location']}. {meal_data['description']}"
            
            embedding = get_embedding(search_context)
            
            new_meal = Meal(
                name=meal_data["name"],
                price=meal_data["price"],
                location=meal_data["location"],
                description=meal_data["description"], # Note: Description needs to be added to Model
                image_url=meal_data["image_url"],
                latitude=meal_data.get("latitude"),
                longitude=meal_data.get("longitude"),
                embedding=embedding,
                confidence=95.0
            )
            db.add(new_meal)
        
        db.commit()
        print("Ingestion complete!")
        
    except Exception as e:
        print(f"Error during ingestion: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    ingest_data()
