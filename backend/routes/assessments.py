from flask import Blueprint, request, jsonify
from services import AssessmentService
from models import PyObjectId
from datasources.mongodb import get_assessment_collection

bp_assessments = Blueprint("assessments", __name__, url_prefix="/assessments")
assessment_service = AssessmentService(get_assessment_collection())


@bp_assessments.post("/")
def create_assessment_route():
    data = request.json or {}
    user_id = data.get("user_id")
    metrics = data.get("metrics", {})

    if not user_id or not metrics:
        return jsonify({"error": "user_id and metrics are required"}), 400

    prediction = data.get("prediction")

    assessment = assessment_service.create_assessment(
        user_id=PyObjectId(user_id),
        metrics=metrics,
        prediction=prediction,
    )

    return jsonify(assessment.model_dump(by_alias=True, mode="json")), 201


@bp_assessments.get("/active")
def get_active_assessment_route():
    user_id = request.args.get("user_id")

    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    assessment = assessment_service.get_active_assessment(
        user_id=PyObjectId(user_id),
    )
    if not assessment:
        return jsonify(None), 200

    return jsonify(assessment.model_dump(by_alias=True, mode="json")), 200


@bp_assessments.get("/")
def list_assessments_route():
    user_id = request.args.get("user_id")

    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    assessments = assessment_service.list_assessments(
        user_id=PyObjectId(user_id),
    )
    return jsonify([a.model_dump(by_alias=True, mode="json") for a in assessments])
