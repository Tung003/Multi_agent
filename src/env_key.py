import os
from dotenv import load_dotenv

load_dotenv()  # load kay in file .env

api_key = os.getenv("GROQ_API_KEY")

# use api_key in headers
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}
print(api_key)