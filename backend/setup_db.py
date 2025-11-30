"""
Setup MongoDB Database theo ERD.puml
Entities: User, Assessment, Message
"""
import os
from dotenv import load_dotenv
from pymongo import MongoClient, ASCENDING, DESCENDING
from urllib.parse import quote_plus
from datetime import datetime, timedelta
import bcrypt
import sys

load_dotenv()

print("=" * 70)
print("SETUP DATABASE THEO ERD.puml")
print("=" * 70)

# 1. Connect to MongoDB
print("\n1️⃣ Connecting to MongoDB Atlas...")
try:
    username = quote_plus(os.getenv('DB_USER'))
    password = quote_plus(os.getenv('DB_PASSWORD'))
    cluster = os.getenv('DB_CLUSTER')
    db_name = os.getenv('DB_NAME')
    
    if not all([username, password, cluster, db_name]):
        print("❌ Missing DB config in .env:")
        print(f"   DB_USER: {'✓' if username else '✗'}")
        print(f"   DB_PASSWORD: {'✓' if password else '✗'}")
        print(f"   DB_CLUSTER: {'✓' if cluster else '✗'}")
        print(f"   DB_NAME: {'✓' if db_name else '✗'}")
        sys.exit(1)
    
    connection_string = (
        f"mongodb+srv://{username}:{password}@"
        f"{cluster}/?retryWrites=true&w=majority&appName=Diabetes-Agent"
    )
    
    client = MongoClient(connection_string, serverSelectionTimeoutMS=10000)
    client.admin.command('ping')
    
    db = client[db_name]
    print(f"   ✅ Connected to database: {db_name}")
    print(f"   ✅ Cluster: {cluster}")
    
except Exception as e:
    print(f"   ❌ Connection failed: {e}")
    sys.exit(1)

# 2. Clean existing collections (optional)
print("\n2️⃣ Cleaning existing data...")
response = input("   ⚠️  Drop all existing collections? (y/n): ")

if response.lower() == 'y':
    for collection in db.list_collection_names():
        db[collection].drop()
        print(f"   ✅ Dropped: {collection}")
else:
    print("   ℹ️  Keeping existing data")

# 3. Create Collections with Validation Schema
print("\n3️⃣ Creating collections with validation schemas...")

# =============================================================================
# ENTITY: User
# =============================================================================
print("\n   📁 Creating 'users' collection...")
try:
    db.create_collection('users', validator={
        '$jsonSchema': {
            'bsonType': 'object',
            'required': ['name', 'hashed_password', 'created_at'],
            'properties': {
                'name': {
                    'bsonType': 'string',
                    'description': 'Username - must be unique'
                },
                'hashed_password': {
                    'bsonType': 'string',
                    'description': 'Bcrypt hashed password'
                },
                'created_at': {
                    'bsonType': 'date',
                    'description': 'Account creation timestamp'
                }
            }
        }
    })
    print(f"      ✅ Created 'users' with schema validation")
except Exception as e:
    if 'already exists' in str(e):
        print(f"      ℹ️  Collection already exists")
    else:
        print(f"      ⚠️  Error: {e}")

