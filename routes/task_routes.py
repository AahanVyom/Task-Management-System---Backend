from flask import Blueprint, request, current_app, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from bson.objectid import ObjectId
from utils import role_required, roles_allowed
import datetime

task_bp = Blueprint("tasks", __name__)

def objid(id_str):
    try:
        return ObjectId(id_str)
    except:
        return None

@task_bp.route("/tasks", methods=["POST"])
@jwt_required()
def create_task():
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"msg":"Admin only"}), 403

    data = request.get_json()
    required = ["title", "description", "priority", "due_date", "assigned_to"]
    for r in required:
        if r not in data:
            return jsonify({"msg":f"Missing field {r}"}), 400

    tasks = current_app.db.tasks
    task = {
        "title": data["title"],
        "description": data["description"],
        "priority": data.get("priority", "Low"),
        "status": data.get("status", "Pending"),
        "assigned_to": [ObjectId(a) for a in data.get("assigned_to", [])],
        "created_by": ObjectId(get_jwt_identity()),
        "due_date": data.get("due_date"),
        "timeline": [
            {
                "status": data.get("status","Pending"),
                "updated_by": get_jwt_identity(),
                "note": data.get("note","Task created"),
                "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
            }
        ],
        "created_at": datetime.datetime.utcnow().isoformat() + "Z"
    }
    res = tasks.insert_one(task)
    return jsonify({"msg":"Task created", "task_id": str(res.inserted_id)}), 201

@task_bp.route("/tasks", methods=["GET"])
@jwt_required()
def list_tasks():
    claims = get_jwt()
    tasks = current_app.db.tasks
    if claims.get("role") == "admin":
        q = {}
        status = request.args.get("status")
        assigned = request.args.get("assigned")
        priority = request.args.get("priority")
        due = request.args.get("due_date")
        if status: q["status"] = status
        if priority: q["priority"] = priority
        if assigned:
            try:
                q["assigned_to"] = {"$in":[ObjectId(assigned)]}
            except:
                pass
        if due: q["due_date"] = due

        docs = []
        for t in tasks.find(q):
            t["id"] = str(t["_id"])
            t["created_by"] = str(t["created_by"])
            t["assigned_to"] = [str(x) for x in t.get("assigned_to",[])]
            docs.append({k:v for k,v in t.items() if k!="_id"})
        return jsonify(docs), 200

    return jsonify({"msg":"Forbidden"}), 403

@task_bp.route("/my-tasks", methods=["GET"])
@jwt_required()
def my_tasks():
    identity = get_jwt_identity()
    tasks = current_app.db.tasks
    docs = []
    for t in tasks.find({"assigned_to": {"$in":[ObjectId(identity)]}}):
        t["id"] = str(t["_id"])
        t["created_by"] = str(t["created_by"])
        t["assigned_to"] = [str(x) for x in t.get("assigned_to",[])]
        docs.append({k:v for k,v in t.items() if k!="_id"})
    return jsonify(docs), 200

@task_bp.route("/tasks/<task_id>", methods=["GET"])
@jwt_required()
def task_detail(task_id):
    tasks = current_app.db.tasks
    t = tasks.find_one({"_id": objid(task_id)})
    if not t:
        return jsonify({"msg":"Task not found"}), 404
    t["id"] = str(t["_id"])
    t["created_by"] = str(t["created_by"])
    t["assigned_to"] = [str(x) for x in t.get("assigned_to",[])]
    return jsonify({k:v for k,v in t.items() if k!="_id"}), 200

@task_bp.route("/tasks/<task_id>/status", methods=["PATCH"])
@jwt_required()
def update_status(task_id):
    identity = get_jwt_identity()
    claims = get_jwt()
    data = request.get_json()
    new_status = data.get("status")
    note = data.get("note", "")
    if not new_status:
        return jsonify({"msg":"Missing status"}), 400

    tasks = current_app.db.tasks
    t = tasks.find_one({"_id": objid(task_id)})
    if not t:
        return jsonify({"msg":"Task not found"}), 404

    if claims.get("role") == "worker":
        if ObjectId(identity) not in t.get("assigned_to", []):
            return jsonify({"msg":"Not assigned to this task"}), 403

    timeline_entry = {
        "status": new_status,
        "updated_by": identity,
        "note": note,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    }
    tasks.update_one({"_id": objid(task_id)}, {"$set":{"status": new_status}, "$push":{"timeline": timeline_entry}})
    return jsonify({"msg":"Status updated"}), 200

@task_bp.route("/tasks/<task_id>", methods=["DELETE"])
@jwt_required()
def delete_task(task_id):
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"msg":"Admin only"}), 403

    tasks = current_app.db.tasks
    result = tasks.delete_one({"_id": objid(task_id)})
    if result.deleted_count == 0:
        return jsonify({"msg":"Task not found"}), 404
    return jsonify({"msg":"Deleted"}), 200
