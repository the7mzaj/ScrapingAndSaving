import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import re
import pandas as pd
import os
import sqlite3

# Database setup
DATABASE = 'users.db'

def init_db():
    """Initialize the database with users table"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def get_user_by_email(email):
    """Get user by email from database"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_user_by_id(user_id):
    """Get user by ID from database"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def create_user(email, first_name, last_name, password):
    """Create a new user in database"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (email, first_name, last_name, password)
        VALUES (?, ?, ?, ?)
    ''', (email, first_name, last_name, password))
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return user_id

class User(UserMixin):
    def __init__(self, user_id, email, first_name, last_name):
        self.id = user_id
        self.email = email
        self.first_name = first_name
        self.last_name = last_name

app = Flask(__name__)
app.secret_key = "asdasdad" #required, don't forget this!!!!
default_url = "https://www.ivory.co.il/catalog.php?act=cat&q="

# Initialize database
init_db()

search_cache = {}
CACHE_SIZE_LIMIT = 50

login_manager = LoginManager()
login_manager.init_app(app)

'''
Loads the user from the database.
'''
@login_manager.user_loader
def load_user(user_id):
    user_data = get_user_by_id(user_id)
    if user_data:
        # user_data is a tuple: (id, email, first_name, last_name, password, created_at)
        return User(user_data[0], user_data[1], user_data[2], user_data[3])
    return None

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        password = request.form.get('password')
        # Check if email already exists
        if get_user_by_email(email):
            flash('Email already registered!', 'error')
            return render_template('register.html')
        
        # Create new user
        hashed_password = generate_password_hash(password)
        user_id = create_user(email, first_name, last_name, hashed_password)
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Find user by email
        user_data = get_user_by_email(email)
        
        if user_data and check_password_hash(user_data[4], password):
            # Login successful - user_data is (id, email, first_name, last_name, password, created_at)
            user = User(user_data[0], user_data[1], user_data[2], user_data[3])
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password!', 'error')
            return render_template('login.html')
    
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    stats = {
        'total_products': 0, 
        'tracked_products': 0, 
        'price_alerts': 0  
    }
    return render_template('dashboard.html', user=current_user, stats=stats)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

'''
Scrapes the data from the given url and returns the html table using pandas.
'''

def scrape_data(url):

    if url in search_cache:
        print("Cache hit")
        return search_cache[url] #url is a key not an index

    print("Cache miss") #doesn't exist in cache, let's scrape it.

    headers = {
    'User-Agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36'
    }

    req = requests.get(url, headers= headers)
    parsing = BeautifulSoup(req.text, 'lxml')

    all_items = parsing.find_all('div', class_ = 'row p-1 entry-wrapper')
    item_names = [re.sub(r'[^a-zA-Z0-9\s]', '', item_name.find('div', class_ = 'col-md-12 col-12 title_product_catalog mb-md-1 main-text-area').text.strip()) for item_name in all_items]
    item_prices = [re.sub(r'[^0-9\s]', '', item_price.find('span', class_ = 'sr-only').text)+ "₪" for item_price in all_items]

    session['item_prices'] = item_prices
    session['item_names'] = item_names

    df = pd.DataFrame({
        "Select": [f'<label class="custom-checkbox"><input type="checkbox" name="row" value="{i}"><span class="checkmark"></span></label>' for i in range(len(item_names))],
        "Product": item_names,
        "Price": item_prices
    })

    result = df.to_html(classes="table", index=False, escape=False)

    #let's add the result to the cache
    if len(search_cache) >= CACHE_SIZE_LIMIT:
        oldest_key = next(iter(search_cache))
        del search_cache[oldest_key]

    search_cache[url] = result
    return result

'''
Returns the name of the item at the given index
'''
def items_indexer_name(idx):
    return session['item_names'][idx]

'''
Returns the price of the item at the given index
'''
def items_indexer_price(idx):
    return session['item_prices'][idx]

@app.route('/', methods=['GET', 'POST'])
def index():
    try:
        if request.method == 'POST':
            user_request = request.form.get("url")
            if not user_request or not user_request.strip(): #if empty or spaces only.
                return render_template('index.html', error="Please enter a product name.")
            
            url = default_url + user_request.strip()
            scraped_data = scrape_data(url)
            session['scraped_table'] = scraped_data
            session['requested_item'] = user_request
            return redirect(url_for('result'))
        
        return render_template('index.html', table=None)
    
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        return render_template('index.html', error="Unable to connect to the website. Please try again.")
    except Exception as e:
        print(f"Unexpected error: {e}")
        return render_template('index.html', error="An error occurred. Please try again.")
        
@app.route('/res', methods=['POST','GET'])
def result():

    if request.method == 'GET':
        table = session.pop('scraped_table', None)
        return render_template('index.html', table=table)

    return redirect(url_for('index'))

@app.route('/process', methods=['POST'])
def process():

    selected_products_result = []
    selected_products_prices = []

    url = default_url + session.pop('requested_item', None)
    selected_rows = request.form.getlist("row")  # [list] of checked values

    for i in range(len(selected_rows)):
        selected_rows[i] = int(selected_rows[i]) #casts to int because the form is a list of strings

    selected_rows_dict = dict.fromkeys(selected_rows)
    selected_rows_prices = dict.fromkeys(selected_rows)
    list_of_keys = list(selected_rows_dict.keys())
    list_of_prices = list(selected_rows_prices.keys())

    for i in range(len(selected_rows)):
        selected_rows_dict[i] = items_indexer_name(list_of_keys[i])
        selected_rows_prices[i] = items_indexer_price(list_of_prices[i])

    for key in selected_rows_dict:
        if selected_rows_dict[key] is None:
            continue
        selected_products_result.append(selected_rows_dict[key])
        selected_products_prices.append(selected_rows_prices[key])

    df = pd.DataFrame({
        "Tracked Products": selected_products_result,
        "Prices": selected_products_prices
    })

    table_html = df.to_html(classes="products-table", index=False, escape=False)
    
    return render_template('selected.html', table=table_html)

@app.route('/product/<product_name>')
def product_graph(product_name):
    # Decode the product name (replace underscores with spaces)
    decoded_name = product_name.replace('_', ' ')
    
    # For now, just return a simple message
    return f"<h1>Product: {decoded_name}</h1><p>This is where the price graph will be!</p><a href='/'>Back to Search</a>"

if __name__ == '__main__':
    #port = int(os.environ.get("PORT", 5))  # Render sets $PORT
    #app.run(host="0.0.0.0", port=port)
    app.run(debug=True)