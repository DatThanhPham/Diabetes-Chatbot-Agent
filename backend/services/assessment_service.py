"""
Assessment Service - Business logic for health assessments
"""
from datetime import datetime, timedelta
from bson.objectid import ObjectId
from datasources.mongodb import get_db

def create_assessment(user_id: str, metrics: dict, prediction: dict) -> dict:
    """
    Create new assessment and invalidate old ones
    
    Args:
        user_id: User's ObjectId as string
        metrics: Health metrics (19 fields from form)
        prediction: Dict with keys: prediction, risk_score, risk_level, model_version
    
    Returns:
        dict: {'success': bool, 'data': {...}, 'error': str}
    """
    try:
        db = get_db()
        
        # Validate prediction structure
        required_pred_keys = ['prediction', 'risk_score', 'risk_level']
        if not all(key in prediction for key in required_pred_keys):
            return {
                'success': False,
                'error': f'Missing prediction keys. Required: {required_pred_keys}'
            }
        
        # Validate metrics (should have 19 fields)
        required_metrics = [
            'HighBP', 'HighChol', 'CholCheck', 'BMI', 'Smoker', 'Stroke',
            'HeartDiseaseorAttack', 'PhysActivity', 'HvyAlcoholConsump',
            'AnyHealthcare', 'NoDocbcCost', 'GenHlth', 'MentHlth',
            'PhysHlth', 'DiffWalk', 'Sex', 'Age', 'Education', 'Income'
        ]
        
        missing_metrics = [m for m in required_metrics if m not in metrics]
        if missing_metrics:
            return {
                'success': False,
                'error': f'Missing metrics: {missing_metrics}'
            }
        
        # 1. Invalidate all existing assessments for this user
        db.assessments.update_many(
            {
                'user_id': user_id,
                'is_valid': True
            },
            {
                '$set': {'is_valid': False}
            }
        )
        
        # 2. Create new assessment
        now = datetime.utcnow()
        
        assessment_data = {
            'user_id': user_id,
            'measured_at': now,
            'created_at': now,
            'is_valid': True,
            'metrics': metrics,
            'prediction': {
                'prediction': int(prediction['prediction']),
                'risk_score': float(prediction['risk_score']),
                'risk_level': prediction['risk_level'],
                'model_version': prediction.get('model_version', 'stacking_ensemble_v1')
            }
        }
        
        result = db.assessments.insert_one(assessment_data)
        
        # Return created assessment with ID
        assessment_data['_id'] = result.inserted_id
        assessment_data['id'] = str(result.inserted_id)
        
        return {
            'success': True,
            'data': assessment_data
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def get_assessments_by_user(user_id: str, valid_only: bool = False) -> list:
    """
    Get all assessments for a user
    
    Args:
        user_id: User's ObjectId as string
        valid_only: Only return valid assessments
    
    Returns:
        list: List of assessments
    """
    try:
        db = get_db()
        
        query = {'user_id': user_id}
        if valid_only:
            query['is_valid'] = True
        
        assessments = list(db.assessments.find(query).sort('created_at', -1))
        
        # Convert ObjectId to string
        for assessment in assessments:
            assessment['id'] = str(assessment.pop('_id'))
        
        return assessments
        
    except Exception as e:
        print(f"Error getting assessments: {e}")
        return []

def get_assessment_by_id(assessment_id: str) -> dict:
    """
    Get assessment by ID
    
    Args:
        assessment_id: Assessment ObjectId as string
    
    Returns:
        dict: Assessment data or None
    """
    try:
        db = get_db()
        
        assessment = db.assessments.find_one({'_id': ObjectId(assessment_id)})
        
        if not assessment:
            return None
        
        assessment['id'] = str(assessment.pop('_id'))
        
        return assessment
        
    except Exception as e:
        print(f"Error getting assessment: {e}")
        return None

def get_latest_valid_assessment(user_id: str) -> dict:
    """
    Get latest valid assessment for user
    
    Args:
        user_id: User's ObjectId as string
    
    Returns:
        dict: Latest valid assessment or None
    """
    try:
        db = get_db()
        
        assessment = db.assessments.find_one(
            {'user_id': user_id, 'is_valid': True},
            sort=[('created_at', -1)]
        )
        
        if not assessment:
            return None
        
        assessment['id'] = str(assessment.pop('_id'))
        
        return assessment
        
    except Exception as e:
        print(f"Error getting latest valid assessment: {e}")
        return None

def get_latest_assessment(user_id: str) -> dict:
    """
    Get latest assessment (regardless of validity)
    
    Args:
        user_id: User's ObjectId as string
    
    Returns:
        dict: Latest assessment or None
    """
    try:
        db = get_db()
        
        assessment = db.assessments.find_one(
            {'user_id': user_id},
            sort=[('created_at', -1)]
        )
        
        if not assessment:
            return None
        
        assessment['id'] = str(assessment.pop('_id'))
        
        return assessment
        
    except Exception as e:
        print(f"Error getting latest assessment: {e}")
        return None

def invalidate_old_assessments(user_id: str, days_threshold: int = 14) -> int:
    """
    Invalidate assessments older than threshold
    
    Args:
        user_id: User's ObjectId as string
        days_threshold: Number of days (default: 14)
    
    Returns:
        int: Number of invalidated assessments
    """
    try:
        db = get_db()
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_threshold)
        
        result = db.assessments.update_many(
            {
                'user_id': user_id,
                'is_valid': True,
                'measured_at': {'$lt': cutoff_date}
            },
            {
                '$set': {'is_valid': False}
            }
        )
        
        return result.modified_count
        
    except Exception as e:
        print(f"Error invalidating old assessments: {e}")
        return 0