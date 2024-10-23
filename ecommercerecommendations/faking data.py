from faker import Faker
import mysql.connector
import random
from datetime import datetime

# Initialize Faker to generate fake data
fake = Faker()

# Connect to your MySQL database
connection = mysql.connector.connect(
    host='localhost',
    user='root',
    password='mysql0293',
    database='ecommerce_recommendations'
)
cursor = connection.cursor()

# Create sample data for users, products, and purchases
def create_fake_data():
    # Insert fake users
    for _ in range(10):  # Creating 10 fake users
        username = fake.user_name()
        email = fake.email()
        cursor.execute("INSERT INTO users (username, email) VALUES (%s, %s)", (username, email))

    # Insert fake products
    for _ in range(5):  # Creating 5 fake products
        product_name = fake.word()
        cursor.execute("INSERT INTO products (name) VALUES (%s)", (product_name,))

    connection.commit()

    # Fetch user and product IDs
    cursor.execute("SELECT user_id FROM users")
    user_ids = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT product_id FROM products")
    product_ids = [row[0] for row in cursor.fetchall()]

    # Insert fake purchase data
    for _ in range(20):  # Creating 20 fake purchases
        user_id = random.choice(user_ids)
        product_id = random.choice(product_ids)
        purchase_date = fake.date_time_this_year()
        cursor.execute("INSERT INTO purchases (user_id, product_id, purchase_date) VALUES (%s, %s, %s)",
                       (user_id, product_id, purchase_date))

    connection.commit()

# Call the function to create the data
create_fake_data()

# Close connection
cursor.close()
connection.close()
print("Fake data created successfully!")