from flask_login import UserMixin
import os

class User(UserMixin):
    def __init__(self, id):
        self.id = id
        self.username = id
    
    @staticmethod
    def get(user_id):
        admin_username = os.getenv('ADMIN_USERNAME', 'admin')
        if user_id == admin_username:
            return User(user_id)
        return None
    
    @staticmethod
    def authenticate(username, password):
        admin_username = os.getenv('ADMIN_USERNAME', 'admin')
        admin_password = os.getenv('ADMIN_PASSWORD', 'password123')
        
        if username == admin_username and password == admin_password:
            return User(username)
        return None 