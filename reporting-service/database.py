import sys
import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from dotenv import load_dotenv

# Load biến môi trường từ file .env (chỉ có tác dụng ở Local)
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
TLS_CERT_KEY_FILE = os.getenv("TLS_CERT_KEY_FILE")

# 1. Kiểm tra biến môi trường
if not MONGO_URI:
    print("CRITICAL ERROR: Missing MONGO_URI in environment variables")
    sys.exit(1)

if not TLS_CERT_KEY_FILE:
    print("CRITICAL ERROR: Missing TLS_CERT_KEY_FILE in environment variables")
    sys.exit(1)

# 2. Kiểm tra sự tồn tại của file chứng chỉ (QUAN TRỌNG)
if not os.path.exists(TLS_CERT_KEY_FILE):
    print(f"CRITICAL ERROR: Certificate file NOT found at path: {TLS_CERT_KEY_FILE}")
    print("HINT (Render): Ensure you created a Secret File named 'cert.pem' and set TLS_CERT_KEY_FILE to '/etc/secrets/cert.pem'")
    sys.exit(1) # Dừng chương trình ngay, không cố kết nối để tránh lỗi khó hiểu

print(f"Using certificate at: {TLS_CERT_KEY_FILE}")

# 3. Kết nối
try:
    client = MongoClient(
        MONGO_URI,
        tls=True,
        tlsCertificateKeyFile=TLS_CERT_KEY_FILE
    )
    
    # Ping thử để đảm bảo kết nối thực sự thành công
    client.admin.command("ping")
    print("✅ Connected to MongoDB Atlas successfully!")

except OperationFailure as e:
    print(f"❌ Authentication failed (Certificate might be invalid): {e}")
    sys.exit(1)
except ConnectionFailure as e:
    print(f"❌ Connection failed (Check Network/URI): {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ An unexpected error occurred: {e}")
    sys.exit(1)

# 4. Chọn database
db = client["reporting_service"]
reports_collection = db["reports"]