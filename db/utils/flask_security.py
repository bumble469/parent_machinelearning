import aiohttp
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()
FLASK_API_URL = os.getenv("REACT_APP_FLASK_API_URL")

async def wake_up_flask_api():
    max_retries = 6  
    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(FLASK_API_URL, timeout=25) as response:
                    if response.status == 200:
                        return True  
        except Exception:
            await asyncio.sleep(5)  
    return False  

async def call_flask_encrypt_api(endpoint, data):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{FLASK_API_URL}/{endpoint}",
                json={"data": data},
                headers={'Content-Type': 'application/json'}
            ) as response:
                response.raise_for_status()
                return await response.json()
    except aiohttp.ClientError:
        raise Exception("Failed to call Flask API")

async def call_flask_decrypt_api(encrypted_data, encrypted_aes_key):
    decrypt_data = {
        "encrypted_data": encrypted_data,
        "encrypted_aes_key": encrypted_aes_key
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{FLASK_API_URL}/decrypt",
                json=decrypt_data,
                headers={'Content-Type': 'application/json'}
            ) as response:
                response.raise_for_status()
                return (await response.json()).get("decrypted_data")
    except aiohttp.ClientError:
        raise Exception("Failed to decrypt data")
