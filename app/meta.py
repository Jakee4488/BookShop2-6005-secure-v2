"""
Setup "Meta" class,

Contains App definition and database init functionality

# ------ DATABASE FUNC -------
# Taken from from https://flask.palletsprojects.com/en/2.2.x/patterns/sqlite3/

"""

import re
from .seller import seller
from markupsafe import escape
import flask
from flask import g
import sqlite3
import re
import bcrypt
from flask import session
from flask import request
from werkzeug.utils import secure_filename
from flask_wtf.csrf import CSRFProtect
import os
import secrets
import hashlib
from flask import Flask
import string
import random

DATABASE = 'database.db'

UPLOAD_FOLDER = r'C:\Users\jacob\Desktop\6005-working-file\BookShop2-6005-secure\app\uploads'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit


def hash_password(password):
    # Convert the password to bytes
    password_bytes = password.encode('utf-8')

    # Generate a salt and hash the password
    salt = bcrypt.gensalt()

    hashed_password = bcrypt.hashpw(password_bytes,salt)

    # Return the hashed password
    return hashed_password.decode('utf-8')

def check_password(password, hashed_password):
    # Convert the password and the stored hash to bytes
    password_bytes = password.encode('utf-8')
    hashed_password_bytes = hashed_password.encode('utf-8')

    # Check the provided password against the stored hash
    return bcrypt.checkpw(password_bytes, hashed_password_bytes)



def generate_random_session_key(length=32):
    # Generate a random session key
    return secrets.token_urlsafe(length)

def hash_session_key(session_key):
    # Hash the session key using SHA-256
    sha256 = hashlib.sha256()
    sha256.update(session_key.encode('utf-8'))
    return sha256.hexdigest()

session_key = generate_random_session_key()

    # Hash the session key
hashed_key = hash_session_key(session_key)

def generate_random_session_key(length=32):
    # Generate a random session key
    return secrets.token_urlsafe(length)

def hash_session_key(session_key):
    # Hash the session key using SHA-256
    sha256 = hashlib.sha256()
    sha256.update(session_key.encode('utf-8'))
    return sha256.hexdigest()

session_key = generate_random_session_key()

    # Hash the session key
hashed_key = hash_session_key(session_key)

app.config.update(
    SECRET_KEY=hashed_key,
    SESSION_COOKIE_SAMESITE='Strict',
    UPLOAD_FOLDER=UPLOAD_FOLDER
)
from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect(app)


def make_dicts(cursor, row):
    return dict((cursor.description[idx][0], value)
                for idx, value in enumerate(row))


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)

    db.row_factory = make_dicts
    return db

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def write_db(query, args=()):
    """
    Helper Method for Write
    """
    db = get_db()
    db.execute(query, args)
    db.commit()


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()
    
def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('../schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def is_valid_password(password):
    errors = []

    if len(password) < 8:
        errors.append("Error 1: Password must be at least 8 characters long")

    if not re.search(r"[a-z]", password):
        errors.append("Error 2: Password must contain at least one lowercase letter")

    if not re.search(r"[A-Z]", password):
        errors.append("Error 3: Password must contain at least one uppercase letter\n")

    if not re.search(r"\d", password):
        errors.append("Error 4: Password must contain at least one digit")

    if not re.search(r"[@!#$%^&+=]", password):
        errors.append("Error 5: Password must contain at least one special character [@#$%^&+=]")

    if errors:
        return False, errors
    else:
        return True, []
    
def generate_otp(length=6):
    # Define the characters from which the OTP will be composed
    characters = string.digits  # You can also include letters (uppercase and/or lowercase) if needed

    # Generate the OTP using random.choices (Python 3.6+)
    otp = ''.join(random.choices(characters, k=length))

    return otp

import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def generate_otp(length=6):
    characters = string.digits
    otp = ''.join(random.choices(characters, k=length))
    return otp

def send_otp_email(receiver_email):
    # Generate OTP
    otp = generate_otp()

    # Email configuration (Gmail SMTP)
    sender_email = 'danubebooks81@gmail.com'  # Replace with your Gmail email address
    sender_password = 'qdol zmgu otlq pgdd'  # Replace with your Gmail password
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587

    # Email content
    subject = 'Your OTP for Verification'
    body = f'Your OTP is: {otp}'

    # Create the email message
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = receiver_email
    message['Subject'] = subject

    # Attach the email body
    message.attach(MIMEText(body, 'plain'))

    # Connect to Gmail's SMTP server and send the email
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, message.as_string())
        server.quit()
        print(f"OTP sent successfully to {receiver_email}")
        return otp  # Return the generated OTP for verification
    except Exception as e:
        print(f"Error: {e}")
        return None  # Return None if there was an error sending the OTP



