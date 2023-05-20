from firebase_admin import credentials
from dotenv import load_dotenv
from os import getenv

load_dotenv()

credentials = credentials.Certificate({
    "type": "service_account",
    "project_id": getenv("PROJECT_ID"),
    "private_key_id": getenv("PRIVATE_KEY_ID"),
    "private_key": getenv("PRIVATE_KEY").replace('\\n', '\n'),
    "client_email": getenv("CLIENT_EMAIL"),
    "client_id": getenv("CLIENT_ID"),
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": getenv("CLIENT_X509_CERT_URL"),
    "universe_domain": "googleapis.com"
})