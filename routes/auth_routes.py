from flask import Blueprint, request, current_app, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from bson.objectid import ObjectId
import datetime

from flask_jwt_extended import jwt_required, get_jwt
from flask import jsonify, current_app

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/users", methods=["GET"])
@jwt_required()
def list_users():
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"msg": "Admin only"}), 403

    users = current_app.db.users
    res = []
    for u in users.find({}, {"password": 0}):
        res.append({
            "id": str(u["_id"]),
            "name": u.get("name"),
            "email": u.get("email"),
            "role": u.get("role")
        })
    return jsonify(res), 200

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role", "worker")
    if not name or not email or not password:
        return jsonify({"msg":"Missing fields"}), 400

    users = current_app.db.users
    if users.find_one({"email": email}):
        return jsonify({"msg":"User already exists"}), 400

    hashed = generate_password_hash(password)
    user = {
        "name": name,
        "email": email,
        "password": hashed,
        "role": role
    }
    res = users.insert_one(user)
    user_id = str(res.inserted_id)
    return jsonify({"msg":"User created", "user_id": user_id}), 201

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        return jsonify({"msg":"Missing email or password"}), 400

    users = current_app.db.users
    user = users.find_one({"email": email})
    if not user or not check_password_hash(user["password"], password):
        return jsonify({"msg":"Bad email or password"}), 401

    identity = str(user["_id"])
    additional_claims = {"role": user.get("role", "worker"), "name": user.get("name")}
    access_token = create_access_token(identity=identity, additional_claims=additional_claims)
    return jsonify({
        "access_token": access_token,
        "user": {"id": identity, "name": user.get("name"), "email": user.get("email"), "role": user.get("role")}
    }), 200
