from flask import Flask
from routes import bp_users, bp_assessments, bp_chat


def create_app():
    app = Flask(__name__)

    # đăng ký các blueprint (controller)
    app.register_blueprint(bp_users)
    app.register_blueprint(bp_assessments)
    app.register_blueprint(bp_chat)

    @app.get("/")
    def root():
        return {"status": "ok", "message": "DCA backend is running"}

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
