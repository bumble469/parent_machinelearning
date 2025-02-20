import aiohttp

FLASK_API_URL = "https://parent-encryption.onrender.com"

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
    except aiohttp.ClientError as error:
        print("Failed to call Flask API:", error)
        raise Exception("Failed to call Flask API")

async def call_flask_decrypt_api(encrypted_data, encrypted_aes_key):
    try:
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
