from flask import jsonify


def success(data: dict | None = None, status: int = 200):
    body = {"success": True}
    body.update(data or {})
    return jsonify(body), status


def failure(message: str, status: int = 400):
    return jsonify({"success": False, "message": message}), status
