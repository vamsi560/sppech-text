# Entry point for Vercel Python Serverless Function
from flask_app import app as application

# Vercel looks for 'app' or 'application' variable
# This allows all Flask routes to work as serverless endpoints
