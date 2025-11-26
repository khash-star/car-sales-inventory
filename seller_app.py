from flask import Flask, render_template, request, redirect, url_for, flash
import json
import os 
import datetime 

# --- CONFIGURATION ---

# Define the file path for our inventory data
INVENTORY_FILE = 'inventory.json'
# --- DATA PERSISTENCE FUNCTIONS ---

def load_inventory():
    # ... (load_inventory function is unchanged)
    if not os.path.exists(INVENTORY_FILE):
        return []
    try:
        with open(INVENTORY_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def save_inventory(inventory_list):
    # ... (save_inventory function is unchanged)
    with open(INVENTORY_FILE, 'w') as f:
        json.dump(inventory_list, f, indent=4)


# --- APPLICATION SETUP ---

# Аппликейшний нэр
app = Flask(__name__) 
app.config['SECRET_KEY'] = 'your_strong_and_unique_secret_key' 

# Load the inventory once when the application starts
INVENTORY = load_inventory()

# Helper function to get the next ID for a new car
def get_next_id():
    # ... (get_next_id function is unchanged)
    if not INVENTORY:
        return 1
    return max(car['id'] for car in INVENTORY) + 1


# --- ROUTING HELPER FUNCTION (Шүүлтүүрийн логикийг давтахгүй байхын тулд) ---

def filter_inventory(search_query, min_price, max_price, min_year, max_year):
    # ... (filter_inventory function is unchanged)
    results = []
    for car in INVENTORY:
        # Text Search
        car_attributes = f"{car.get('make', '')} {car.get('model', '')} {car.get('year', '')} {car.get('color', '')}".lower()
        text_match = (not search_query) or (search_query in car_attributes)
        
        # Price Filter
        price_match = (min_price is None or car['price'] >= min_price) and \
                      (max_price is None or car['price'] <= max_price)
            
        # Year Filter
        year_match = (min_year is None or car['year'] >= min_year) and \
                     (max_year is None or car['year'] <= max_year)

        if text_match and price_match and year_match:
            results.append(car)
    return results


# --- CUSTOMER (ХЭРЭГЛЭГЧ) ROUTES ---

## 1. Үндсэн хуудас (Read-Only)
@app.route('/')
def customer_list_inventory():
    """Renders the 'customer_inventory.html' (Read-Only mode) template."""
    
    # Query Parameter-үүдийг авах
    search_query = request.args.get('query', '').lower()
    min_price = request.args.get('min_price', type=int)
    max_price = request.args.get('max_price', type=int)
    min_year = request.args.get('min_year', type=int)
    max_year = request.args.get('max_year', type=int)
    
    # Шүүлтүүрийн логикийг дуудна
    filtered_inventory = filter_inventory(search_query, min_price, max_price, min_year, max_year)
    
    return render_template(
        'customer_inventory.html', 
        inventory=filtered_inventory, 
        title="Available Car Models",
        current_query=search_query,
        min_price=min_price, max_price=max_price, min_year=min_year, max_year=max_year,
    )


# --- ADMIN/SELLER (УДИРДАХ) ROUTES ---

## 2. Admin Dashboard (CRUD үйлдлүүдтэй үндсэн хуудас)
@app.route('/admin')
def admin_list_inventory():
    """Renders the 'seller_inventory.html' (Admin mode) template with filtering options."""
    
    # Query Parameter-үүдийг авах
    search_query = request.args.get('query', '').lower()
    min_price = request.args.get('min_price', type=int)
    max_price = request.args.get('max_price', type=int)
    min_year = request.args.get('min_year', type=int)
    max_year = request.args.get('max_year', type=int)
    
    # Шүүлтүүрийн логикийг дуудна
    filtered_inventory = filter_inventory(search_query, min_price, max_price, min_year, max_year)
    
    return render_template(
        'seller_inventory.html', 
        inventory=filtered_inventory, 
        title="Current Car Inventory (Admin)",
        current_query=search_query,
        min_price=min_price, max_price=max_price, min_year=min_year, max_year=max_year,
        is_admin=True 
    )


## 3. Add Car Route (Admin)
@app.route('/admin/add_car', methods=['GET', 'POST'])
def admin_add_car(): # <--- Функцын нэрийг admin_add_car болгож өөрчлөв!
    if request.method == 'POST':
        # --- INPUT VALIDATION ---
        try:
            year = int(request.form['year'])
            price = int(request.form['price'])
            mileage = int(request.form['mileage'])
        except ValueError:
            flash("Үнэ, Он, Гүйлтийн утгууд заавал тоо байх ёстой.", 'danger')
            return redirect(url_for('admin_add_car')) # <--- Дуудлагыг шинэчлэв

        current_year = datetime.datetime.now().year
        
        if price < 0 or mileage < 0 or year > current_year:
            if price < 0 or mileage < 0:
                flash("Үнэ болон гүйлтийн утгууд сөрөг тоо байж болохгүй.", 'danger')
            if year > current_year:
                flash(f"Он (Year) нь {current_year}-аас их байж болохгүй.", 'danger')
            
            return redirect(url_for('admin_add_car')) # <--- Дуудлагыг шинэчлэв
        
        # --- END VALIDATION ---
        
        new_car_data = {
            "id": get_next_id(), 
            "make": request.form['make'],
            "model": request.form['model'],
            "year": year,
            "price": price,
            "mileage": mileage,
            "color": request.form['color']
        }
        
        INVENTORY.append(new_car_data)
        flash(f"Машин: {new_car_data['make']} {new_car_data['model']}-ийг амжилттай нэмлээ!", 'success')
        save_inventory(INVENTORY)
        
        return redirect(url_for('admin_list_inventory')) 
        
    return render_template('seller_inventory_add.html', title="Add New Car") 


## 4. Edit Car Route (Admin)
@app.route('/admin/edit_car/<int:car_id>', methods=['GET', 'POST'])
def admin_edit_car(car_id): # <--- Функцын нэрийг admin_edit_car болгож өөрчлөв!
    car_to_edit = next((car for car in INVENTORY if car['id'] == car_id), None)

    if car_to_edit is None:
        flash(f"Car with ID {car_id} not found.", 'danger')
        return redirect(url_for('admin_list_inventory')) 

    if request.method == 'POST':
        # --- INPUT VALIDATION ---
        try:
            year = int(request.form['year'])
            price = int(request.form['price'])
            mileage = int(request.form['mileage'])
        except ValueError:
            flash("Үнэ, Он, Гүйлтийн утгууд заавал тоо байх ёстой.", 'danger')
            return redirect(url_for('admin_edit_car', car_id=car_id)) # <--- Дуудлагыг шинэчлэв

        current_year = datetime.datetime.now().year
        
        if price < 0 or mileage < 0 or year > current_year:
            if price < 0 or mileage < 0:
                flash("Үнэ болон гүйлтийн утгууд сөрөг тоо байж болохгүй.", 'danger')
            if year > current_year:
                flash(f"Он (Year) нь {current_year}-аас их байж болохгүй.", 'danger')
                
            return redirect(url_for('admin_edit_car', car_id=car_id)) # <--- Дуудлагыг шинэчлэв
        
        # Update the car's details
        car_to_edit['make'] = request.form['make']
        car_to_edit['model'] = request.form['model']
        car_to_edit['year'] = year
        car_to_edit['price'] = price
        car_to_edit['mileage'] = mileage
        car_to_edit['color'] = request.form['color']
        
        flash(f"Машин: {car_to_edit['make']} {car_to_edit['model']}-ийн мэдээллийг амжилттай шинэчиллээ!", 'success')
        
        save_inventory(INVENTORY)
        return redirect(url_for('admin_list_inventory')) 
        
    return render_template('seller_inventory_edit.html', title=f"Edit Car ID {car_id}", car=car_to_edit) 


## 5. Delete Car Route (Admin)
@app.route('/admin/delete_car/<int:car_id>', methods=['POST'])
def admin_delete_car(car_id): # <--- Функцын нэрийг admin_delete_car болгож өөрчлөв!
    global INVENTORY
    
    original_length = len(INVENTORY)
    car_deleted_info = next((car for car in INVENTORY if car['id'] == car_id), None)
    
    INVENTORY[:] = [car for car in INVENTORY if car['id'] != car_id]
    
    if len(INVENTORY) < original_length:
        if car_deleted_info:
            flash(f"Машин: {car_deleted_info['make']} {car_deleted_info['model']}-ийг амжилттай устгалаа!", 'danger')
        else:
            flash(f"ID {car_id}-тай машиныг амжилттай устгалаа!", 'danger')

        save_inventory(INVENTORY)
    
    return redirect(url_for('admin_list_inventory')) 


# 6. Run the application (Local Development-д зориулсан)
if __name__ == '__main__':
    app.run(debug=True)