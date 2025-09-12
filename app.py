import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import re
import pandas as pd
import os

users_db = {}
user_sessions = {}

class User(UserMixin):
    def __init__(self, user_id, email, first_name, last_name):
        self.id = user_id
        self.email = email
        self.first_name = first_name
        self.last_name = last_name

app = Flask(__name__)
app.secret_key = "asdasdad" #required, don't forget this!!!!
default_url = "https://www.ivory.co.il/catalog.php?act=cat&q="

search_cache = {}
CACHE_SIZE_LIMIT = 50

login_manager = LoginManager()
login_manager.init_app(app)

'''
Loads the user from the database.
'''
@login_manager.user_loader
def load_user(user_id):
    if user_id in users_db:
        user_data = users_db[user_id] #if the user exists in the db,
        return User(user_id, user_data['email'], user_data['first_name'], user_data['last_name']) #return it
    return None

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get form data
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        password = request.form.get('password')
        for user_id, user_data in users_db.items():
            if user_data['email'] == email:
                flash('Email already registered!', 'error')
                return render_template('register.html')
            
        user_id = str(len(users_db) + 1)
        hashed_password = generate_password_hash(password)

        users_db[user_id] = {
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'password': hashed_password
        }
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Find user by email
        user_found = None
        for user_id, user_data in users_db.items():
            if user_data['email'] == email:
                user_found = (user_id, user_data)
                break
        
        if user_found and check_password_hash(user_found[1]['password'], password):
            # Login successful
            user = User(user_found[0], user_found[1]['email'], 
                      user_found[1]['first_name'], user_found[1]['last_name'])
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