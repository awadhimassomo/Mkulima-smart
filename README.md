# Mkulima-smart

## Environment Setup
```bash
# ON THE CURRENT DIRECTORY (WITH FILE manage.py) RUN THE FOLLOWING IN ORDER:

# create virtual environment and activate it
python -m venv venv
source /venv/bin/activate

# install required packages
python -m pip install -r requirements/development.txt
```

## Back-end Setup
```bash
######################################################
# (MANUALLY) duplicate .env.example and rename to .env
######################################################

# Create initial migrations for our custom models
python manage.py makemigrations

# IF ABOVE DOES NOT WORK, TRY ONE BY ONE BELOW:
python manage.py makemigrations products
python manage.py makemigrations orders
python manage.py makemigrations payments
python manage.py makemigrations authentication

# Apply migrations to create database tables
# if any errors, make sure that database is dropped and recreated for a clean slate
python manage.py migrate


# Create superuser account
python manage.py createsuperuser
# then fill in the requested data

# Create test data for api testing
python manage.py create_test_data
```

## Running Back-end Server
```bash
# Collect static files
python manage.py collectstatic --noinput

# Start the development server
python manage.py runserver

#try
#localhost:8000/
#localhost:8000/health
#localhost:8000/admin
#localhost:8000/db

# API endpoints ready"

# AUTHENTICATION APIs:"
#localhost:8000/api/v1/auth/register/ - User registration"
#localhost:8000/api/v1/auth/login/ - User login"
#localhost:8000/api/v1/auth/profile/ - User profile"
#localhost:8000/api/v1/auth/change-password/ - Change password"
#localhost:8000/api/v1/auth/verify-email/ - Email verification"
# PRODUCTS APIs:"
#localhost:8000/api/v1/products/ - List products"
#localhost:8000/api/v1/products/ - Create product (auth required)"
#localhost:8000/api/v1/products/{id}/ - Product detail"
#localhost:8000/api/v1/products/search/ - Advanced search"
#localhost:8000/api/v1/products/featured/ - Featured products"
#localhost:8000/api/v1/products/categories/ - Product categories"
# ORDERS APIs:"
#localhost:8000/api/v1/orders/ - List orders"
#localhost:8000/api/v1/orders/ - Create order (auth required)"
#localhost:8000/api/v1/orders/{id}/ - Order detail"
#localhost:8000/api/v1/orders/{id}/update_status/ - Update order status"
#localhost:8000/api/v1/orders/{id}/cancel/ - Cancel order"
#localhost:8000/api/v1/orders/calculate_summary/ - Calculate order total"
#localhost:8000/api/v1/orders/my_orders/ - User's orders"
#localhost:8000/api/v1/orders/statistics/ - Order statistics"
# PAYMENTS APIs:"
#localhost:8000/api/v1/payments/methods/ - Payment methods"
#localhost:8000/api/v1/payments/process/ - Process payment"
#localhost:8000/api/v1/payments/{id}/status/ - Payment status"
#localhost:8000/api/v1/payments/accounts/ - User payment accounts"

```

## Testing API Endpoints with Generated Token (LINUX)
```bash
# make test_api_requests.sh executable
chmod +x tests/scripts/test_api_requests.sh

# then execute the script
bash tests/scripts/test_api_requests.sh
```