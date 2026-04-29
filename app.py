from flask import Flask
from db import close_db

def create_app():
    app = Flask(__name__)
    app.secret_key = 'change-this-in-production'

    app.config.update(
        DB_HOST='localhost',
        DB_PORT=5432,
        DB_NAME='hotel_db',       # ← change to your database name
        DB_USER='postgres',        # ← change to your postgres user
        DB_PASSWORD='postgres123',    # ← change to your postgres password
    )

    app.teardown_appcontext(close_db)
    app.jinja_env.filters['enumerate'] = enumerate

    from routes.auth    import auth_bp
    from routes.manager import manager_bp
    from routes.client  import client_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(manager_bp, url_prefix='/manager')
    app.register_blueprint(client_bp,  url_prefix='/client')

    return app

if __name__ == '__main__':
    create_app().run(debug=True)
