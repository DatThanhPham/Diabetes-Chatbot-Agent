from flask import Flask, request, jsonify
import random
import time

app = Flask(__name__)

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    
    if not data or len(data) != 19:
        return jsonify({"error": "Dữ liệu đầu vào không đủ 19 chỉ số"}), 400

    print("--- MOCK MODEL NHẬN ĐƯỢC DỮ LIỆU ---")
    print(data)
    
    # Giả lập thời gian model đang "suy nghĩ"
    time.sleep(1) 
    
    # === THAY ĐỔI LOGIC: CHỈ TRẢ VỀ 0 (Không) HOẶC 1 (Có) ===
    prediction = random.choice([0, 1])
    
    print(f"--- MOCK MODEL TRẢ VỀ KẾT QUẢ: {prediction} ---")
    
    return jsonify({"prediction": prediction}), 200

if __name__ == '__main__':
    # Chạy trên cổng 5001
    app.run(debug=True, port=5001)