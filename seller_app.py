from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
)
import json
import os
import datetime  # Validation-д хэрэгтэй
from functools import wraps

# =========================
#  ТОХИРГОО
# =========================

# Inventory JSON файл
INVENTORY_FILE = "inventory.json"

# Админ нэвтрэх нэр, нууц үг
# Хүсвэл дараа нь Render → Environment variables хэсэгтээс ADMIN_USERNAME/ADMIN_PASSWORD гэж өгөөд
# эндээс os.environ.get(...) ашиглаад уншиж болно.
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")


# =========================
#  DATA PERSISTENCE
# =========================

def load_inventory():
    """Loads the car inventory list from the JSON file."""
    if not os.path.exists(INVENTORY_FILE):
        return []
    try:
        with open(INVENTORY_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []


def save_inventory(inventory_list):
    """Saves the current car inventory list back into the JSON file."""
    with open(INVENTORY_FILE, "w") as f:
        json.dump(inventory_list, f, indent=4)


# =========================
#  APP SETUP
# =========================

app = Flask(__name__)
app.config["SECRET_KEY"] = "your_strong_and_unique_secret_key"

# iframe-ээр дуудахад блоклохгүй байлгах header-ууд
@app.after_request
def allow_iframe(response):
    # X-Frame-Options-ийг ALLOWALL болгож, iframe-ийг зөвшөөрнө
    response.headers["X-Frame-Options"] = "ALLOWALL"
    # CSP дээр frame-ancestors-д бүх домэйнийг зөвшөөрнө (шаардлагатай бол нарийсгаж болно)
    response.headers["Content-Security-Policy"] = "frame-ancestors *"
    return response


# Inventory-г апп стартан дээр нэг ачаалж авна
INVENTORY = load_inventory()


def get_next_id():
    """Calculates the next available ID based on the current INVENTORY."""
    if not INVENTORY:
        return 1
    return max(car["id"] for car in INVENTORY) + 1


# =========================
#  LOGIN ХАМГААЛАЛТ
# =========================

def login_required(view_func):
    """Энгийн login шалгах decorator."""
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    return wrapped_view


# =========================
#  AUTH ROUTES
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["logged_in"] = True
            session["username"] = username
            flash("Амжилттай нэвтэрлээ.", "success")
            return redirect(url_for("list_inventory"))
        else:
            flash("Нэвтрэх нэр эсвэл нууц үг буруу байна.", "danger")
            return redirect(url_for("login"))

    # GET хүсэлт → Login form харуулна
    return render_template("login.html", title="Admin Login")


@app.route("/logout")
def logout():
    session.clear()
    flash("Амжилттай гарлаа.", "info")
    return redirect(url_for("login"))


# =========================
#  APPLICATION ROUTES
# =========================

# 1. Main Inventory List Route with Search/Filter Logic
@app.route("/")
@login_required
def list_inventory():
    """
    Renders the 'seller_inventory.html' template with filtering options.
    Guest Mode-ийг дэмжсэн хувилбар (одоо бол админд л хамаатай).
    """
    is_guest = request.args.get("guest", "").lower() == "true"

    # Query Parameter-үүдийг авах
    search_query = request.args.get("query", "").lower()
    min_price = request.args.get("min_price", type=int)
    max_price = request.args.get("max_price", type=int)
    min_year = request.args.get("min_year", type=int)
    max_year = request.args.get("max_year", type=int)

    # 1. Шүүлтүүрийн үр дүнг хадгалах жагсаалт
    results = []

    # 2. Бүх INVENTORY-г давтаж, шүүлтүүрийг хэрэгжүүлэх
    for car in INVENTORY:
        # A. Үндсэн хайлт (Text Search)
        car_attributes = (
            f"{car.get('make', '')} "
            f"{car.get('model', '')} "
            f"{car.get('year', '')} "
            f"{car.get('color', '')}"
        ).lower()
        text_match = (not search_query) or (search_query in car_attributes)

        # B. Үнийн шүүлтүүр (Price Range)
        price_match = (min_price is None or car["price"] >= min_price) and (
            max_price is None or car["price"] <= max_price
        )

        # C. Оны шүүлтүүр (Year Range)
        year_match = (min_year is None or car["year"] >= min_year) and (
            max_year is None or car["year"] <= max_year
        )

        # D. Бүх шүүлтүүр таарч байвал нэмнэ
        if text_match and price_match and year_match:
            results.append(car)

    filtered_inventory = results

    return render_template(
        "seller_inventory.html",
        inventory=filtered_inventory,
        title="Current Car Inventory",
        current_query=search_query,
        min_price=min_price,
        max_price=max_price,
        min_year=min_year,
        max_year=max_year,
        is_guest=is_guest,
    )


# 2. Add Car Route (Validation-тай)
@app.route("/add_car", methods=["GET", "POST"])
@login_required
def add_car():
    if request.method == "POST":
        # --- INPUT VALIDATION (УТГА ШАЛГАЛТ) ---
        try:
            year = int(request.form["year"])
            price = int(request.form["price"])
            mileage = int(request.form["mileage"])
        except ValueError:
            flash("Үнэ, Он, Гүйлтийн утгууд заавал тоо байх ёстой.", "danger")
            return redirect(url_for("add_car"))

        current_year = datetime.datetime.now().year

        if price < 0 or mileage < 0 or year > current_year:
            if price < 0 or mileage < 0:
                flash("Үнэ болон гүйлтийн утгууд сөрөг тоо байж болохгүй.", "danger")
            if year > current_year:
                flash(f"Он (Year) нь {current_year}-аас их байж болохгүй.", "danger")

            return redirect(url_for("add_car"))

        # --- END VALIDATION ---

        new_car_data = {
            "id": get_next_id(),
            "make": request.form["make"],
            "model": request.form["model"],
            "year": year,
            "price": price,
            "mileage": mileage,
            "color": request.form["color"],
        }

        INVENTORY.append(new_car_data)
        flash(
            f"Машин: {new_car_data['make']} {new_car_data['model']}-ийг амжилттай нэмлээ!",
            "success",
        )
        save_inventory(INVENTORY)
        return redirect(url_for("list_inventory"))

    return render_template("seller_inventory_add.html", title="Add New Car")


# 3. Edit Car Route (Validation-тай)
@app.route("/edit_car/<int:car_id>", methods=["GET", "POST"])
@login_required
def edit_car(car_id):
    car_to_edit = next((car for car in INVENTORY if car["id"] == car_id), None)

    if car_to_edit is None:
        flash(f"Car with ID {car_id} not found.", "danger")
        return redirect(url_for("list_inventory"))

    if request.method == "POST":
        # --- INPUT VALIDATION (УТГА ШАЛГАЛТ) ---
        try:
            year = int(request.form["year"])
            price = int(request.form["price"])
            mileage = int(request.form["mileage"])
        except ValueError:
            flash("Үнэ, Он, Гүйлтийн утгууд заавал тоо байх ёстой.", "danger")
            return redirect(url_for("edit_car", car_id=car_id))

        current_year = datetime.datetime.now().year

        if price < 0 or mileage < 0 or year > current_year:
            if price < 0 or mileage < 0:
                flash("Үнэ болон гүйлтийн утгууд сөрөг тоо байж болохгүй.", "danger")
            if year > current_year:
                flash(f"Он (Year) нь {current_year}-аас их байж болохгүй.", "danger")

            return redirect(url_for("edit_car", car_id=car_id))
        # --- END VALIDATION ---

        # Update the car's details
        car_to_edit["make"] = request.form["make"]
        car_to_edit["model"] = request.form["model"]
        car_to_edit["year"] = year
        car_to_edit["price"] = price
        car_to_edit["mileage"] = mileage
        car_to_edit["color"] = request.form["color"]

        flash(
            f"Машин: {car_to_edit['make']} {car_to_edit['model']}-ийн мэдээллийг амжилттай шинэчиллээ!",
            "success",
        )

        save_inventory(INVENTORY)
        return redirect(url_for("list_inventory"))

    return render_template(
        "seller_inventory_edit.html",
        title=f"Edit Car ID {car_id}",
        car=car_to_edit,
    )


# 4. Delete Car Route
@app.route("/delete_car/<int:car_id>", methods=["POST"])
@login_required
def delete_car(car_id):
    global INVENTORY

    original_length = len(INVENTORY)
    car_deleted_info = next((car for car in INVENTORY if car["id"] == car_id), None)

    INVENTORY[:] = [car for car in INVENTORY if car["id"] != car_id]

    if len(INVENTORY) < original_length:
        if car_deleted_info:
            flash(
                f"Машин: {car_deleted_info['make']} {car_deleted_info['model']}-ийг амжилттай устгалаа!",
                "danger",
            )
        else:
            flash(f"ID {car_id}-тай машиныг амжилттай устгалаа!", "danger")

        save_inventory(INVENTORY)

    return redirect(url_for("list_inventory"))


# Local хөгжүүлэлтэд зориулсан run (Render дээр ашиглагдахгүй, зүгээр үлдээсэн)
if __name__ == "__main__":
    app.run(debug=True)
