# wsgi.py
from app import create_app

app = create_app()

if __name__ == '__main__':
    # This only runs locally — Railway uses gunicorn instead
    app.run(debug=True)