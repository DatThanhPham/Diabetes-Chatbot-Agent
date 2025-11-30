"""
Test your specific flow: analyze_risk -> get_advice
"""
import requests
import json

BASE_URL = "http://127.0.0.1:5000"

print("=" * 70)
print("TESTING YOUR FLOW: analyze_risk -> get_advice")
print("=" * 70)

# Test data
test_form = {
    "HighBP": 1.0,
    "HighChol": 1.0,
    "CholCheck": 1.0,
    "BMI": 28.5,
    "Smoker": 0.0,
    "Stroke": 0.0,
    "HeartDiseaseorAttack": 0.0,
    "PhysActivity": 1.0,
    "HvyAlcoholConsump": 0.0,
    "AnyHealthcare": 1.0,
    "NoDocbcCost": 0.0,
    "GenHlth": 3.0,
    "MentHlth": 5.0,
    "PhysHlth": 3.0,
    "DiffWalk": 0.0,
    "Sex": 1.0,
    "Age": 6.0,
    "Education": 4.0,
    "Income": 6.0
}

# Step 1: Analyze risk (no login required)
print("\n📊 STEP 1: Analyzing risk (without login)...")
print("-" * 70)

res = requests.post(f"{BASE_URL}/api/analyze_risk", json=test_form)
print(f"Status: {res.status_code}")

if res.status_code == 200:
    result = res.json()
    prediction = result['prediction']
    risk_level = result['risk_level']
    validated_data = result['validated_data']
    risk_score = result.get('risk_score', prediction)
    
    print(f"✓ Prediction: {prediction}")
    print(f"✓ Risk Level: {risk_level}")
    print(f"✓ Risk Score: {risk_score:.4f}")
    
    # Step 2: Get advice (without saving)
    print("\n💬 STEP 2: Getting AI advice (without saving to DB)...")
    print("-" * 70)
    
    res = requests.post(f"{BASE_URL}/api/get_advice", json={
        "validated_data": validated_data,
        "prediction": prediction,
        "risk_score": risk_score
    })
    
    print(f"Status: {res.status_code}")
    
    if res.status_code == 200:
        advice_result = res.json()
        advice = advice_result['advice']
        
        print(f"✓ Advice length: {len(advice)} chars")
        print(f"\n📝 Advice preview:")
        print("=" * 70)
        print(advice[:500] + "..." if len(advice) > 500 else advice)
        print("=" * 70)
        
        # Step 3: Test with user_id (save to DB)
        print("\n💾 STEP 3: Getting advice WITH user_id (save to DB)...")
        print("-" * 70)
        
        # Register/Login user
        username = "admin"
        password = "admin123"
        
        requests.post(f"{BASE_URL}/api/users/register", json={
            "name": username,
            "password": password
        })
        
        res = requests.post(f"{BASE_URL}/api/users/login", json={
            "name": username,
            "password": password
        })
        
        if res.status_code == 200:
            user_id = res.json()['user']['id']
            print(f"✓ User ID: {user_id}")
            
            # Get advice WITH user_id
            res = requests.post(f"{BASE_URL}/api/get_advice", json={
                "validated_data": validated_data,
                "prediction": prediction,
                "risk_score": risk_score,
                "user_id": user_id
            })
            
            if res.status_code == 200:
                advice_result = res.json()
                assessment_id = advice_result.get('assessment_id')
                
                if assessment_id:
                    print(f"✓ Assessment saved: {assessment_id}")
                    
                    # Step 4: Chat with RAG
                    print("\n💬 STEP 4: Chatting with RAG...")
                    print("-" * 70)
                    
                    res = requests.post(f"{BASE_URL}/api/chat_with_rag", json={
                        "user_message": "BMI của tôi là 28.5, tôi cần giảm bao nhiêu kg?",
                        "assessment_id": assessment_id
                    })
                    
                    if res.status_code == 200:
                        chat_response = res.json()['response']
                        print(f"✓ Chat response length: {len(chat_response)} chars")
                        print(f"\n📝 Chat preview:")
                        print("=" * 70)
                        print(chat_response[:300] + "..." if len(chat_response) > 300 else chat_response)
                        print("=" * 70)
                        
                        # Step 5: Get messages
                        print("\n📨 STEP 5: Getting chat history...")
                        print("-" * 70)
                        
                        res = requests.get(f"{BASE_URL}/api/messages/assessment/{assessment_id}")
                        
                        if res.status_code == 200:
                            messages = res.json()
                            print(f"✓ Total messages: {len(messages)}")
                            for i, msg in enumerate(messages, 1):
                                print(f"  {i}. [{msg['sender_type']}]: {msg['content'][:60]}...")
else:
    print(f"❌ Error: {res.json()}")

print("\n" + "=" * 70)
print("✅ YOUR FLOW TEST COMPLETED")
print("=" * 70)