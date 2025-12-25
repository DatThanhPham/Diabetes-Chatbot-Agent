"""
Constants and configuration
"""

# Form field labels (Vietnamese)
FIELD_LABELS = {
    'HighBP': 'Huyết áp cao',
    'HighChol': 'Cholesterol cao',
    'CholCheck': 'Đã kiểm tra Cholesterol (5 năm qua)',
    'BMI': 'Chỉ số BMI',
    'Smoker': 'Hút thuốc (>100 điếu)',
    'Stroke': 'Đột quỵ',
    'HeartDiseaseorAttack': 'Bệnh tim / Đau tim',
    'PhysActivity': 'Hoạt động thể chất (30 ngày qua)',
    'HvyAlcoholConsump': 'Uống rượu nhiều',
    'AnyHealthcare': 'Có bảo hiểm y tế',
    'NoDocbcCost': 'Không đủ tiền khám bệnh',
    'GenHlth': 'Sức khỏe tổng quát',
    'MentHlth': 'Ngày sức khỏe tinh thần kém',
    'PhysHlth': 'Ngày sức khỏe thể chất kém',
    'DiffWalk': 'Khó đi lại',
    'Sex': 'Giới tính',
    'Age': 'Độ tuổi',
    'Education': 'Học vấn',
    'Income': 'Thu nhập'
}

# Field descriptions
FIELD_DESCRIPTIONS = {
    'HighBP': 'Bạn có bị huyết áp cao không?',
    'HighChol': 'Bạn có cholesterol cao không?',
    'CholCheck': 'Bạn đã kiểm tra cholesterol trong 5 năm qua?',
    'BMI': 'Chỉ số khối cơ thể (kg/m²)',
    'Smoker': 'Bạn có hút ít nhất 100 điếu thuốc trong đời?',
    'Stroke': 'Bạn đã bị đột quỵ bao giờ chưa?',
    'HeartDiseaseorAttack': 'Bạn có bệnh tim hoặc đã bị đau tim?',
    'PhysActivity': 'Bạn có tập thể dục trong 30 ngày qua?',
    'HvyAlcoholConsump': 'Nam >14 ly/tuần, Nữ >7 ly/tuần',
    'AnyHealthcare': 'Bạn có bảo hiểm y tế không?',
    'NoDocbcCost': 'Có lúc nào bạn không đủ tiền khám bệnh?',
    'GenHlth': 'Đánh giá sức khỏe tổng quát của bạn',
    'MentHlth': 'Số ngày sức khỏe tinh thần không tốt trong 30 ngày',
    'PhysHlth': 'Số ngày sức khỏe thể chất không tốt trong 30 ngày',
    'DiffWalk': 'Bạn có khó khăn khi đi bộ hoặc lên cầu thang?',
    'Sex': 'Giới tính của bạn',
    'Age': 'Nhóm tuổi của bạn',
    'Education': 'Trình độ học vấn cao nhất',
    'Income': 'Mức thu nhập hàng năm'
}

# Yes/No options
YES_NO_OPTIONS = {
    'Có': 1.0,
    'Không': 0.0
}

# Gender options
GENDER_OPTIONS = {
    'Nam': 1.0,
    'Nữ': 0.0
}

# General Health scale
GENERAL_HEALTH_OPTIONS = {
    'Xuất sắc': 1.0,
    'Rất tốt': 2.0,
    'Tốt': 3.0,
    'Trung bình': 4.0,
    'Kém': 5.0
}

# Age groups
AGE_GROUPS = {
    '18-24 tuổi': 1.0,
    '25-29 tuổi': 2.0,
    '30-34 tuổi': 3.0,
    '35-39 tuổi': 4.0,
    '40-44 tuổi': 5.0,
    '45-49 tuổi': 6.0,
    '50-54 tuổi': 7.0,
    '55-59 tuổi': 8.0,
    '60-64 tuổi': 9.0,
    '65-69 tuổi': 10.0,
    '70-74 tuổi': 11.0,
    '75-79 tuổi': 12.0,
    '80+ tuổi': 13.0
}

# Education levels
EDUCATION_LEVELS = {
    'Không tốt nghiệp phổ thông': 1.0,
    'Tốt nghiệp tiểu học': 2.0,
    'Tốt nghiệp THCS': 3.0,
    'Tốt nghiệp THPT': 4.0,
    'Cao đẳng/Đại học (chưa tốt nghiệp)': 5.0,
    'Cao đẳng/Đại học (đã tốt nghiệp)': 6.0
}

# Income levels
INCOME_LEVELS = {
    '< 10 triệu/năm': 1.0,
    '10-15 triệu/năm': 2.0,
    '15-20 triệu/năm': 3.0,
    '20-25 triệu/năm': 4.0,
    '25-35 triệu/năm': 5.0,
    '35-50 triệu/năm': 6.0,
    '50-75 triệu/năm': 7.0,
    '> 75 triệu/năm': 8.0
}

# Risk level info
RISK_LEVELS = {
    'low': {
        'icon': '✅',  # ✅ THÊM
        'label': 'Nguy cơ THẤP',
        'color': '#4caf50',
        'bg_color': '#e8f5e9',
        'description': 'Nguy cơ tiểu đường của bạn ở mức thấp. Hãy duy trì lối sống lành mạnh!'
    },
    'high': {
        'icon': '⚠️',  # ✅ THÊM
        'label': 'Nguy cơ CAO',
        'color': '#f44336',
        'bg_color': '#ffebee',
        'description': 'Nguy cơ tiểu đường của bạn ở mức cao. Cần chú ý và thay đổi lối sống ngay!'
    }
}

# BMI ranges
BMI_RANGES = {
    'underweight': {'min': 0, 'max': 18.5, 'label': 'Thiếu cân', 'color': '#2196f3'},
    'normal': {'min': 18.5, 'max': 24.9, 'label': 'Bình thường', 'color': '#4caf50'},
    'overweight': {'min': 25, 'max': 29.9, 'label': 'Thừa cân', 'color': '#ff9800'},
    'obese': {'min': 30, 'max': 100, 'label': 'Béo phì', 'color': '#f44336'}
}