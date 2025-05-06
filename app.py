from flask import Flask, render_template, request, redirect, url_for, flash
import csv
import os

# Initialize Flask app
app = Flask(__name__)
app.secret_key = "supersecretkey"  # For flashing error messages

# Paths to the CSV files
USER_CSV = "database/users.csv"
TRANSACTION_CSV = "database/transactions.csv"
BUDGET_CSV = "database/budgets.csv"

# Ensure database directory exists
os.makedirs("database", exist_ok=True)

# If users.csv doesn't exist, create it
if not os.path.exists(USER_CSV):
    with open(USER_CSV, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["email", "password", "name"])  # CSV headers

# If transactions.csv doesn't exist, create it
if not os.path.exists(TRANSACTION_CSV):
    with open(TRANSACTION_CSV, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["email", "date", "title", "category", "amount"])

# If budgets.csv doesn't exist, create it
if not os.path.exists(BUDGET_CSV):
    with open(BUDGET_CSV, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["email", "budget"])
        writer.writeheader()


@app.route("/")
def home():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        # Authenticate user
        with open(USER_CSV, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row["email"] == email and row["password"] == password:
                    # Store the email of the logged-in user in the session
                    global current_user_email
                    current_user_email = email
                    return redirect(url_for("dashboard"))

        flash("Invalid email or password. Please try again.")
        return redirect(url_for("login"))

    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm-password"]

        if password != confirm_password:
            flash("Passwords do not match.")
            return redirect(url_for("register"))

        # Check if email already exists
        with open(USER_CSV, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row["email"] == email:
                    flash("Email already registered.")
                    return redirect(url_for("register"))

        # Save new user
        with open(USER_CSV, "a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([email, password, name])

        flash("Registration successful. Please login.")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/set-budget", methods=["GET", "POST"])
def set_budget():
    if not current_user_email:
        flash("Please login to set a budget.")
        return redirect(url_for("login"))

    if request.method == "POST":
        budget = request.form["budget"]

        # Save the budget associated with the current user
        budgets = {}

        # Load existing budgets
        with open(BUDGET_CSV, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                budgets[row["email"]] = row["budget"]

        # Update the current user's budget
        budgets[current_user_email] = budget

        # Write updated budgets back to the CSV file
        with open(BUDGET_CSV, "w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=["email", "budget"])
            writer.writeheader()
            for email, user_budget in budgets.items():
                writer.writerow({"email": email, "budget": user_budget})

        flash("Budget updated successfully.")
        return redirect(url_for("dashboard"))

    return render_template("set-budget.html")


@app.route("/dashboard")
def dashboard():
    if not current_user_email:
        flash("Please login to access the dashboard.")
        return redirect(url_for("login"))

    # Load user's budget
    user_budget = 0
    with open(BUDGET_CSV, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row["email"] == current_user_email:
                user_budget = float(row["budget"])
                break

    # Calculate total income and expenses from transactions
    total_income = 0
    total_expenses = 0
    transactions = []
    categories = {}

    with open(TRANSACTION_CSV, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row["email"] == current_user_email:
                transactions.append(row)
                amount = float(row["amount"])
                category = row["category"]

                if category == "income":
                    total_income += amount
                elif category == "expense":
                    total_expenses += amount

                # Aggregate data for chart
                if category not in categories:
                    categories[category] = 0
                categories[category] += amount

    # Calculate remaining budget
    remaining_budget = user_budget - total_expenses

    # Prepare data for chart
    chart_labels = list(categories.keys())
    chart_values = list(categories.values())

    return render_template(
        "dashboard.html",
        remaining_budget=remaining_budget,
        total_income=total_income,
        total_expenses=total_expenses,
        transactions=transactions,
        chart_labels=chart_labels,
        chart_values=chart_values,
    )


@app.route("/add-transaction", methods=["GET", "POST"])
def add_transaction():
    if not current_user_email:
        flash("Please login to add a transaction.")
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form["title"]
        amount = request.form["amount"]
        category = request.form["category"]
        date = request.form["date"]

        # Save transaction
        with open(TRANSACTION_CSV, "a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([current_user_email, date, title, category, amount])

        flash("Transaction added successfully.")
        return redirect(url_for("dashboard"))

    return render_template("add-transaction.html")


@app.route("/reports")
def reports():
    if not current_user_email:
        flash("Please login to view reports.")
        return redirect(url_for("login"))

    transactions = []
    with open(TRANSACTION_CSV, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row["email"] == current_user_email:  # Filter by logged-in user's email
                transactions.append(row)

    return render_template("reports.html", transactions=transactions)


if __name__ == "__main__":
    current_user_email = None  # Global variable to store the logged-in user's email
    app.run(debug=True)