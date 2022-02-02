# Statement for enabling the development environment
DEBUG = True

# Define the application directory (like doing a pwd)
import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))  

# Define the database - we are working with
# SQLite for this example
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'app.db')
DATABASE_CONNECT_OPTIONS = {}
DB_NAME = "app.db"

# Application threads. A common general assumption is
# using 2 per available processor cores - to handle
# incoming requests using one and performing background
# operations using the other.
THREADS_PER_PAGE = 2

# Enable protection agains *Cross-site Request Forgery (CSRF)*
CSRF_ENABLED     = True

# Use a secure, unique and absolutely secret key for
# signing the data. 
CSRF_SESSION_KEY = "secret"

# Secret key for signing cookies
SECRET_KEY = "secret"

# Upload csv folder
UPLOAD_FOLDER = f'{BASE_DIR}/app/static/uploads/'

# Inventory file name
INVENTORY_FILE = 'inventory.csv'

# It will instruct Flask to print out the steps it goes through to 
# locate templates on every render_template call.
EXPLAIN_TEMPLATE_LOADING = True