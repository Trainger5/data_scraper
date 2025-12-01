from flask import Flask
from flask_cors import CORS
import os

def create_app():
    # Get absolute path to app directory
    app_dir = os.path.dirname(os.path.abspath(__file__))
    
    app = Flask(__name__, 
                template_folder=os.path.join(app_dir, 'templates'),
                static_folder=os.path.join(app_dir, 'static'))
    CORS(app)
    
    from app.routes import main
    app.register_blueprint(main)
    
    return app
