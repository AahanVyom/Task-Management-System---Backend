from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from config import MONGO_URI, JWT_SECRET_KEY, JWT_ACCESS_TOKEN_EXPIRES
from pymongo import MongoClient
import os

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = JWT_ACCESS_TOKEN_EXPIRES

CORS(app, supports_credentials=True, resources={
    r"/*": {
        "origins": ["https://aahanvyom.github.io"]
    }
})

jwt = JWTManager(app)

client = MongoClient(MONGO_URI)
db = client.get_default_database()

app.db = db

from routes.auth_routes import auth_bp
from routes.task_routes import task_bp
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(task_bp, url_prefix="/api")

@app.route("/")
def hello():
    return jsonify({"msg":"Task Manager API is running"})

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
