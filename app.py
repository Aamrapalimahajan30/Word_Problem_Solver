from flask import Flask, render_template, request, redirect, session
import mysql.connector
import re
from sympy import symbols, solve
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- DB CONNECTION ----------------
def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Aachu30@",
        database="problem"
    )

# ---------------- WORD → NUMBER ----------------
word_numbers = {
    "zero":0,"one":1,"two":2,"three":3,"four":4,"five":5,
    "six":6,"seven":7,"eight":8,"nine":9,"ten":10,
    "eleven":11,"twelve":12,"thirteen":13,"fourteen":14,
    "fifteen":15,"sixteen":16,"seventeen":17,"eighteen":18,
    "nineteen":19,"twenty":20
}

plus = ["add","sum","total","more","together"]
sub = ["left","remain","less","difference"]
multi = ["each","times","per"]
div = ["divide","split","equally"]

# ---------------- CATEGORY ----------------
def detect_category(text):
    text = text.lower()
    if "x" in text:
        return "Algebra"
    elif "area" in text:
        return "Area"
    elif "volume" in text:
        return "Volume"
    elif "ratio" in text:
        return "Ratio"
    else:
        return "Arithmetic"

# ---------------- SOLVER ----------------
def solve_problem(text):
    category = detect_category(text)
    text = text.lower()

    try:
        # -------- ALGEBRA --------
        if category == "Algebra":
            x = symbols('x')
            eq = text.replace("=", "-(") + ")"
            result = solve(eval(eq), x)
            return f"Solution: x = {result}"

        # -------- AREA --------
        elif category == "Area":
            nums = list(map(int, re.findall(r'\d+', text)))

            if "circle" in text:
                r = nums[0]
                return f"Area of Circle = {3.14 * r * r}"

            elif "rectangle" in text:
                return f"Area of Rectangle = {nums[0] * nums[1]}"

        # -------- VOLUME --------
        elif category == "Volume":
            nums = list(map(int, re.findall(r'\d+', text)))

            if "cube" in text:
                return f"Volume of Cube = {nums[0]**3}"

        # -------- RATIO --------
        elif category == "Ratio":
            nums = list(map(int, re.findall(r'\d+', text)))
            return f"Ratio = {nums[0]}:{nums[1]}"

        # -------- NEW SMART ARITHMETIC --------
        else:
            nums = list(map(int, re.findall(r'\d+', text)))

            if len(nums) < 2:
                return "Not enough numbers"

            # ADDITION
            if any(k in text for k in ["add", "plus", "sum", "total", "together", "all", "in all"]):
                return f"Answer = {sum(nums)}"

            # SUBTRACTION
            elif any(k in text for k in ["left", "remain", "less", "difference", "subtract", "minus"]):
                return f"Answer = {nums[0] - nums[1]}"

            # MULTIPLICATION
            elif any(k in text for k in ["times", "each", "per", "multiply"]):
                return f"Answer = {nums[0] * nums[1]}"

            # DIVISION
            elif any(k in text for k in ["divide", "equally", "split"]):
                if nums[1] == 0:
                    return "Error: Division by zero"
                return f"Answer = {nums[0] / nums[1]}"

            else:
                return "Operation not recognized"

    except Exception as e:
        return "Error solving problem"
# ---------------- HOME ----------------
@app.route("/", methods=["GET", "POST"])
def index():
    if "user" not in session:
        return redirect("/login")

    result = ""

    if request.method == "POST":
        problem = request.form["problem"]

        result = solve_problem(problem)
        category = detect_category(problem)

        db = get_db()
        cursor = db.cursor()

        try:
            cursor.execute(
                "INSERT INTO problems (user_id, problem, result, category) VALUES (%s,%s,%s,%s)",
                (session["user_id"], problem, result, category)
            )
            db.commit()

        except Exception as e:
            db.rollback()

        finally:
            cursor.close()
            db.close()

    return render_template("index.html", result=result)

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db()
        cursor = db.cursor()

        try:
            cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
            user = cursor.fetchone()

        finally:
            cursor.close()
            db.close()

        if user is None:
            error = "User not found"
        elif not check_password_hash(user[2], password):
            error = "Invalid password"
        else:
            session["user"] = username
            session["user_id"] = user[0]
            return redirect("/")

    return render_template("login.html", error=error)

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        db = get_db()
        cursor = db.cursor()

        try:
            cursor.execute(
                "INSERT INTO users (username,password) VALUES (%s,%s)",
                (username, password)
            )
            db.commit()

        finally:
            cursor.close()
            db.close()

        return redirect("/login")

    return render_template("register.html")

# ---------------- HISTORY ----------------
@app.route("/history")
def history():
    if "user" not in session:
        return redirect("/login")

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute(
            "SELECT problem, result, category FROM problems WHERE user_id=%s",
            (session["user_id"],)
        )
        data = cursor.fetchall()

    finally:
        cursor.close()
        db.close()

    return render_template("history.html", data=data)

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# clear history
@app.route("/clear-history", methods=["POST"])
def clear_history():
    if "user" not in session:
        return redirect("/login")

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute(
            "DELETE FROM problems WHERE user_id=%s",
            (session["user_id"],)
        )
        db.commit()
    finally:
        cursor.close()
        db.close()

    return redirect("/history")

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)