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
item_prices = [re.sub(r'[^0-9\s]', '', item_price.find('span', class_ = 'sr-only').text)+ "₪" for item_price in all_items]

#Order the results as a CSV in a pandas dataFrame
df = pd.DataFrame(columns= ["Product","Price"])
df["Product"] = item_names
df["Price"] = item_prices

print(df)
#Add the path and uncomment
#df.to_csv(r'/Users/Username/Where/Folder/Example.csv', index = False)


#Need to do:

# Create a basic front end with a search bar for adding the product the user is looking for
# the text written in the search box should craete a URL in the template of the store's URl templates, for reference, see the first comment.
# After mapping the URL, the URL should hit an API that reaches this code, this code will reveal the desired dataFrame.
# The dataFrame should also be displayed in a proper way udner the search bar.
# Adding the dataFramae to the website may require to work harder, so it isn't supposed to be an easy project.


# Extra:

# If we decide to bring this project live, it's better that we do a search history, and after each search that the customer perform, we''re going to save it
# as part of a cookies, and we will run a daily chron job until the cookie expires, the chron job will mainly save the itme price.
# Why? that data collected by the chron job will plot the prices using matplotlib, and whenever the user searches the same item again, they can click it and it will show a price graph for the last 30d.

# Done extra? Go live:

# We can host the chron job in web, host the customer's profile in a redis DB for quick in-mem access.
# We can host the whole project in AWS, or preferrably Azue for easier scaling since I'm experienced with MS Azure.

# Goal: Until Aril, 2 commits.

