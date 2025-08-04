#!/usr/bin/env python3
"""
Test script for Flask Microservice Framework
Tests basic functionality of all services
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

def test_assets_service():
    """Test assets service functionality"""
    print("\n📁 Testing Assets Service...")
    
    # Create an asset
    asset_data = {
        "name": "Test Asset",
        "description": "A test asset for framework testing",
        "file_path": "/test/path/file.jpg",
        "file_size": 1024,
        "mime_type": "image/jpeg",
        "metadata": {"width": 1920, "height": 1080},
        "tags": ["test", "image", "demo"]
    }
    
    try:
        # Create asset
        response = requests.post(
            f"{SERVICES['assets-service']}/api/assets",
            json=asset_data,
            timeout=10
        )
        
        if response.status_code == 201:
            asset = response.json()['data']
            asset_id = asset['id']
            print(f"✅ Asset created with ID: {asset_id}")
            
            # Get the asset
            response = requests.get(
                f"{SERVICES['assets-service']}/api/assets/{asset_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ Asset retrieved successfully")
            else:
                print(f"❌ Failed to retrieve asset: {response.status_code}")
                
        else:
            print(f"❌ Failed to create asset: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Assets service test failed: {e}")

def test_files_service():
    """Test files service functionality"""
    print("\n📄 Testing Files Service...")
    
    try:
        # Get files list
        response = requests.get(
            f"{SERVICES['files-service']}/api/files",
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Files service is responding")
        else:
            print(f"❌ Files service test failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Files service test failed: {e}")

def test_transcode_service():
    """Test transcode service functionality"""
    print("\n🎬 Testing Transcode Service...")
    
    try:
        # Get supported formats
        response = requests.get(
            f"{SERVICES['transcode-service']}/api/transcode/formats",
            timeout=10
        )
        
        if response.status_code == 200:
            formats = response.json()['data']
            print(f"✅ Supported formats: {list(formats.keys())}")
        else:
            print(f"❌ Failed to get formats: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Transcode service test failed: {e}")

def test_search_service():
    """Test search service functionality"""
    print("\n🔍 Testing Search Service...")
    
    try:
        # Get search analytics
        response = requests.get(
            f"{SERVICES['search-service']}/api/search/analytics",
            timeout=10
        )
        
        if response.status_code == 200:
            analytics = response.json()['data']
            print(f"✅ Search analytics: {analytics['total_indexed']} items indexed")
        else:
            print(f"❌ Failed to get analytics: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Search service test failed: {e}")

def test_api_gateway():
    """Test API gateway functionality"""
    print("\n🌐 Testing API Gateway...")
    
    try:
        # Test service status
        response = requests.get(
            f"{SERVICES['api-gateway']}/api/status",
            timeout=10
        )
        
        if response.status_code == 200:
            status = response.json()
            print("✅ API Gateway is responding")
            print(f"   Services status: {list(status.get('services', {}).keys())}")
        else:
            print(f"❌ API Gateway test failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ API Gateway test failed: {e}")

def main():
    """Main test function"""
    print("🧪 Flask Microservice Framework Test Suite")
    print("=" * 50)
    print(f"Test started at: {datetime.now()}")
    
    # Wait a moment for services to be ready
    print("\n⏳ Waiting for services to be ready...")
    time.sleep(5)
    
    # Run tests
    test_health_checks()
    test_assets_service()
    test_files_service()
    test_transcode_service()
    test_search_service()
    test_api_gateway()
    
    print("\n" + "=" * 50)
    print("✅ Test suite completed!")
    print("If all tests passed, your microservice framework is working correctly.")

if __name__ == '__main__':
    main() 