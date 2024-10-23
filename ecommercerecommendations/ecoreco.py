from flask import Flask, render_template, request
import mysql.connector
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

# Flask app launch
app = Flask(__name__)


# Function to establish database connection
def get_connection():
    connection = mysql.connector.connect(
        host='localhost',
        user='root',
        password='mysql0293',
        database='ecommerce_recommendations'
    )
    return connection


# Function to fetch users and their emails
def fetch_users():
    connection = get_connection()
    cursor = connection.cursor()

    # Obtener todos los usuarios y correos electrónicos
    cursor.execute("SELECT user_id, username, email FROM users;")
    user_rows = cursor.fetchall()

    # Mostrar los usuarios
    print("Usuarios registrados:")
    for user_row in user_rows:
        print(f"ID: {user_row[0]}, Username: {user_row[1]}, Email: {user_row[2]}")

    cursor.close()
    connection.close()
    return user_rows


# Function to connect to the database and fetch purchase data
def fetch_purchase_data():
    # Establecer conexión con la base de datos
    connection = get_connection()
    cursor = connection.cursor()

    # Obtener los datos de las compras
    query = """
    SELECT users.user_id, products.product_id, products.name, purchases.purchase_date
    FROM purchases
    JOIN users ON purchases.user_id = users.user_id
    JOIN products ON purchases.product_id = products.product_id;
    """
    cursor.execute(query)
    data_rows = cursor.fetchall()
    cursor.close()
    connection.close()

    # Convertir los datos en un DataFrame
    purchase_df = pd.DataFrame(data_rows, columns=['user_id', 'product_id', 'product_name', 'purchase_date'])

    # Aplicar la ponderación basada en la fecha de compra
    weighted_purchase_df = weighted_purchase_data(purchase_df)
    return weighted_purchase_df


# Transform data into a user-item matrix
def create_user_item_matrix(df):
    # Usamos el campo de peso (weight) para crear la matriz de usuario-producto
    user_item_matrix = df.pivot_table(index='user_id', columns='product_name', values='weight', aggfunc='sum',
                                      fill_value=0)
    return user_item_matrix


# Add a weight to recent purchases
def weighted_purchase_data(df):
    # Add a weight to recent purchases (more recent = higher weight)
    df['purchase_date'] = pd.to_datetime(df['purchase_date'])
    now = pd.Timestamp.now()

    # Compute the difference between now and purchase date
    df['days_since_purchase'] = (now - df['purchase_date']).dt.days

    # Assign weights inversely proportional to the time passed
    df['weight'] = 1 / (df['days_since_purchase'] + 1)
    return df


# Calculate similarity between users
def calculate_user_similarity(user_item_matrix):
    similarity_matrix = cosine_similarity(user_item_matrix)
    similarity_df = pd.DataFrame(similarity_matrix, index=user_item_matrix.index, columns=user_item_matrix.index)
    return similarity_df


# Recommend products based on user similarity
def recommend_products(user_id, user_item_matrix, similarity_df):
    # Check if user_id exists in the user-item matrix and similarity DataFrame
    if user_id not in similarity_df.index:
        print(f"User ID {user_id} not found in similarity DataFrame")
        return None  # Return None if the user_id is not found

    # Find similar users
    similar_users = similarity_df[user_id].sort_values(ascending=False)

    # Generate recommendations
    recommendations = user_item_matrix.loc[similar_users.index].sum(axis=0).sort_values(ascending=False)

    # Eliminate products the user has already interacted with
    user_products = user_item_matrix.loc[user_id]
    recommendations = recommendations[user_products == 0]

    return recommendations.head(5)


# Home page route
@app.route("/")
def index():
    return render_template('index.html')


# Route for recommendation based on user_id
@app.route('/recommend', methods=['POST'])
def recommend():
    try:
        user_id = int(request.form['user_id'])  # Get user_id from the form input
    except ValueError:
        return render_template('index.html', error="Please enter a valid user ID")

    # Fetch and process the purchase data
    purchase_data = fetch_purchase_data()

    if not purchase_data.empty:
        user_item_matrix = create_user_item_matrix(purchase_data)
        similarity_df = calculate_user_similarity(user_item_matrix)

        # Generate recommendations for the user
        if user_id in similarity_df.index:
            recommendations = recommend_products(user_id, user_item_matrix, similarity_df)

            # Check if recommendations is empty
            if recommendations is None or recommendations.empty:
                return render_template('index.html', error="No recommendations available for this user")

            return render_template('index.html', user_id=user_id, recommendations=recommendations.to_dict())
        else:
            return render_template('index.html', error="User ID not found in the database")
    else:
        return render_template('index.html', error="No purchase data available")


# Now we run the app
if __name__ == '__main__':
    # Fetch and display users on startup
    fetch_users()

    app.run(debug=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)


