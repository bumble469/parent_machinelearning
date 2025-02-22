import aiohttp
import os
# import asyncio
from dotenv import load_dotenv

load_dotenv()
FLASK_API_URL = os.getenv("REACT_APP_FLASK_API_URL")

async def wake_up_flask_api():
    """Ping the Flask API to wake it up before sending the main request."""
    try:
        print("Waking up Flask API...")
        async with aiohttp.ClientSession() as session:
            async with session.get(FLASK_API_URL, timeout=10) as response:
                if response.status == 200:
                    print("Flask API is awake!")
    except Exception as error:
        print("Flask API might still be sleeping, proceeding with request...")

async def call_flask_encrypt_api(endpoint, data):
    try:
        await wake_up_flask_api()  # Wake up the API before calling
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{FLASK_API_URL}/{endpoint}",
                json={"data": data},
                headers={'Content-Type': 'application/json'}
            ) as response:
                response.raise_for_status()
                return await response.json()
    except aiohttp.ClientError as error:
        print("Failed to call Flask API:", error)
        raise Exception("Failed to call Flask API")

async def call_flask_decrypt_api(encrypted_data, encrypted_aes_key):
    try:
        await wake_up_flask_api()  # Wake up API before decrypt request
        decrypt_data = {
            "encrypted_data": encrypted_data,
            "encrypted_aes_key": encrypted_aes_key
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{FLASK_API_URL}/decrypt",
                json=decrypt_data,
                headers={'Content-Type': 'application/json'}
            ) as response:
                response.raise_for_status()
                return (await response.json()).get("decrypted_data")
    except aiohttp.ClientError as error:
        print("Failed to call Flask decrypt:", error)
        raise Exception("Failed to decrypt data")

# # Example to test the wake-up function (Run this separately)
# if __name__ == "__main__":
#     asyncio.run(wake_up_flask_api())
