from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'fallback-secret-key')

db_config = {
    'host': '127.0.0.1',
    'database': 'enquiry_system',
    'user': 'enquiry_user',
    'password': 'Abc@123',
    'port': 3306,
    'auth_plugin': 'mysql_native_password',
    'use_pure': True
}

def create_db_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        return connection
    except Error as e:
        print(f"MySQL Connection Error: {e}")
        return None

def init_db():
    connection = create_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS enquiries (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(100) NOT NULL,
                    phone VARCHAR(20) NOT NULL,
                    service VARCHAR(50) NOT NULL,
                    message TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    status VARCHAR(20) DEFAULT 'new'
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS subscribers (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    email VARCHAR(100) NOT NULL UNIQUE,
                    subscribed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS admin_users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) NOT NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("SELECT COUNT(*) FROM admin_users")
            if cursor.fetchone()[0] == 0:
                hashed_pw = generate_password_hash('admin123')
                cursor.execute(
                    "INSERT INTO admin_users (username, password_hash) VALUES (%s, %s)",
                    ('admin', hashed_pw)
                )
            
            connection.commit()
            print("Database initialized successfully")
        except Error as e:
            print(f"Database initialization error: {e}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

init_db()

def verify_admin(username, password):
    connection = create_db_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM admin_users WHERE username = %s", (username,))
        user = cursor.fetchone()
        return user and check_password_hash(user['password_hash'], password)
    except Error as e:
        print(f"Admin verification error: {e}")
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def login_required(f):
    def wrapper(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')


@app.route('/submit-enquiry', methods=['POST'])
def submit_enquiry():
    data = request.get_json()
    required_fields = ['name', 'email', 'phone', 'service', 'message']
    
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    connection = create_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor()
        query = """
            INSERT INTO enquiries (name, email, phone, service, message)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            data['name'].strip(),
            data['email'].strip(),
            data['phone'].strip(),
            data['service'].strip(),
            data['message'].strip()
        ))
        connection.commit()
        return jsonify({'success': True, 'message': 'Enquiry submitted successfully'}), 200
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/subscribe', methods=['POST'])
def subscribe():
    email = request.get_json().get('email', '').strip()
    
    if not email or '@' not in email:
        return jsonify({'error': 'Valid email is required'}), 400
    
    connection = create_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO subscribers (email) VALUES (%s) ON DUPLICATE KEY UPDATE is_active = TRUE",
            (email,)
        )
        connection.commit()
        return jsonify({'success': True, 'message': 'Subscribed successfully'}), 200
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if verify_admin(username, password):
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        return render_template('admin/login.html', error='Invalid credentials')
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    return render_template('admin/dashboard.html')

@app.route('/admin/enquiries')
@login_required
def admin_enquiries_list():
    connection = create_db_connection()
    if not connection:
        return render_template('admin/error.html', message='Database connection failed'), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        status_filter = request.args.get('status', 'all')
        search_query = request.args.get('search', '')
        
        query = "SELECT * FROM enquiries WHERE 1=1"
        params = []
        
        if status_filter != 'all':
            query += " AND status = %s"
            params.append(status_filter)
        
        if search_query:
            query += " AND (name LIKE %s OR email LIKE %s OR phone LIKE %s)"
            params.extend([f"%{search_query}%"] * 3)
        
        query += " ORDER BY created_at DESC"
        cursor.execute(query, params)
        enquiries = cursor.fetchall()
        
        cursor.execute("SELECT status, COUNT(*) as count FROM enquiries GROUP BY status")
        status_counts = cursor.fetchall()
        
        return render_template('admin/enquiries.html',
                            enquiries=enquiries,
                            status_counts=status_counts,
                            current_status=status_filter,
                            search_query=search_query)
    except Error as e:
        return render_template('admin/error.html', message=f"Error: {e}"), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/admin/enquiries/<int:enquiry_id>')
@login_required
def admin_enquiry_detail(enquiry_id):
    connection = create_db_connection()
    if not connection:
        return render_template('admin/error.html', message='Database connection failed'), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM enquiries WHERE id = %s", (enquiry_id,))
        enquiry = cursor.fetchone()
        
        if not enquiry:
            return render_template('admin/error.html', message='Enquiry not found'), 404
            
        return render_template('admin/view_enquiry.html', enquiry=enquiry)
    except Error as e:
        return render_template('admin/error.html', message=f"Error fetching enquiry: {e}"), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)