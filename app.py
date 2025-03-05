import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request
import re
import pandas as pd

app = Flask(__name__)

def scrape_data():
    url = "https://www.ivory.co.il/catalog.php?act=cat&q=sony"

    headers = {
    'User-Agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36'
    }

    req = requests.get(url, headers= headers)

    parsing = BeautifulSoup(req.text, 'lxml')

    all_items = parsing.find_all('div', class_ = 'row p-1 entry-wrapper')

    item_names = [re.sub(r'[^a-zA-Z0-9\s]', '', item_name.find('div', class_ = 'col-md-12 col-12 title_product_catalog mb-md-1 main-text-area').text.strip()) for item_name in all_items]
    item_prices = [re.sub(r'[^0-9\s]', '', item_price.find('span', class_ = 'sr-only').text)+ "₪" for item_price in all_items]

    df = pd.DataFrame(columns= ["Product","Price"])
    df["Product"] = item_names
    df["Price"] = item_prices

    #df.to_csv(r'/Users/Username/Where/Folder/Example.csv', index = False)

    blad = df.to_html()

    return blad


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        scraped_data = scrape_data()
        return render_template('index.html', table=scraped_data)
    return render_template('index.html', table=None, data=None)

if __name__ == '__main__':
    app.run(debug=True)
