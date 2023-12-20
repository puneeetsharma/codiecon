import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import datetime

# Sample data (replace this with your actual data)
# Assuming you have a dataset with columns: 'user_id', 'year', 'savings_percentage', 'discount_availed'
# 'user_id' is the unique identifier for each user
# 'year' is the order year, 'savings_percentage' is the savings percentage on orders,
# and 'discount_availed' is the discount availed in the previous year
data = {
    'user_id': [1, 1, 1, 2, 2, 2, 3, 3, 3],
    'year': [2018, 2019, 2020, 2018, 2019, 2020, 2018, 2019, 2020],
    'savings_percentage': [10, 15, 20, 8, 12, 18, 5, 8, 10],
    'discount_availed': [200, 250, 300, 150, 180, 220, 100, 120, 130]
}

# Convert 'year' to datetime for better handling
data['year'] = [datetime.datetime(year, 1, 1) for year in data['year']]

# Create features and target variables
X = np.array(data['discount_availed']).reshape(-1, 1)
y = np.array(data['savings_percentage'])

# Split the data into training and testing sets (per user)
user_ids = np.unique(data['user_id'])
savings_forecasts = {}

for user_id in user_ids:
    user_data = data[data['user_id'] == user_id]

    X_user = np.array(user_data['discount_availed']).reshape(-1, 1)
    y_user = np.array(user_data['savings_percentage'])

    X_train, X_test, y_train, y_test = train_test_split(X_user, y_user, test_size=0.2, random_state=42)

    # Initialize and train the model
    model = LinearRegression()
    model.fit(X_train, y_train)

    # Make predictions on the test set
    y_pred = model.predict(X_test)

    # Evaluate the model
    mse = mean_squared_error(y_test, y_pred)
    print(f"Mean Squared Error for User {user_id}: {mse}")

    # Assuming 'discount_availed_next_year' is the discount you expect to avail next year for each user
    discount_availed_next_year = np.array([[350]])  # Replace with your expected discount for the next year

    # Predict the savings for the next year for each user
    savings_forecast = model.predict(discount_availed_next_year)
    savings_forecasts[user_id] = savings_forecast[0]

print("Savings Forecasts for Next Year:")
for user_id, forecast in savings_forecasts.items():
    print(f"User {user_id}: {forecast:.2f}%")


def get_saving_forecast(data):
      # You can adjust the number of rows as needed
    return model.predict(data)