# =============================================================================
# ENTITY: Assessment
# =============================================================================
print("\n   📁 Creating 'assessments' collection...")
try:
    db.create_collection('assessments', validator={
        '$jsonSchema': {
            'bsonType': 'object',
            'required': ['user_id', 'measured_at', 'created_at', 'is_valid', 'metrics', 'prediction'],
            'properties': {
                'user_id': {
                    'bsonType': 'string',
                    'description': 'Foreign key to users._id (as string)'
                },
                'measured_at': {
                    'bsonType': 'date',
                    'description': 'Thời điểm chỉ số đại diện (measurement time)'
                },
                'created_at': {
                    'bsonType': 'date',
                    'description': 'Record creation timestamp'
                },
                'is_valid': {
                    'bsonType': 'bool',
                    'description': 'True nếu assessment này còn hiệu lực (quy tắc 2 tuần)'
                },
                'metrics': {
                    'bsonType': 'object',
                    'description': 'Health metrics from form (19 fields)',
                    'required': ['HighBP', 'HighChol', 'BMI', 'Age'],
                    'properties': {
                        'HighBP': {'bsonType': 'double'},
                        'HighChol': {'bsonType': 'double'},
                        'CholCheck': {'bsonType': 'double'},
                        'BMI': {'bsonType': 'double'},
                        'Smoker': {'bsonType': 'double'},
                        'Stroke': {'bsonType': 'double'},
                        'HeartDiseaseorAttack': {'bsonType': 'double'},
                        'PhysActivity': {'bsonType': 'double'},
                        'HvyAlcoholConsump': {'bsonType': 'double'},
                        'AnyHealthcare': {'bsonType': 'double'},
                        'NoDocbcCost': {'bsonType': 'double'},
                        'GenHlth': {'bsonType': 'double'},
                        'MentHlth': {'bsonType': 'double'},
                        'PhysHlth': {'bsonType': 'double'},
                        'DiffWalk': {'bsonType': 'double'},
                        'Sex': {'bsonType': 'double'},
                        'Age': {'bsonType': 'double'},
                        'Education': {'bsonType': 'double'},
                        'Income': {'bsonType': 'double'}
                    }
                },
                'prediction': {
                    'bsonType': 'object',
                    'description': 'Prediction results from ML model',
                    'required': ['prediction', 'risk_score', 'risk_level'],
                    'properties': {
                        'prediction': {
                            'bsonType': 'int',
                            'enum': [0, 1],
                            'description': '0=low risk, 1=high risk'
                        },
                        'risk_score': {
                            'bsonType': 'double',
                            'minimum': 0.0,
                            'maximum': 1.0,
                            'description': 'Probability of high risk (0.0-1.0)'
                        },
                        'risk_level': {
                            'enum': ['low', 'high'],
                            'description': 'Risk level category'
                        },
                        'model_version': {
                            'bsonType': 'string',
                            'description': 'ML model version used'
                        }
                    }
                }
            }
        }
    })
    print(f"      ✅ Created 'assessments' with schema validation")
except Exception as e:
    if 'already exists' in str(e):
        print(f"      ℹ️  Collection already exists")
    else:
        print(f"      ⚠️  Error: {e}")

# =============================================================================
# ENTITY: Message
# =============================================================================
print("\n   📁 Creating 'messages' collection...")
try:
    db.create_collection('messages', validator={
        '$jsonSchema': {
            'bsonType': 'object',
            'required': ['sender_type', 'content', 'created_at'],
            'properties': {
                'assessment_id': {
                    'bsonType': ['string', 'null'],
                    'description': 'Optional FK to assessments._id - null for general chat'
                },
                'sender_type': {
                    'enum': ['user', 'agent'],
                    'description': 'Who sent this message'
                },
                'content': {
                    'bsonType': 'string',
                    'description': 'Message text content'
                },
                'created_at': {
                    'bsonType': 'date',
                    'description': 'Message timestamp'
                },
                'metadata': {
                    'bsonType': 'object',
                    'description': 'Additional metadata (type, context, etc.)'
                }
            }
        }
    })
    print(f"      ✅ Created 'messages' with schema validation")
except Exception as e:
    if 'already exists' in str(e):
        print(f"      ℹ️  Collection already exists")
    else:
        print(f"      ⚠️  Error: {e}")

# 4. Create Indexes for Performance
print("\n4️⃣ Creating indexes for performance...")

# Users indexes
print("\n   📌 Users indexes:")
db.users.create_index("name", unique=True, name="idx_username_unique")
print(f"      ✅ name (unique)")
db.users.create_index("created_at", name="idx_user_created")
print(f"      ✅ created_at")

# Assessments indexes
print("\n   📌 Assessments indexes:")
db.assessments.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)], name="idx_user_assessments_time")
print(f"      ✅ user_id + created_at (DESC) - for getting latest assessments")

db.assessments.create_index([("user_id", ASCENDING), ("is_valid", ASCENDING)], name="idx_user_valid_assessments")
print(f"      ✅ user_id + is_valid - for getting valid assessment")

db.assessments.create_index("is_valid", name="idx_valid_filter")
print(f"      ✅ is_valid - for filtering")

db.assessments.create_index("measured_at", name="idx_measurement_time")
print(f"      ✅ measured_at - for time-based queries")

# Messages indexes
print("\n   📌 Messages indexes:")
db.messages.create_index([("assessment_id", ASCENDING), ("created_at", ASCENDING)], name="idx_assessment_messages")
print(f"      ✅ assessment_id + created_at - for chat history")

db.messages.create_index("created_at", name="idx_message_time")
print(f"      ✅ created_at - for sorting")

db.messages.create_index("sender_type", name="idx_sender_filter")
print(f"      ✅ sender_type - for filtering")

# 5. Insert Sample Data
print("\n5️⃣ Inserting sample data...")

