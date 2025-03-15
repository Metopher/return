from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
import heapq  # For Dijkstra's Algorithm

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Required for session management

# Function to get a new database connection
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",  # Add your MySQL password here
        database="returnloop"  # Updated database name
    )

# Graph Representation of Kochi (Distances in KM)
graph = {
    "Aluva": {"Edappally": 10, "Kakkanad": 14},
    "Edappally": {"Aluva": 10, "Kaloor": 6, "Kakkanad": 8},
    "Kaloor": {"Edappally": 6, "MG Road": 4},
    "MG Road": {"Kaloor": 4, "Fort Kochi": 11},
    "Fort Kochi": {"MG Road": 11, "Willingdon Island": 5},
    "Willingdon Island": {"Fort Kochi": 5, "Thevara": 6},
    "Thevara": {"Willingdon Island": 6, "Vyttila": 7},
    "Vyttila": {"Thevara": 7, "Kakkanad": 9, "Tripunithura": 6},
    "Kakkanad": {"Edappally": 8, "Aluva": 14, "Vyttila": 9},
    "Tripunithura": {"Vyttila": 6}
}

# Dijkstra's Algorithm to find the shortest distance
def dijkstra(graph, start, end):
    queue = [(0, start)]  # (distance, node)
    distances = {node: float('inf') for node in graph}
    distances[start] = 0
    visited = set()

    while queue:
        current_distance, current_node = heapq.heappop(queue)

        if current_node in visited:
            continue
        visited.add(current_node)

        if current_node == end:
            return current_distance  # Return total shortest distance

        for neighbor, weight in graph[current_node].items():
            distance = current_distance + weight
            if distance < distances[neighbor]:
                distances[neighbor] = distance
                heapq.heappush(queue, (distance, neighbor))

    return float('inf')  # No path found

# Home route
@app.route('/')
def home():
    user_name = session.get('name', None)  # Get the user's name from the session
    return render_template('home.html', user_name=user_name)

# Get Ride Route (Shortest Distance Calculation)
@app.route('/get_ride', methods=['GET', 'POST'])
def get_ride():
    user_name = session.get('name', None)
    if request.method == 'POST':
        start = request.form.get('start_location')
        destination = request.form.get('destination')

        # Debugging Output
        print(f"Ride Request - Start: {start}, Destination: {destination}")

        # Store ride details in the `rides` table
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO rides (start_location, destination, email) VALUES (%s, %s, %s)", 
                       (start, destination, session.get('email', 'anonymous')))  # Use session email
        conn.commit()
        conn.close()

        flash("Ride request submitted successfully!", "success")

    return render_template('get_ride.html', user_name=user_name)

# Pooling Route
@app.route('/pooling', methods=['GET', 'POST'])
def pooling():
    user_name = session.get('name', None)

    # Fetch all pooling options from the database with username instead of email
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT p.*, u.name as username 
        FROM pooling p 
        LEFT JOIN users u ON p.email = u.email 
        ORDER BY p.pickup, p.destination, p.date
    """)
    pooling_options = cursor.fetchall()
    conn.close()

    if request.method == 'POST':
        pickup = request.form.get('location')
        destination = request.form.get('destination')
        date = request.form.get('date')

        # Debugging Output
        print(f"Pooling Request - Pickup: {pickup}, Destination: {destination}, Date: {date}")

        # Store pooling details in the `pooling` table
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO pooling (pickup, destination, date, email) VALUES (%s, %s, %s, %s)", 
                       (pickup, destination, date, session.get('email', 'anonymous')))  # Use session email
        conn.commit()
        conn.close()

        flash("Pooling request submitted successfully!", "success")
        return redirect(url_for('pooling'))

    return render_template('pooling.html', user_name=user_name, pooling_options=pooling_options)

# Signup Route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        gender = request.form.get('gender')
        password = request.form.get('password')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            flash("Email already registered. Please log in.", "warning")
            conn.close()
            return redirect(url_for('login'))

        cursor.execute(
            "INSERT INTO users (name, email, phone, gender, password) VALUES (%s, %s, %s, %s, %s)", 
            (name, email, phone, gender, password)
        )
        conn.commit()
        conn.close()

        flash("Signup successful! Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('signup.html')

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['email'] = email  # Store email in session
            session['name'] = user[1]  # Store user's name in session
            flash("Login successful!", "success")
            return redirect(url_for('home'))
        else:
            flash("Login failed. Check your email or password.", "danger")

    return render_template('login.html')

# Logout Route
@app.route('/logout')
def logout():
    session.pop('email', None)  # Remove email from session
    session.pop('name', None)  # Remove name from session
    flash("Logged out successfully.", "info")
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)