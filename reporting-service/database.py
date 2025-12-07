import sys
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from pymongo.errors import ConnectionFailure

# Load biến môi trường từ file .env
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
TLS_CERT_KEY_FILE = os.getenv("TLS_CERT_KEY_FILE")

if not MONGO_URI:
    print("ERROR: Missing MONGO_URI in .env file")
    sys.exit(1)

# Kiểm tra file chứng chỉ
if TLS_CERT_KEY_FILE and not os.path.exists(TLS_CERT_KEY_FILE):
    print(f"WARNING: TLS certificate not found at {TLS_CERT_KEY_FILE}")
    TLS_CERT_KEY_FILE = None  # bỏ qua nếu không tồn tại file

# Tạo client
client = MongoClient(
    MONGO_URI,
    tls=True,
    tlsCertificateKeyFile=TLS_CERT_KEY_FILE
)

# Test connection
try:
    client.admin.command("ping")
    print("Connected to MongoDB!")
except ConnectionFailure:
    print("Failed to connect to MongoDB.")
    sys.exit(1)

# Chọn database đúng của Reporting Service
db = client["reporting_service"]

# Collections
reports_collection = db["reports"]

print("Using database: reporting_service")
