import pymysql
pymysql.install_as_MySQLdb()
from flask import Flask, redirect, url_for
from flask_mysqldb import MySQL

from config import Config  # or choose a different environment (e.g., ProductionConfig)

mysql = MySQL()

def create_app():

    app = Flask(__name__)
    # Load configuration from the config.py file
    app.config.from_object(Config)  # You can change this to use ProductionConfig or TestingConfig'
    # Initialize MySQL with the Flask app
    mysql.init_app(app)


    from routes.auth_routes import auth_bp
    from routes.admin_routes import admin_bp
    from routes.patient_routes import patient_bp
    from routes.coach_routes import coach_bp
    from routes.chat_routes import chat_bp
    from routes.admin_classes_routes import admin_classes_bp
    # Register Blueprints

    app.register_blueprint(admin_classes_bp, url_prefix= '/admin_classes')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(patient_bp, url_prefix='/patient')
    app.register_blueprint(coach_bp, url_prefix='/coach')
    app.register_blueprint(chat_bp, url_prefix='/chat')
    # Home Route (Landing Page)
    @app.route('/')
    def home():
        return redirect(url_for('auth.login'))

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)

    print(app.url_map)
