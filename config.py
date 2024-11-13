import os

class Config:
    # Secret key for session management (You should change this to a more secure value)
    SECRET_KEY = os.urandom(24)

    # Session lifetime settings (optional)
    PERMANENT_SESSION_LIFETIME = 3600  # In seconds (1 hour)
    #MySQL Configuration for Amazon RDS
    MYSQL_HOST = "parkinson-db.cpkow24yk7fq.us-east-2.rds.amazonaws.com"  # Endpoint of RDS instance
    MYSQL_USER = "admin"
    MYSQL_PASSWORD = "StudentFall2024!"
    MYSQL_DB = "parkinson-db"
    MYSQL_PORT = 3306  # Default MySQL port

    # For MySQLdb (This would be needed if you're using MySQLdb for connection)
    MYSQL_CURSORCLASS = 'DictCursor'  # Use DictCursor if you want your queries to return dictionaries

    # Debugging
    DEBUG = True
    TESTING = False

    # Additional config options could go here (e.g., email server, logging, etc.)


# You can have different classes for different environments (e.g., Development, Testing, Production)
class DevelopmentConfig(Config):
    DEBUG = True
    ENV = 'development'


class TestingConfig(Config):
    DEBUG = False
    TESTING = True
    ENV = 'testing'


class ProductionConfig(Config):
    DEBUG = False
    ENV = 'production'
