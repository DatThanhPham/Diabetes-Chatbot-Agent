import google.generativeai as genai
from google.generativeai import caching
import os
import datetime
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

FILES_TO_UPLOAD = [
    "knowledge/diabetes-101-booklet.pdf",
    "knowledge/types_of_physical_activity.pdf",
    "knowledge/wcie_participant_guide_class_2_lr.pdf",
    "knowledge/wcie_participant_guide_class_4_lr.pdf",
    "knowledge/YourGuide2Diabetes_508.pdf"
]

uploaded_files = []
print(f"Đang tải lên {len(FILES_TO_UPLOAD)} file...")

# 1. Upload files
for file_name in FILES_TO_UPLOAD:
    print(f"--> Uploading: {file_name}...")
    uf = genai.upload_file(path=file_name)
    uploaded_files.append(uf)

# 2. CHỜ FILE SẴN SÀNG
# Gemini cần thời gian xử lý file PDF lớn
import time
for f in uploaded_files:
    while f.state.name == "PROCESSING":
        print(f"Waiting for {f.name}...")
        time.sleep(2)
        f = genai.get_file(f.name)

# 3. TẠO CACHE
print("--> Đang tạo Cache Context...")
cache = caching.CachedContent.create(
    model='models/gemini-2.0-flash',
    display_name="diabetes_knowledge_base",
    system_instruction="Bạn là chuyên gia y tế về bệnh tiểu đường. Hãy trả lời câu hỏi dựa trên các tài liệu được cung cấp.",
    contents=uploaded_files,
    ttl=datetime.timedelta(minutes=60) # Tồn tại trong 60 phút
)

import json
state_data = {
    "cache_name": cache.name,
    "created_at": str(datetime.datetime.now())
}
with open("cache_state.json", "w") as f:
    json.dump(state_data, f)
print("💾 Đã lưu Cache vào file cache_state.json")