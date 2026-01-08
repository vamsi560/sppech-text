# Entry point for Vercel Python Serverless Function
from flask_app import app

# Vercel looks for 'app' or 'handler' variable
handler = app
