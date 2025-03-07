from dotenv import load_dotenv
import os


load_dotenv()
ADMINS = list(map(int, os.getenv('ADMINS', '').split(','))) if os.getenv('ADMINS') else []