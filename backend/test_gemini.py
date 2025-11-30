"""
Test Gemini API configuration and file access
"""
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

print("=" * 70)
print("TESTING GEMINI API CONFIGURATION")
print("=" * 70)

# 1. Check API Key
api_key = os.getenv('GEMINI_API_KEY')
print(f"\n1️⃣ API Key Status:")
if api_key:
    print(f"   ✓ API Key found: {api_key[:10]}...{api_key[-5:]}")
    genai.configure(api_key=api_key)
else:
    print(f"   ❌ API Key NOT found in .env")
    exit(1)

# 2. List available models
print(f"\n2️⃣ Available Models:")
try:
    models = genai.list_models()
    count = 0
    for model in models:
        if 'generateContent' in model.supported_generation_methods:
            print(f"   ✓ {model.name}")
            count += 1
            if count >= 5:  # Show first 5
                break
    print(f"   Total: {count} models available")
except Exception as e:
    print(f"   ❌ Error listing models: {e}")
    exit(1)

# 3. Test basic generation
print(f"\n3️⃣ Testing Basic Generation:")
try:
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content("Say 'Hello, I am working!' in Vietnamese")
    print(f"   ✓ Response: {response.text[:100]}...")
except Exception as e:
    print(f"   ❌ Generation failed: {e}")
    exit(1)

# 4. Check uploaded files
print(f"\n4️⃣ Checking Uploaded Files:")
file_ids_str = os.getenv('KNOWLEDGE_FILE_IDS', '')
if file_ids_str:
    file_ids = [fid.strip() for fid in file_ids_str.split(',') if fid.strip()]
    print(f"   Configured file IDs: {len(file_ids)}")
    
    for fid in file_ids:
        try:
            file_obj = genai.get_file(fid)
            print(f"   ✓ File: {fid}")
            print(f"      - Name: {file_obj.display_name}")
            print(f"      - Size: {file_obj.size_bytes / 1024:.2f} KB")
            print(f"      - State: {file_obj.state.name}")
        except Exception as e:
            print(f"   ❌ File {fid}: {e}")
else:
    print(f"   ⚠ No KNOWLEDGE_FILE_IDS configured")
    print(f"   → Will work without RAG (knowledge base)")

# 5. Test generation with files (if available)
if file_ids_str:
    print(f"\n5️⃣ Testing Generation with Files:")
    try:
        rag_files = []
        for fid in file_ids[:2]:  # Test with first 2 files
            try:
                rag_files.append(genai.get_file(fid))
            except:
                pass
        
        if rag_files:
            model = genai.GenerativeModel('gemini-2.0-flash')
            prompt = "Dựa vào tài liệu, hãy cho tôi biết tiểu đường là gì?"
            content = [prompt] + rag_files
            
            response = model.generate_content(content)
            print(f"   ✓ Response with RAG: {response.text[:150]}...")
        else:
            print(f"   ⚠ No files loaded for RAG test")
            
    except Exception as e:
        print(f"   ❌ RAG generation failed: {e}")

print("\n" + "=" * 70)
print("✅ GEMINI API TEST COMPLETED")
print("=" * 70)