import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, redirect, url_for, session
import re
import pandas as pd

app = Flask(__name__)
app.secret_key = "balasha" #required, don't forget this!!!!
default_url = "https://www.ivory.co.il/catalog.php?act=cat&q="

def scrape_data(url):

    headers = {
    'User-Agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36'
    }

    req = requests.get(url, headers= headers)

    parsing = BeautifulSoup(req.text, 'lxml')

    all_items = parsing.find_all('div', class_ = 'row p-1 entry-wrapper')

    item_names = [re.sub(r'[^a-zA-Z0-9\s]', '', item_name.find('div', class_ = 'col-md-12 col-12 title_product_catalog mb-md-1 main-text-area').text.strip()) for item_name in all_items]
    item_prices = [re.sub(r'[^0-9\s]', '', item_price.find('span', class_ = 'sr-only').text)+ "₪" for item_price in all_items]

    df = pd.DataFrame(columns= ["Select","Product","Price"])
    df["Select"] = [f'<input type="checkbox" name="row" value="{i}">' for i in range(len(item_names))]
    df["Product"] = item_names
    df["Price"] = item_prices

    return df.to_html(classes="table", index=False, escape=False)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = default_url
        url += request.form.get("url")
        scraped_data = scrape_data(url)
        session['scraped_table'] = scraped_data
        return redirect(url_for('result'))
    return render_template('index.html', table=None)

@app.route('/res', methods=['POST','GET'])
def result():
    if request.method == 'GET':
        table = session.pop('scraped_table', None)
        return render_template('index.html', table=table)
    return redirect(url_for('index'))

@app.route('/process', methods=['POST'])
def process():
    selected_rows = request.form.getlist("row")  # list of checked values
    return f"You selected rows: {', '.join(selected_rows)}"

if __name__ == '__main__':

    app.run(debug=True)