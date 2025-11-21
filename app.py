from flask import Flask, render_template, request, redirect, url_for, flash, get_flashed_messages
import json
import os   

# Define the file path for our inventory data
INVENTORY_FILE = 'inventory.json'

# --- DATA PERSISTENCE FUNCTIONS ---

def load_inventory():
    """Loads the car inventory list from the JSON file."""
    if not os.path.exists(INVENTORY_FILE):
        return []
    
    with open(INVENTORY_FILE, 'r') as f:
        return json.load(f)

def save_inventory(inventory_list):
    """Saves the current car inventory list back into the JSON file."""
    with open(INVENTORY_FILE, 'w') as f:
        json.dump(inventory_list, f, indent=4)


# --- APPLICATION SETUP ---

app = Flask(__name__)
# *** SECRET_KEY: flash() функцийг ашиглахад заавал шаардлагатай ***
app.config['SECRET_KEY'] = 'your_strong_and_unique_secret_key' 

# Load the inventory once when the application starts
INVENTORY = load_inventory()

# Helper function to get the next ID for a new car
def get_next_id():
    """Calculates the next available ID based on the current INVENTORY."""
    if not INVENTORY:
        return 1
    return max(car['id'] for car in INVENTORY) + 1


# --- APPLICATION ROUTES ---

# 1. Main Inventory List Route with Search/Filter Logic
@app.route('/')
def list_inventory():
    """
    Renders the 'index.html' template. 
    Accepts a 'query' parameter for filtering the inventory.
    """
    search_query = request.args.get('query', '').lower()
    filtered_inventory = INVENTORY
    
    if search_query:
        results = []
        for car in INVENTORY:
            car_attributes = f"{car.get('make', '')} {car.get('model', '')} {car.get('year', '')} {car.get('color', '')}".lower()
            
            if search_query in car_attributes:
                results.append(car)
        
        filtered_inventory = results

    return render_template(
        'index.html', 
        inventory=filtered_inventory, 
        title="Current Car Inventory",
        current_query=search_query
    )

# 2. Add Car Route
@app.route('/add_car', methods=['GET', 'POST'])
def add_car():
    if request.method == 'POST':
        # --- Handle Form Submission (POST Request) ---
        new_car_data = {
            "id": get_next_id(), 
            "make": request.form['make'],
            "model": request.form['model'],
            "year": int(request.form['year']),
            "price": int(request.form['price']),
            "mileage": int(request.form['mileage']),
            "color": request.form['color']
        }
        
        INVENTORY.append(new_car_data)
        
        # *** Шинэ: Амжилттай нэмэх мэдэгдэл ***
        flash(f"Машин: {new_car_data['make']} {new_car_data['model']}-ийг амжилттай нэмлээ!", 'success')
        
        save_inventory(INVENTORY)
        return redirect(url_for('list_inventory'))
        
    return render_template('add_car.html', title="Add New Car")


# 3. Edit Car Route
@app.route('/edit_car/<int:car_id>', methods=['GET', 'POST'])
def edit_car(car_id):
    car_to_edit = next((car for car in INVENTORY if car['id'] == car_id), None)

    if car_to_edit is None:
        # Та error.html үүсгээгүй бол энэ нь алдаа өгч болно, гэхдээ логик нь зөв.
        return render_template('error.html', message=f"Car with ID {car_id} not found."), 404

    if request.method == 'POST':
        # --- Handle Form Submission (POST Request) ---
        
        # Update the car's details in the INVENTORY list
        car_to_edit['make'] = request.form['make']
        car_to_edit['model'] = request.form['model']
        car_to_edit['year'] = int(request.form['year'])
        car_to_edit['price'] = int(request.form['price'])
        car_to_edit['mileage'] = int(request.form['mileage'])
        car_to_edit['color'] = request.form['color']
        
        # *** Шинэ: Амжилттай засах мэдэгдэл ***
        flash(f"Машин: {car_to_edit['make']} {car_to_edit['model']}-ийн мэдээллийг амжилттай шинэчиллээ!", 'warning')
        
        save_inventory(INVENTORY)
        return redirect(url_for('list_inventory'))
        
    return render_template('edit_car.html', title=f"Edit Car ID {car_id}", car=car_to_edit)


# 4. Delete Car Route
@app.route('/delete_car/<int:car_id>', methods=['POST'])
def delete_car(car_id):
    global INVENTORY
    
    original_length = len(INVENTORY)
    
    # Машины мэдээллийг мэдэгдэлд ашиглахын тулд устгахаас өмнө авна.
    car_deleted_info = next((car for car in INVENTORY if car['id'] == car_id), None)
    
    INVENTORY[:] = [car for car in INVENTORY if car['id'] != car_id]
    
    if len(INVENTORY) < original_length:
        # *** Шинэ: Амжилттай устгах мэдэгдэл ***
        if car_deleted_info:
            flash(f"Машин: {car_deleted_info['make']} {car_deleted_info['model']}-ийг амжилттай устгалаа!", 'danger')
        else:
            flash(f"ID {car_id}-тай машиныг амжилттай устгалаа!", 'danger')

        save_inventory(INVENTORY)
    
    return redirect(url_for('list_inventory'))


# 5. Run the application
if __name__ == '__main__':
    app.run(debug=True)