import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from urllib.parse import quote_plus

app = Flask(__name__)

password = quote_plus('United2012@@')
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://root:{password}@localhost/pcparts'
db = SQLAlchemy(app)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    price = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    image_url = db.Column(db.String(255), nullable=True)

    def __init__(self, name, price, url, image_url):
        self.name = name
        self.price = price
        self.url = url
        self.image_url = image_url

# Web scraping function
def scrape_data(search_query):
    url = 'https://www.newegg.ca/p/pl?d=' + search_query
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    products = []
    
    items = soup.find_all('div', class_='item-container')
    for item in items:
        product_name_elem = item.find('a', class_='item-title')
        product_price_elem = item.find('li', class_='price-current')
        product_image_elem = item.find('img', class_='lazy-img')
        
        if product_name_elem and product_price_elem:
            product_name = product_name_elem.text.strip()
            product_price = product_price_elem.text.strip()
            product_url = product_name_elem['href']
            
            if product_image_elem:
                product_image_url = product_image_elem['src']
            else:
                product_image_url = None
            
            product = {
                'name': product_name,
                'price': product_price,
                'url': product_url,
                'image_url': product_image_url
            }
            products.append(product)
    
    return products

# API endpoint to retrieve products from the database or scrape data
@app.route('/api/products')
def get_products():
    search_query = request.args.get('q')
    
    if search_query:
        # Search for products in the database
        products = Product.query.filter(Product.name.contains(search_query)).all()
        
        if not products:
            # If no products found in the database, scrape data from Newegg
            scraped_products = scrape_data(search_query)
            
            # Save scraped products to the database
            for product in scraped_products:
                image_url = product['image_url'] if product['image_url'] else ''
                new_product = Product(product['name'], product['price'], product['url'], product['image_url'])
                db.session.add(new_product)
            db.session.commit()
            
            products = scraped_products
    else:
        # If no search query provided, retrieve all products from the database
        products = Product.query.all()
    
    product_data = []
    for product in products:
        if isinstance(product, Product):
            # If the product is a database model instance
            product_data.append({
                'name': product.name,
                'price': product.price,
                'url': product.url,
                'image_url': product.image_url
            })
        else:
            # If the product is a dictionary from the scraped data
            product_data.append(product)
    
    return jsonify(product_data)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='10.0.0.48', port=5000, debug=True)