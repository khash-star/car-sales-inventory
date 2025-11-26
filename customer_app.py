from flask import Flask, render_template, request, redirect
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
app.config['SECRET_KEY'] = 'customer_app_key'
INVENTORY = load_inventory()

# --- ADMIN ROUTE (/admin) ---
@app.route("/admin")
def admin():
    # Админ сервисийн Render URL
    admin_url = "https://car-sales-inventory.onrender.com"
    
    # Вариант 1: iframe-ээр дотор нь ачаах (URL /admin хэвээр үлдэнэ)
    return f"""
    <html>
      <head>
        <title>Admin Panel</title>
        <style>
          html, body {{
            margin: 0;
            padding: 0;
            height: 100%;
          }}
          iframe {{
            border: none;
            width: 100%;
            height: 100vh;
          }}
        </style>
      </head>
      <body>
        <iframe src="{admin_url}"></iframe>
      </body>
    </html>
    """
    # Хэрвээ redirect байдлаар явуулахыг хүсвэл дээрхийг комментлоод,
    # доорх мөрийг үлдээнэ:
    # return redirect(admin_url)

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
        'customer_inventory.html',
        inventory=filtered_inventory, 
        title="Available Car Models",
        current_query=search_query,
        min_price=min_price, max_price=max_price, min_year=min_year, max_year=max_year
    )

# 2. New Car Details Route
@app.route('/car_details/<int:car_id>')
def car_details(car_id):
    """
    Renders a read-only detail page for a single car.
    """
    # Find the car in the INVENTORY list
    car_info = next((car for car in INVENTORY if car['id'] == car_id), None)

    if car_info is None:
        # Хэрэв машин олддохгүй бол алдаа гаргана
        return render_template('error.html', title="Car Not Found", 
                               message=f"Car with ID {car_id} not found in inventory."), 404
        
    return render_template(
        'customer_car_details.html',
        title=f"Details for {car_info['make']} {car_info['model']}", 
        car=car_info
    )

# 3. Run the application
if __name__ == '__main__':
    app.run(debug=True)

