import os
import joblib
import pandas as pd
import numpy as np

# Đường dẫn đến thư mục models (root/models)
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'models')

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
        
        # Auto-load khi khởi tạo
        self.load_resources()

    def load_resources(self):
        """Load model, encoders, và scaler"""
        try:
            print("⏳ Đang tải model và preprocessing resources...")
            
            model_path = os.path.join(MODEL_DIR, 'stacking_ensemble_model.bin')
            encoders_path = os.path.join(MODEL_DIR, 'label_encoders.bin')
            scaler_path = os.path.join(MODEL_DIR, 'scaler.bin')
            
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model not found: {model_path}")
            if not os.path.exists(encoders_path):
                raise FileNotFoundError(f"Encoders not found: {encoders_path}")
            if not os.path.exists(scaler_path):
                raise FileNotFoundError(f"Scaler not found: {scaler_path}")
            
            self.model = joblib.load(model_path)
            self.encoders = joblib.load(encoders_path)
            self.scaler = joblib.load(scaler_path)
            self.is_loaded = True
            
            print("✅ Model loaded successfully!")
            print(f"   - Model type: {type(self.model).__name__}")
            print(f"   - Features: {len(self.columns_order)}")
            print(f"   - Categorical: {len(self.categorical_cols)}")
            print(f"   - Numerical: {len(self.numerical_cols)}")
            
        except Exception as e:
            print(f"❌ Lỗi khi tải model: {e}")
            self.is_loaded = False
            raise

    def preprocess_input(self, data):
        """
        Preprocess input data
        Input: data là dictionary { 'HighBP': 1.0, 'BMI': 25.5, ... }
        """
        # 1. Tạo DataFrame và đảm bảo đúng thứ tự cột
        df_input = pd.DataFrame([data], columns=self.columns_order)
        
        # 2. Chuyển đổi toàn bộ sang numeric
        df_input = df_input.apply(pd.to_numeric, errors='coerce')

        # 3. Kiểm tra NaN
        if df_input.isnull().values.any():
            missing_cols = df_input.columns[df_input.isnull().any()].tolist()
            raise ValueError(f"Dữ liệu không hợp lệ ở các cột: {missing_cols}")

        # 4. Label Encoding cho categorical
        for col in self.categorical_cols:
            if col in self.encoders:
                encoder = self.encoders[col]
                val = df_input.at[0, col]
                
                # Kiểm tra giá trị có trong classes không
                if val not in encoder.classes_:
                    raise ValueError(
                        f"Giá trị '{val}' ở cột '{col}' không hợp lệ. "
                        f"Các giá trị hợp lệ: {list(encoder.classes_)}"
                    )
                
                df_input[col] = encoder.transform([val])

        # 5. Standard Scaling cho numerical
        df_input[self.numerical_cols] = self.scaler.transform(df_input[self.numerical_cols])

        return df_input

    def predict(self, form_data):
        """
        Predict diabetes risk
        Returns: int (0 or 1)
        """
        if not self.is_loaded:
            raise RuntimeError("Model not loaded. Call load_resources() first.")

        try:
            # Preprocess
            processed_data = self.preprocess_input(form_data)
            
            # Predict
            prediction = self.model.predict(processed_data)
            
            return int(prediction[0])
            
        except Exception as e:
            print(f"❌ Prediction error: {e}")
            raise
    
    def predict_proba(self, form_data):
        """
        Predict probability
        Returns: dict {"low_risk": float, "high_risk": float}
        """
        if not self.is_loaded:
            raise RuntimeError("Model not loaded")
        
        try:
            processed_data = self.preprocess_input(form_data)
            
            if hasattr(self.model, 'predict_proba'):
                proba = self.model.predict_proba(processed_data)[0]
                return {
                    "low_risk": float(proba[0]),
                    "high_risk": float(proba[1])
                }
            else:
                # Fallback if no predict_proba
                prediction = self.predict(form_data)
                return {
                    "low_risk": 0.0 if prediction == 1 else 1.0,
                    "high_risk": 1.0 if prediction == 1 else 0.0
                }
        except Exception as e:
            print(f"❌ Probability error: {e}")
            raise
    
    def get_model_info(self):
        """Get model information"""
        return {
            "is_loaded": self.is_loaded,
            "model_type": type(self.model).__name__ if self.model else None,
            "n_features": len(self.columns_order),
            "categorical_features": self.categorical_cols,
            "numerical_features": self.numerical_cols,
            "all_features": self.columns_order
        }

# Tạo instance toàn cục
try:
    predictor = DiabetesPredictor()
    print("✅ Predictor initialized successfully")
except Exception as e:
    print(f"⚠ Warning: Predictor initialization failed: {e}")
    print("⚠ Server will start but predictions may not work")
    predictor = None