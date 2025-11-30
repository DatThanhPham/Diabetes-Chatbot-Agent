import os
import joblib
import pandas as pd
import numpy as np
import xgboost as xgb

# Đường dẫn đến thư mục models
MODEL_DIR = os.path.join(os.path.dirname(__file__), '..', '../models')

class DiabetesPredictor:
    def __init__(self):
        self.model = None
        self.encoders = None
        self.scaler = None
        self.is_loaded = False
        
        # Định nghĩa các nhóm cột y hệt như lúc train
        self.columns_order = [
            'HighBP', 'HighChol', 'CholCheck', 'BMI', 'Smoker', 
            'Stroke', 'HeartDiseaseorAttack', 'PhysActivity', 'HvyAlcoholConsump', 
            'AnyHealthcare', 'NoDocbcCost', 'GenHlth', 'MentHlth', 
            'PhysHlth', 'DiffWalk', 'Sex', 'Age', 'Education', 'Income'
        ]
        self.categorical_cols = ['GenHlth', 'Age', 'Education', 'Income']
        self.numerical_cols = ['BMI', 'MentHlth', 'PhysHlth']

    def load_resources(self):
        try:
            print("⏳ Đang tải model XGBoost và bộ xử lý...")
            self.model = joblib.load(os.path.join(MODEL_DIR, 'stacking_ensemble_model.bin'))
            self.encoders = joblib.load(os.path.join(MODEL_DIR, 'label_encoders.bin'))
            self.scaler = joblib.load(os.path.join(MODEL_DIR, 'scaler.bin'))
            self.is_loaded = True
            print("✅ Tải resources thành công!")
        except Exception as e:
            print(f"Lỗi khi tải model: {e}")
            self.is_loaded = False

    def preprocess_input(self, data):
        """
        Input: data là dictionary { 'HighBP': 1, 'BMI': 25.5, ... }
        """
        # 1. Tạo DataFrame và đảm bảo đúng thứ tự cột
        # Ép kiểu float ngay từ đầu để tránh lỗi LabelEncoder (vì lúc train data là float)
        df_input = pd.DataFrame([data], columns=self.columns_order)
        
        # Chuyển đổi toàn bộ dữ liệu sang numeric (float)
        # errors='coerce' sẽ biến các giá trị không phải số thành NaN
        df_input = df_input.apply(pd.to_numeric, errors='coerce')

        # Kiểm tra nếu có giá trị NaN (do nhập liệu sai hoặc thiếu)
        if df_input.isnull().values.any():
            missing_cols = df_input.columns[df_input.isnull().any()].tolist()
            raise ValueError(f"Dữ liệu đầu vào không hợp lệ hoặc thiếu ở các cột: {missing_cols}")

        print(f"⏳ Dữ liệu sau khi chuẩn hóa số học:\n", df_input)

        # 2. Xử lý Categorical (Label Encoding)
        for col in self.categorical_cols:
            if col in self.encoders:
                encoder = self.encoders[col]
                try:
                    # LabelEncoder rất nhạy cảm. 
                    # Giá trị input phải khớp chính xác với giá trị trong classes_ của encoder.
                    # Vì lúc train dữ liệu là float (VD: 5.0), ta đảm bảo input cũng là float.
                    val = df_input.at[0, col]
                    
                    # Kiểm tra xem giá trị này có trong encoder không
                    if val not in encoder.classes_:
                        # Xử lý trường hợp giá trị lạ (Ví dụ: Age nhập vào 15 mà max chỉ 13)
                        # Cách 1: Gán về giá trị phổ biến nhất (mode) hoặc min/max
                        # Cách 2: Ném lỗi (An toàn nhất)
                        raise ValueError(f"Giá trị '{val}' ở cột '{col}' không tồn tại trong tập huấn luyện.")
                    
                    df_input[col] = encoder.transform([val])
                    
                except Exception as e:
                    print(f"Lỗi encode cột {col}: {e}")
                    raise e

        # 3. Xử lý Numerical (StandardScaler)
        # Scaler trả về numpy array, cần gán lại đúng cột
        try:
            df_input[self.numerical_cols] = self.scaler.transform(df_input[self.numerical_cols])
        except Exception as e:
            print(f"Lỗi scale dữ liệu: {e}")
            raise e

        return df_input

    def predict(self, form_data):
        if not self.is_loaded:
            self.load_resources()
            if not self.is_loaded:
                return {"error": "Model not loaded"}

        try:
            # Preprocess
            processed_data = self.preprocess_input(form_data)
            
            # Predict
            prediction = self.model.predict(processed_data)

            return prediction[0]
        except Exception as e:
            return {"error": str(e)}

# Tạo instance toàn cục để sử dụng trong app
predictor = DiabetesPredictor()