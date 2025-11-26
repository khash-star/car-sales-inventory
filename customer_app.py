from flask import Flask, render_template, request
import json
import os

# Define the file path for our inventory data (SELLER APP-тай адил файл)
INVENTORY_FILE = 'inventory.json'

# --- DATA PERSISTENCE FUNCTIONS (Уншихын тулд шаардлагатай) ---
def load_inventory():
    """Loads the car inventory list from the JSON file."""
    if not os.path.exists(INVENTORY_FILE):
        return []
    try:
        with open(INVENTORY_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

# --- APPLICATION SETUP ---
app = Flask(__name__)
# Энэ апп CRUD хийхгүй тул SECRET_KEY шаардлагагүй, гэхдээ байхад илүүдэхгүй.
app.config['SECRET_KEY'] = 'customer_app_key' 
INVENTORY = load_inventory()

# --- APPLICATION ROUTES ---

# 1. Main Inventory List Route with Search/Filter Logic
@app.route('/')
def customer_list_inventory():
    """Renders the read-only inventory list for customers."""
    
    # Query Parameter-үүдийг авах (Шүүлтүүрт зориулж)
    search_query = request.args.get('query', '').lower()
    min_price = request.args.get('min_price', type=int)
    max_price = request.args.get('max_price', type=int)
    min_year = request.args.get('min_year', type=int)
    max_year = request.args.get('max_year', type=int)
    
    results = [] 
    
    # Шүүлтүүрийн логик
    for car in INVENTORY:
        car_attributes = f"{car.get('make', '')} {car.get('model', '')} {car.get('year', '')} {car.get('color', '')}".lower()
        
        # A. Текстийн хайлт
        text_match = (not search_query) or (search_query in car_attributes)
        
        # B. Үнийн шүүлтүүр
        price_match = (min_price is None or car['price'] >= min_price) and \
                      (max_price is None or car['price'] <= max_price)
        
        # C. Оны шүүлтүүр
        year_match = (min_year is None or car['year'] >= min_year) and \
                     (max_year is None or car['year'] <= max_year)
        
        if text_match and price_match and year_match:
            results.append(car)
    
    filtered_inventory = results 

    return render_template(
        'customer_inventory.html', # Зөв темплейт рүү зааж байна
        inventory=filtered_inventory, 
        title="Available Car Models",
        current_query=search_query,
        min_price=min_price, max_price=max_price, min_year=min_year, max_year=max_year
    )

# 2. Run the application
if __name__ == '__main__':
    # Local-д 5001 порт дээр ажиллуулна (Conflict-гүй)
    app.run(debug=True, port=5001)