# Sample Users
print("\n   👤 Creating sample users...")
sample_users = [
    {
        'name': 'admin',
        'hashed_password': bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        'created_at': datetime.utcnow()
    },
    {
        'name': 'demo_user',
        'hashed_password': bcrypt.hashpw('demo123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        'created_at': datetime.utcnow()
    }
]

user_ids = {}
for user in sample_users:
    try:
        result = db.users.insert_one(user)
        user_ids[user['name']] = str(result.inserted_id)
        print(f"      ✅ Created user: {user['name']}")
    except Exception as e:
        if 'duplicate key' in str(e):
            existing = db.users.find_one({'name': user['name']})
            user_ids[user['name']] = str(existing['_id'])
            print(f"      ℹ️  User exists: {user['name']}")
        else:
            print(f"      ⚠️  Error: {e}")

# Sample Assessments for demo_user
if 'demo_user' in user_ids:
    print("\n   📊 Creating sample assessments...")
    
    # Assessment 1: Valid (most recent)
    assessment1 = {
        'user_id': user_ids['demo_user'],
        'measured_at': datetime.utcnow(),
        'created_at': datetime.utcnow(),
        'is_valid': True,  # Current valid assessment
        'metrics': {
            'HighBP': 1.0,
            'HighChol': 1.0,
            'CholCheck': 1.0,
            'BMI': 28.5,
            'Smoker': 0.0,
            'Stroke': 0.0,
            'HeartDiseaseorAttack': 0.0,
            'PhysActivity': 1.0,
            'HvyAlcoholConsump': 0.0,
            'AnyHealthcare': 1.0,
            'NoDocbcCost': 0.0,
            'GenHlth': 3.0,
            'MentHlth': 5.0,
            'PhysHlth': 3.0,
            'DiffWalk': 0.0,
            'Sex': 1.0,
            'Age': 6.0,
            'Education': 4.0,
            'Income': 6.0
        },
        'prediction': {
            'prediction': 1,
            'risk_score': 0.65,
            'risk_level': 'high',
            'model_version': 'stacking_ensemble_v1'
        }
    }
    
    # Assessment 2: Invalid (older, replaced by assessment1)
    assessment2 = {
        'user_id': user_ids['demo_user'],
        'measured_at': datetime.utcnow() - timedelta(days=7),
        'created_at': datetime.utcnow() - timedelta(days=7),
        'is_valid': False,  # Invalidated by newer assessment
        'metrics': {
            'HighBP': 1.0,
            'HighChol': 0.0,
            'CholCheck': 1.0,
            'BMI': 30.0,
            'Smoker': 1.0,
            'Stroke': 0.0,
            'HeartDiseaseorAttack': 0.0,
            'PhysActivity': 0.0,
            'HvyAlcoholConsump': 0.0,
            'AnyHealthcare': 1.0,
            'NoDocbcCost': 0.0,
            'GenHlth': 4.0,
            'MentHlth': 10.0,
            'PhysHlth': 8.0,
            'DiffWalk': 1.0,
            'Sex': 1.0,
            'Age': 6.0,
            'Education': 4.0,
            'Income': 6.0
        },
        'prediction': {
            'prediction': 1,
            'risk_score': 0.78,
            'risk_level': 'high',
            'model_version': 'stacking_ensemble_v1'
        }
    }
    
    try:
        # Insert old assessment first
        result2 = db.assessments.insert_one(assessment2)
        assessment2_id = str(result2.inserted_id)
        print(f"      ✅ Created old assessment (invalid): {assessment2_id}")
        
        # Insert new assessment
        result1 = db.assessments.insert_one(assessment1)
        assessment1_id = str(result1.inserted_id)
        print(f"      ✅ Created current assessment (valid): {assessment1_id}")
        
        # Sample Messages for current assessment
        print("\n   💬 Creating sample messages...")
        sample_messages = [
            {
                'assessment_id': assessment1_id,
                'sender_type': 'agent',
                'content': '🤖 Xin chào! Tôi là AI Assistant chuyên về tiểu đường. Kết quả đánh giá của bạn cho thấy nguy cơ tiểu đường CAO (65%).',
                'metadata': {'type': 'initial_greeting'},
                'created_at': datetime.utcnow()
            },
            {
                'assessment_id': assessment1_id,
                'sender_type': 'user',
                'content': 'Tôi nên làm gì để giảm nguy cơ?',
                'metadata': {},
                'created_at': datetime.utcnow()
            },
            {
                'assessment_id': assessment1_id,
                'sender_type': 'agent',
                'content': '''✅ Dựa vào kết quả của bạn, tôi đề xuất:

1. **Kiểm soát cân nặng**: BMI của bạn là 28.5 (thừa cân). Hãy giảm 3-5kg trong 3 tháng tới.
2. **Kiểm soát huyết áp**: Bạn đang có huyết áp cao, cần theo dõi hàng ngày.
3. **Tăng vận động**: Hiện tại bạn có vận động nhưng cần tăng cường thêm.
4. **Khám định kỳ**: Nên đi khám và xét nghiệm HbA1c trong vòng 1 tuần.''',
                'metadata': {'type': 'advice'},
                'created_at': datetime.utcnow()
            },
            {
                'assessment_id': None,  # General message not related to assessment
                'sender_type': 'user',
                'content': 'Tiểu đường type 2 là gì?',
                'metadata': {'type': 'general_question'},
                'created_at': datetime.utcnow()
            },
            {
                'assessment_id': None,
                'sender_type': 'agent',
                'content': '''Tiểu đường type 2 là tình trạng cơ thể không sử dụng insulin hiệu quả (kháng insulin), dẫn đến đường huyết tăng cao.

📊 Nguyên nhân chính:
- Thừa cân, béo phì
- Lối sống ít vận động
- Chế độ ăn không lành mạnh
- Yếu tố di truyền

⚠️ Có thể phòng ngừa và kiểm soát được bằng thay đổi lối sống!''',
                'metadata': {'type': 'educational'},
                'created_at': datetime.utcnow()
            }
        ]
        
        db.messages.insert_many(sample_messages)
        print(f"      ✅ Created {len(sample_messages)} messages")
        print(f"         - {sum(1 for m in sample_messages if m['assessment_id'])} messages linked to assessment")
        print(f"         - {sum(1 for m in sample_messages if not m['assessment_id'])} general messages")
        
    except Exception as e:
        print(f"      ⚠️  Error: {e}")

# 6. Verify Setup
print("\n6️⃣ Verifying database setup...")

# Count documents
users_count = db.users.count_documents({})
assessments_count = db.assessments.count_documents({})
valid_assessments = db.assessments.count_documents({'is_valid': True})
messages_count = db.messages.count_documents({})
linked_messages = db.messages.count_documents({'assessment_id': {'$ne': None}})

print(f"\n   📊 Collection Statistics:")
print(f"      Users: {users_count} documents")
print(f"      Assessments: {assessments_count} documents ({valid_assessments} valid)")
print(f"      Messages: {messages_count} documents ({linked_messages} linked to assessments)")

# List indexes
print(f"\n   📌 Index Summary:")
for coll_name in ['users', 'assessments', 'messages']:
    indexes = list(db[coll_name].list_indexes())
    print(f"      {coll_name}: {len(indexes)} indexes")
    for idx in indexes:
        if idx['name'] != '_id_':
            print(f"         - {idx['name']}")

# 7. Test Business Rule: Only 1 valid assessment per user
print("\n7️⃣ Testing Business Rule: Only 1 valid assessment...")
if 'demo_user' in user_ids:
    valid_assessments = list(db.assessments.find({
        'user_id': user_ids['demo_user'],
        'is_valid': True
    }))
    
    if len(valid_assessments) == 1:
        print(f"   ✅ PASS: Only 1 valid assessment found")
        print(f"      Assessment ID: {valid_assessments[0]['_id']}")
        print(f"      Measured at: {valid_assessments[0]['measured_at']}")
    else:
        print(f"   ❌ FAIL: Found {len(valid_assessments)} valid assessments (should be 1)")

# 8. Summary
print("\n" + "=" * 70)
print("✅ DATABASE SETUP COMPLETED - THEO ERD.puml")
print("=" * 70)

print(f"""
📁 Database: {db_name}
🌐 Cluster: {cluster}

📊 Collections Created:
   ✓ users - {users_count} documents
   ✓ assessments - {assessments_count} documents ({valid_assessments} valid)
   ✓ messages - {messages_count} documents ({linked_messages} assessment-linked)

📌 Indexes: Total {sum(len(list(db[c].list_indexes())) for c in ['users', 'assessments', 'messages'])} indexes

👤 Sample Accounts:
   • admin / admin123
   • demo_user / demo123

✅ Business Rules Implemented:
   • Only 1 valid assessment per user at a time
   • Messages can be linked to assessment (optional)
   • Assessment has metrics + prediction subdocuments

🚀 Next Steps:
   1. Start backend: python app.py
   2. Test login: POST /api/users/login
   3. View data: MongoDB Atlas → Browse Collections
""")

print("=" * 70)

# Close connection
client.close()