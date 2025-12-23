from flask import Flask
import os
from config import app_config
from database import create_table
from routes import init_routes

app = Flask(__name__)
app.config['WTF_CSRF_ENABLED'] = app_config['WTF_CSRF_ENABLED']
app.config['MQ_QUEUE_NAME'] = app_config['MQ_QUEUE_NAME']

init_routes(app)

with app.app_context():
    try:
        create_table()
    except Exception as e:
        print(f"Error in database initialization: {e}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)