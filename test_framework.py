#!/usr/bin/env python3
"""
Test script for Flask Microservice Framework
Tests basic functionality of all services including authentication
"""

import requests
import json
import time
import sys
from datetime import datetime

# Service URLs
SERVICES = {
    'api-gateway': 'http://localhost:8000',
    'assets-service': 'http://localhost:8001',
    'files-service': 'http://localhost:8002',
    'transcode-service': 'http://localhost:8003',
    'search-service': 'http://localhost:8004'
}

# Test credentials (using default passwords)
TEST_CREDENTIALS = {
    'admin': {
        'username': 'admin',
        'password': 'admin123'
    },
    'user': {
        'username': 'user',
        'password': 'user123'
    }
}

def test_health_checks():
    """Test health check endpoints for all services"""
    print("🔍 Testing health checks...")
    
    for service_name, url in SERVICES.items():
        try:
            response = requests.get(f"{url}/health", timeout=5)
            if response.status_code == 200:
                print(f"✅ {service_name}: Healthy")
            else:
                print(f"❌ {service_name}: Unhealthy (Status: {response.status_code})")
        except requests.exceptions.RequestException as e:
            print(f"❌ {service_name}: Connection failed - {e}")

def test_authentication():
    """Test authentication functionality"""
    print("\n🔐 Testing Authentication...")
    
    api_gateway = SERVICES['api-gateway']
    
    # Test 1: Login with valid admin credentials
    print("  Testing admin login...")
    try:
        response = requests.post(
            f"{api_gateway}/auth/login",
            json=TEST_CREDENTIALS['admin'],
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            admin_token = data['token']
            print(f"    ✅ Admin login successful, token received")
            
            # Test 2: Verify admin token
            print("  Testing token verification...")
            response = requests.post(
                f"{api_gateway}/auth/verify",
                headers={'Authorization': f'Bearer {admin_token}'},
                timeout=10
            )
            
            if response.status_code == 200:
                print("    ✅ Token verification successful")
            else:
                print(f"    ❌ Token verification failed: {response.status_code}")
        else:
            print(f"    ❌ Admin login failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"    ❌ Admin login test failed: {e}")
        return None
    
    # Test 3: Login with valid user credentials
    print("  Testing user login...")
    try:
        response = requests.post(
            f"{api_gateway}/auth/login",
            json=TEST_CREDENTIALS['user'],
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            user_token = data['token']
            print(f"    ✅ User login successful, token received")
        else:
            print(f"    ❌ User login failed: {response.status_code}")
            user_token = None
            
    except Exception as e:
        print(f"    ❌ User login test failed: {e}")
        user_token = None
    
    # Test 4: Login with invalid credentials
    print("  Testing invalid login...")
    try:
        response = requests.post(
            f"{api_gateway}/auth/login",
            json={'username': 'admin', 'password': 'wrongpassword'},
            timeout=10
        )
        
        if response.status_code == 401:
            print("    ✅ Invalid login correctly rejected")
        else:
            print(f"    ❌ Invalid login should have been rejected: {response.status_code}")
            
    except Exception as e:
        print(f"    ❌ Invalid login test failed: {e}")
    
    # Test 5: Access protected endpoint without token
    print("  Testing protected endpoint without token...")
    try:
        response = requests.get(
            f"{api_gateway}/api/assets",
            timeout=10
        )
        
        if response.status_code == 401:
            print("    ✅ Protected endpoint correctly requires authentication")
        else:
            print(f"    ❌ Protected endpoint should require authentication: {response.status_code}")
            
    except Exception as e:
        print(f"    ❌ Protected endpoint test failed: {e}")
    
    # Test 6: Access protected endpoint with valid token
    print("  Testing protected endpoint with valid token...")
    if admin_token:
        try:
            response = requests.get(
                f"{api_gateway}/api/assets",
                headers={'Authorization': f'Bearer {admin_token}'},
                timeout=10
            )
            
            if response.status_code == 200:
                print("    ✅ Protected endpoint accessible with valid token")
            else:
                print(f"    ❌ Protected endpoint should be accessible: {response.status_code}")
                
        except Exception as e:
            print(f"    ❌ Protected endpoint with token test failed: {e}")
    
    # Test 7: Get current user info
    print("  Testing current user info...")
    if admin_token:
        try:
            response = requests.get(
                f"{api_gateway}/auth/me",
                headers={'Authorization': f'Bearer {admin_token}'},
                timeout=10
            )
            
            if response.status_code == 200:
                user_info = response.json()['user']
                print(f"    ✅ Current user info: {user_info['username']} ({user_info['role']})")
            else:
                print(f"    ❌ Failed to get user info: {response.status_code}")
                
        except Exception as e:
            print(f"    ❌ User info test failed: {e}")
    
    # Test 8: Test with expired/invalid token
    print("  Testing invalid token...")
    try:
        response = requests.get(
            f"{api_gateway}/api/assets",
            headers={'Authorization': 'Bearer invalid.token.here'},
            timeout=10
        )
        
        if response.status_code == 401:
            print("    ✅ Invalid token correctly rejected")
        else:
            print(f"    ❌ Invalid token should have been rejected: {response.status_code}")
            
    except Exception as e:
        print(f"    ❌ Invalid token test failed: {e}")
    
    return admin_token

def test_assets_service_with_auth(token):
    """Test assets service functionality with authentication"""
    print("\n📁 Testing Assets Service (with authentication)...")
    
    if not token:
        print("  ❌ Skipping assets test - no valid token")
        return
    
    # Create an asset with random name and filename
    import uuid
    random_id = uuid.uuid4().hex[:8]
    random_filename = f"test_file_auth_{random_id}.jpg"
    
    asset_data = {
        "name": f"Test Asset Auth {random_id}",
        "description": "A test asset for framework testing",
        "file_path": f"/test/path/{random_filename}",
        "file_size": 1024,
        "mime_type": "image/jpeg",
        "metadata": {"width": 1920, "height": 1080},
        "tags": ["test", "image", "demo"]
    }
    
    try:
        # Create asset with authentication
        response = requests.post(
            f"{SERVICES['api-gateway']}/api/assets",
            json=asset_data,
            headers={'Authorization': f'Bearer {token}'},
            timeout=10
        )
        
        if response.status_code == 201:
            asset = response.json()['data']
            asset_id = asset['id']
            print(f"  ✅ Asset created with ID: {asset_id}")
            
            # Get the asset
            response = requests.get(
                f"{SERVICES['api-gateway']}/api/assets/{asset_id}",
                headers={'Authorization': f'Bearer {token}'},
                timeout=10
            )
            
            if response.status_code == 200:
                print("  ✅ Asset retrieved successfully")
            else:
                print(f"  ❌ Failed to retrieve asset: {response.status_code}")
                
        else:
            print(f"  ❌ Failed to create asset: {response.status_code}")
            
    except Exception as e:
        print(f"  ❌ Assets service test failed: {e}")

def test_files_service_with_auth(token):
    """Test files service functionality with authentication"""
    print("\n📄 Testing Files Service (with authentication)...")
    
    if not token:
        print("  ❌ Skipping files test - no valid token")
        return
    
    try:
        # Get files list with authentication
        response = requests.get(
            f"{SERVICES['api-gateway']}/api/files",
            headers={'Authorization': f'Bearer {token}'},
            timeout=10
        )
        
        if response.status_code == 200:
            print("  ✅ Files service is responding")
        else:
            print(f"  ❌ Files service test failed: {response.status_code}")
            
    except Exception as e:
        print(f"  ❌ Files service test failed: {e}")

def test_transcode_service_with_auth(token):
    """Test transcode service functionality with authentication"""
    print("\n🎬 Testing Transcode Service (with authentication)...")
    
    if not token:
        print("  ❌ Skipping transcode test - no valid token")
        return
    
    try:
        # Get supported formats with authentication
        response = requests.get(
            f"{SERVICES['api-gateway']}/api/transcode/formats",
            headers={'Authorization': f'Bearer {token}'},
            timeout=10
        )
        
        if response.status_code == 200:
            formats = response.json()['data']
            print(f"  ✅ Supported formats: {list(formats.keys())}")
        else:
            print(f"  ❌ Failed to get formats: {response.status_code}")
            
    except Exception as e:
        print(f"  ❌ Transcode service test failed: {e}")

def test_search_service_with_auth(token):
    """Test search service functionality with authentication"""
    print("\n🔍 Testing Search Service (with authentication)...")
    
    if not token:
        print("  ❌ Skipping search test - no valid token")
        return
    
    try:
        # Get search analytics with authentication
        response = requests.get(
            f"{SERVICES['api-gateway']}/api/search/analytics",
            headers={'Authorization': f'Bearer {token}'},
            timeout=10
        )
        
        if response.status_code == 200:
            analytics = response.json()['data']
            print(f"  ✅ Search analytics: {analytics['total_indexed']} items indexed")
        else:
            print(f"  ❌ Failed to get analytics: {response.status_code}")
            
    except Exception as e:
        print(f"  ❌ Search service test failed: {e}")

def test_api_gateway_with_auth(token):
    """Test API gateway functionality with authentication"""
    print("\n🌐 Testing API Gateway (with authentication)...")
    
    if not token:
        print("  ❌ Skipping API gateway test - no valid token")
        return
    
    try:
        # Test service status with authentication
        response = requests.get(
            f"{SERVICES['api-gateway']}/api/status",
            headers={'Authorization': f'Bearer {token}'},
            timeout=10
        )
        
        if response.status_code == 200:
            status = response.json()
            print("  ✅ API Gateway is responding")
            print(f"     Services status: {list(status.get('services', {}).keys())}")
        else:
            print(f"  ❌ API Gateway test failed: {response.status_code}")
            
    except Exception as e:
        print(f"  ❌ API Gateway test failed: {e}")

def test_assets_service():
    """Test assets service functionality (direct service access - no auth required)"""
    print("\n📁 Testing Assets Service (direct access)...")
    
    # Create an asset directly to the assets service with random name and filename
    import uuid
    random_id = uuid.uuid4().hex[:8]
    random_filename = f"test_file_{random_id}.jpg"
    
    asset_data = {
        "name": f"Test Asset Direct {random_id}",
        "description": "A test asset for direct service testing",
        "file_path": f"/test/path/{random_filename}",
        "file_size": 1024,
        "mime_type": "image/jpeg",
        "metadata": {"width": 1920, "height": 1080},
        "tags": ["test", "image", "demo"]
    }
    
    try:
        # Create asset directly to assets service
        response = requests.post(
            f"{SERVICES['assets-service']}/api/assets",
            json=asset_data,
            timeout=10
        )
        
        if response.status_code == 201:
            asset = response.json()['data']
            asset_id = asset['id']
            print(f"✅ Asset created directly with ID: {asset_id}")
            
            # Get the asset directly
            response = requests.get(
                f"{SERVICES['assets-service']}/api/assets/{asset_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ Asset retrieved directly successfully")
            else:
                print(f"❌ Failed to retrieve asset directly: {response.status_code}")
                
        else:
            print(f"❌ Failed to create asset directly: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Assets service direct test failed: {e}")

def test_files_service():
    """Test files service functionality (direct service access - no auth required)"""
    print("\n📄 Testing Files Service (direct access)...")
    
    try:
        # Get files list directly from files service
        response = requests.get(
            f"{SERVICES['files-service']}/api/files",
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Files service direct access working")
        else:
            print(f"❌ Files service direct test failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Files service direct test failed: {e}")

def test_transcode_service():
    """Test transcode service functionality (direct service access - no auth required)"""
    print("\n🎬 Testing Transcode Service (direct access)...")
    
    try:
        # Get supported formats directly from transcode service
        response = requests.get(
            f"{SERVICES['transcode-service']}/api/transcode/formats",
            timeout=10
        )
        
        if response.status_code == 200:
            formats = response.json()['data']
            print(f"✅ Transcode service direct access working")
            print(f"   Supported formats: {list(formats.keys())}")
        else:
            print(f"❌ Failed to get formats directly: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Transcode service direct test failed: {e}")

def test_search_service():
    """Test search service functionality (direct service access - no auth required)"""
    print("\n🔍 Testing Search Service (direct access)...")
    
    try:
        # Get search analytics directly from search service
        response = requests.get(
            f"{SERVICES['search-service']}/api/search/analytics",
            timeout=10
        )
        
        if response.status_code == 200:
            analytics = response.json()['data']
            print(f"✅ Search service direct access working")
            print(f"   Total indexed: {analytics['total_indexed']} items")
        else:
            print(f"❌ Failed to get analytics directly: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Search service direct test failed: {e}")

def test_metrics_endpoints():
    """Test metrics endpoints for all services"""
    print("\n📊 Testing Metrics Endpoints...")
    
    for service_name, url in SERVICES.items():
        try:
            response = requests.get(f"{url}/metrics", timeout=5)
            if response.status_code == 200:
                print(f"✅ {service_name}: Metrics endpoint accessible")
            else:
                print(f"❌ {service_name}: Metrics endpoint failed (Status: {response.status_code})")
        except requests.exceptions.RequestException as e:
            print(f"❌ {service_name}: Metrics connection failed - {e}")

def main():
    """Main test function"""
    print("🧪 Flask Microservice Framework Test Suite")
    print("=" * 50)
    print(f"Test started at: {datetime.now()}")
    
    # Wait a moment for services to be ready
    print("\n⏳ Waiting for services to be ready...")
    time.sleep(5)
    
    # Run health checks first
    test_health_checks()
    
    # Run authentication tests
    admin_token = test_authentication()
    
    # Run authenticated service tests (through API gateway)
    test_assets_service_with_auth(admin_token)
    test_files_service_with_auth(admin_token)
    test_transcode_service_with_auth(admin_token)
    test_search_service_with_auth(admin_token)
    test_api_gateway_with_auth(admin_token)
    
    # Run direct service tests (bypassing API gateway)
    print("\n" + "=" * 50)
    print("🔄 Running direct service tests (bypassing API gateway)...")
    test_assets_service()
    test_files_service()
    test_transcode_service()
    test_search_service()
    
    # Test metrics endpoints
    test_metrics_endpoints()
    
    print("\n" + "=" * 50)
    print("✅ Test suite completed!")
    print("If authentication tests passed, your authentication system is working correctly.")
    print("Direct service tests verify individual service functionality.")

if __name__ == '__main__':
    main() 