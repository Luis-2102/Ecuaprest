# config.py
import os

class Config:
    SQLALCHEMY_DATABASE_URI = 'postgresql://usuario:contraseña@localhost:5432/mi_base'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'supersecreto'
