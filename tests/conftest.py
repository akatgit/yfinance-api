import pytest
import requests
import os
from dotenv import load_dotenv
import time
import subprocess
import signal

load_dotenv()

# Test configuration
BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", None)
TEST_TICKER = "AAPL"
INVALID_TICKER = "INVALIDTICKER999"

@pytest.fixture(scope="session")
def base_url():
    """Base URL for API testing"""
    return BASE_URL

@pytest.fixture(scope="session")
def api_key():
    """API key for authentication tests"""
    return API_KEY

@pytest.fixture(scope="session")
def test_ticker():
    """Valid ticker symbol for testing"""
    return TEST_TICKER

@pytest.fixture(scope="session")
def invalid_ticker():
    """Invalid ticker for error testing"""
    return INVALID_TICKER

@pytest.fixture(scope="session")
def http_client():
    """Reusable HTTP client with session"""
    session = requests.Session()
    session.headers.update({"User-Agent": "yfinance-api-test-suite/1.0"})
    yield session
    session.close()

@pytest.fixture(scope="session", autouse=True)
def start_server():
    """Start the FastAPI server for testing (optional - use if testing locally)"""
    # Only start server if running locally and not already running
    if "localhost" in BASE_URL or "127.0.0.1" in BASE_URL:
        try:
            # Check if server is already running
            response = requests.get(f"{BASE_URL}/health", timeout=2)
            if response.status_code == 200:
                print(f"\n✓ Server already running at {BASE_URL}")
                yield
                return
        except requests.exceptions.RequestException:
            pass
        
        # Start server
        print(f"\n→ Starting server at {BASE_URL}...")
        port = BASE_URL.split(":")[-1]
        process = subprocess.Popen(
            ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", port],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for server to be ready
        max_retries = 30
        for i in range(max_retries):
            try:
                response = requests.get(f"{BASE_URL}/health", timeout=1)
                if response.status_code == 200:
                    print(f"✓ Server started successfully")
                    break
            except requests.exceptions.RequestException:
                time.sleep(1)
        else:
            process.kill()
            raise RuntimeError("Server failed to start within 30 seconds")
        
        yield
        
        # Teardown
        print("\n→ Stopping server...")
        process.send_signal(signal.SIGTERM)
        process.wait(timeout=5)
    else:
        # Remote server - no setup needed
        yield

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "smoke: mark test as smoke test for quick validation"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )
    config.addinivalue_line(
        "markers", "edge_case: mark test as edge case validation"
    )
