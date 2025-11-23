import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

FILES_TO_UPLOAD = [
    "knowledge/diabetes-101-booklet.pdf",
    "knowledge/types_of_physical_activity.pdf",
    "knowledge/wcie_participant_guide_class_2_lr.pdf",
    "knowledge/wcie_participant_guide_class_4_lr.pdf",
    "knowledge/YourGuide2Diabetes_508.pdf"
]

print(f"Đang chuẩn bị tải lên {len(FILES_TO_UPLOAD)} file...")
uploaded_ids = []

try:
    for file_name in FILES_TO_UPLOAD:
        print(f"--> Đang tải: {file_name}...")
        uploaded_file = genai.upload_file(path=file_name)
        print(f"    ✅ Xong! ID: {uploaded_file.name}")
        uploaded_ids.append(uploaded_file.name)

    # Tạo chuỗi ID cách nhau bởi dấu phẩy
    ids_string = ",".join(uploaded_ids)
    
    print("\n" + "="*50)
    print(f'KNOWLEDGE_FILE_IDS="{ids_string}"')
    print("="*50)

except Exception as e:
    print(f"❌ Lỗi: {e}")