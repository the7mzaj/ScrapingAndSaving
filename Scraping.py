from bs4 import BeautifulSoup
import requests
import re
import pandas as pd

#Search what you're looking for and paste it here
url = ""


headers = {
    'User-Agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36'
}

req = requests.get(url, headers= headers)

#Parse the whole content of the webpage
parsing = BeautifulSoup(req.text, 'lxml')

#Find all the items by class
all_items = parsing.find_all('div', class_ = 'row p-1 entry-wrapper')

#Extract the items named and it's prices
item_names = [re.sub(r'[^a-zA-Z0-9\s]', '', item_name.find('div', class_ = 'col-md-12 col-12 title_product_catalog mb-md-1 main-text-area').text.strip()) for item_name in all_items]
item_prices = [re.sub(r'[^0-9\s]', '', item_price.find('span', class_ = 'sr-only').text) for item_price in all_items]

#Order the results as a CSV in a pandas dataFrame
df = pd.DataFrame(columns= item_names)
df.loc[len(df)+1] = item_prices

df.to_csv(r'/Users/hamzajbara/Desktop/ScrapingAndSaving/SonyScraping.csv', index = False)


