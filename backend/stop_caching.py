import google.generativeai as genai
from google.generativeai import caching
import os
import json
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

STATE_FILE = "cache_state.json"

if os.path.exists(STATE_FILE):
    try:
        # 1. Đọc tên cache từ file
        with open(STATE_FILE, 'r') as f:
            data = json.load(f)
            cache_name = data.get('cache_name')
            
        # 2. Xóa trên Google
        if cache_name:
            print(f"🛑 Đang xóa cache: {cache_name}")
            cache = caching.CachedContent(name=cache_name)
            cache.delete()
            print("✅ Đã xóa thành công trên server.")
            
    except Exception as e:
        print(f"⚠️ Lỗi (có thể cache đã tự hết hạn): {e}")
    
    # 3. Xóa file json
    os.remove(STATE_FILE)
    print("🗑️ Đã xóa file trạng thái cục bộ.")
else:
    print("⚠️ Không tìm thấy file cache_state.json (Hệ thống chưa bật?)")