import os

import httpx
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("PLATFORM_BASE_URL", "https://api.gonitro.dev")
CLIENT_ID = os.getenv("PLATFORM_CLIENT_ID")
CLIENT_SECRET = os.getenv("PLATFORM_CLIENT_SECRET")


def get_access_token() -> str:
    """Get OAuth2 access token using client credentials"""
    url = f"{BASE_URL}/oauth/token"
    data = {"clientID": CLIENT_ID, "clientSecret": CLIENT_SECRET}

    response = httpx.post(url, json=data)
    response.raise_for_status()
    return response.json()["accessToken"]


def test_connection(token: str) -> bool | None:
    """Test API connection with a simple request"""
    url = f"{BASE_URL}/jobs/test-job-id/status"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = httpx.get(url, headers=headers)
        # 404 is expected for non-existent job, but proves auth works
        if response.status_code == 404:
            print("✅ Authentication successful (404 expected for test job ID)")
            return True
        response.raise_for_status()
        return True  # noqa: TRY300
    except httpx.HTTPError as e:
        if e.response.status_code == 404:
            print("✅ Authentication successful (404 expected for test job ID)")
            return True
        raise


def main() -> None:
    if not CLIENT_ID or not CLIENT_SECRET:
        print("❌ Missing credentials!")
        print("To get your credentials:")
        print("1. Go to https://admin.gonitro.com")
        print("2. Navigate to Settings → API")
        print("3. Click 'Create Application'")
        print("4. Name your application and save the Client ID and Client Secret")
        print("5. Set environment variables:")
        print("   export PLATFORM_CLIENT_ID=<YOUR_CLIENT_ID>")
        print("   export PLATFORM_CLIENT_SECRET=<YOUR_CLIENT_SECRET>")
        return

    try:
        print("🔐 Getting access token...")
        token = get_access_token()
        print("✅ Token obtained successfully")

        print("🧪 Testing API connection...")
        test_connection(token)
        print("✅ API connection successful")

        print("\n🎉 Setup complete! You can now use the Platform API.")
        print("📖 See https://developers.gonitro.com/docs for API documentation")

    except Exception as e:  # noqa: BLE001
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
