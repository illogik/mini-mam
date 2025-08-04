#!/usr/bin/env python3
"""
Startup script for Flask Microservice Framework
Runs all services locally for development
"""

import os
import sys
import subprocess
import time
import signal
import threading
from pathlib import Path

# Add current directory and src directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

def run_service(service_name, service_path, port):
    """Run a service in a separate process"""
    print(f"Starting {service_name} on port {port}...")
    
    # Set environment variables
    env = os.environ.copy()
    env['FLASK_ENV'] = 'development'
    env['FLASK_DEBUG'] = 'true'
    
    # Set service-specific environment variables
    if service_name == 'api-gateway':
        env['API_GATEWAY_PORT'] = str(port)
    elif service_name == 'assets-service':
        env['ASSETS_SERVICE_PORT'] = str(port)
    elif service_name == 'files-service':
        env['FILES_SERVICE_PORT'] = str(port)
    elif service_name == 'transcode-service':
        env['TRANSCODE_SERVICE_PORT'] = str(port)
    elif service_name == 'search-service':
        env['SEARCH_SERVICE_PORT'] = str(port)
    
    try:
        # Run the service
        process = subprocess.Popen(
            [sys.executable, f"{service_path}/app.py"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        print(f"✅ {service_name} started successfully (PID: {process.pid})")
        return process
    
    except Exception as e:
        print(f"❌ Failed to start {service_name}: {e}")
        return None

def check_service_health(service_name, port, timeout=30):
    """Check if a service is healthy"""
    import requests
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"http://localhost:{port}/health", timeout=1)
            if response.status_code == 200:
                print(f"✅ {service_name} is healthy")
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(1)
    
    print(f"❌ {service_name} health check failed")
    return False

def main():
    """Main startup function"""
    print("🚀 Starting Flask Microservice Framework...")
    
    # Service configuration
    services = [
        ('assets-service', 'src/assets-service', 8001),
        ('files-service', 'src/files-service', 8002),
        ('transcode-service', 'src/transcode-service', 8003),
        ('search-service', 'src/search-service', 8004),
        ('api-gateway', 'src/api-gateway', 8000)
    ]
    
    processes = []
    
    try:
        # Start all services
        for service_name, service_path, port in services:
            process = run_service(service_name, service_path, port)
            if process:
                processes.append((service_name, process, port))
            time.sleep(1)  # Small delay between service starts
        
        # Wait for services to be healthy
        print("\n🔍 Checking service health...")
        for service_name, process, port in processes:
            if not check_service_health(service_name, port):
                print(f"⚠️  {service_name} may not be fully ready")
        
        print("\n🎉 All services started!")
        print("\n📋 Service URLs:")
        print("  API Gateway:     http://localhost:8000")
        print("  Assets Service:  http://localhost:8001")
        print("  Files Service:   http://localhost:8002")
        print("  Transcode Service: http://localhost:8003")
        print("  Search Service:  http://localhost:8004")
        print("\n📚 API Documentation:")
        print("  API Gateway:     http://localhost:8000/docs")
        print("  Assets Service:  http://localhost:8001/docs")
        print("  Files Service:   http://localhost:8002/docs")
        print("  Transcode Service: http://localhost:8003/docs")
        print("  Search Service:  http://localhost:8004/docs")
        print("\n⏹️  Press Ctrl+C to stop all services")
        
        # Keep running until interrupted
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Shutting down services...")
        
        # Stop all processes
        for service_name, process, port in processes:
            try:
                process.terminate()
                process.wait(timeout=5)
                print(f"✅ {service_name} stopped")
            except subprocess.TimeoutExpired:
                process.kill()
                print(f"⚠️  {service_name} force killed")
            except Exception as e:
                print(f"❌ Error stopping {service_name}: {e}")
        
        print("👋 All services stopped")

if __name__ == '__main__':
    main() 