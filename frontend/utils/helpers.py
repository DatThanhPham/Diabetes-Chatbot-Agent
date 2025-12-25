"""
Helper functions
"""
from datetime import datetime
from utils.constants import RISK_LEVELS, BMI_RANGES
import pytz

def format_datetime(iso_string):
    """
    Format ISO datetime to Vietnamese format
    
    Args:
        iso_string: ISO format datetime string
    
    Returns:
        str: Formatted datetime (e.g., "30/11/2024 lúc 16:45")
    """
    if not iso_string:
        return ""
    
    try:
        # Parse ISO string
        dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
        
        # Convert to Vietnam timezone
        vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
        dt_vn = dt.astimezone(vn_tz)
        
        # Format
        return dt_vn.strftime("%d/%m/%Y lúc %H:%M")
    except:
        return iso_string

def format_date(date_string):
    """Format date to Vietnamese format: HH:MM:SS DD/MM/YYYY"""
    if not date_string:
        return ''
    
    try:
        # Handle different date formats
        if isinstance(date_string, str):
            # Try parsing HTTP date format: "Wed, 03 Dec 2025 06:32:49 GMT"
            try:
                dt = datetime.strptime(date_string, '%a, %d %b %Y %H:%M:%S %Z')
            except:
                # Try ISO format
                date_string = date_string.replace('Z', '+00:00')
                dt = datetime.fromisoformat(date_string)
        else:
            dt = date_string
        
        # If datetime is naive (no timezone), assume UTC
        if dt.tzinfo is None:
            dt = pytz.UTC.localize(dt)
        
        # Convert to Vietnam timezone
        vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
        dt_vn = dt.astimezone(vn_tz)
        
        # Format as HH:MM:SS DD/MM/YYYY
        return dt_vn.strftime('%H:%M:%S %d/%m/%Y')
    except Exception as e:
        print(f"Error formatting date: {e}")
        return str(date_string)

def format_risk_score(score):
    """Format risk score to percentage"""
    try:
        return f"{float(score) * 100:.1f}%"
    except:
        return "N/A"

def get_risk_level_info(risk_level):
    """Get risk level display info"""
    return RISK_LEVELS.get(risk_level)

def get_bmi_category(bmi):
    """Get BMI category"""
    try:
        bmi = float(bmi)
        for category, info in BMI_RANGES.items():
            if info['min'] <= bmi < info['max']:
                return category, info
        return 'obese', BMI_RANGES['obese']
    except:
        return None, None

def validate_bmi(bmi):
    """Validate BMI value"""
    try:
        bmi = float(bmi)
        if bmi < 10 or bmi > 100:
            return False, "BMI phải từ 10 đến 100"
        return True, ""
    except:
        return False, "BMI không hợp lệ"

def validate_health_days(days):
    """Validate health days (0-30)"""
    try:
        days = int(days)
        if days < 0 or days > 30:
            return False, "Giá trị phải từ 0 đến 30"
        return True, ""
    except:
        return False, "Giá trị không hợp lệ"

def calculate_bmi(weight_kg, height_cm):
    """Calculate BMI from weight and height"""
    try:
        height_m = float(height_cm) / 100
        bmi = float(weight_kg) / (height_m ** 2)
        return round(bmi, 1)
    except:
        return 0

def format_metric_value(key, value):
    """Format metric value for display"""
    if value == 1.0:
        return "✓ Có"
    elif value == 0.0:
        return "✗ Không"
    else:
        return str(value)
