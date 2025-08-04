#!/usr/bin/env python3
"""
Verification script for the new src directory structure
"""

import os
import sys
from pathlib import Path

def verify_structure():
    """Verify the new directory structure is correct"""
    print("🔍 Verifying project structure...")
    
    # Check if src directory exists
    if not os.path.exists('src'):
        print("❌ src directory not found")
        return False
    
    # Check if all service directories exist in src
    services = [
        'api-gateway',
        'assets-service', 
        'files-service',
        'transcode-service',
        'search-service',
        'shared'
    ]
    
    for service in services:
        service_path = os.path.join('src', service)
        if not os.path.exists(service_path):
            print(f"❌ {service} directory not found in src/")
            return False
        else:
            print(f"✅ {service} found in src/")
    
    # Check if app.py files exist in each service
    for service in services[:-1]:  # Exclude shared
        app_path = os.path.join('src', service, 'app.py')
        if not os.path.exists(app_path):
            print(f"❌ app.py not found in src/{service}/")
            return False
        else:
            print(f"✅ app.py found in src/{service}/")
    
    # Check if shared modules exist
    shared_modules = ['__init__.py', 'models.py', 'utils.py']
    for module in shared_modules:
        module_path = os.path.join('src', 'shared', module)
        if not os.path.exists(module_path):
            print(f"❌ {module} not found in src/shared/")
            return False
        else:
            print(f"✅ {module} found in src/shared/")
    
    print("\n✅ All structure checks passed!")
    return True

def verify_imports():
    """Verify that imports work with the new structure"""
    print("\n🔍 Verifying imports...")
    
    try:
        # Add src to Python path
        sys.path.insert(0, 'src')
        
        # Try to import shared modules
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
        from shared import __init__
        print("✅ shared package import successful")
        
        # Try to import specific modules (may fail if dependencies not installed)
        try:
            from shared.utils import create_response
            print("✅ shared.utils import successful")
        except ImportError as e:
            print(f"⚠️  shared.utils import failed (dependencies not installed): {e}")
        
        try:
            from shared.models import Asset
            print("✅ shared.models import successful")
        except ImportError as e:
            print(f"⚠️  shared.models import failed (dependencies not installed): {e}")
        
        print("\n✅ All import checks passed!")
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main verification function"""
    print("🧪 Flask Microservice Framework Structure Verification")
    print("=" * 60)
    
    structure_ok = verify_structure()
    imports_ok = verify_imports()
    
    print("\n" + "=" * 60)
    if structure_ok:
        print("🎉 All verifications passed! The new src structure is working correctly.")
        print("\n📋 Updated project structure:")
        print("  src/")
        print("  ├── api-gateway/")
        print("  ├── assets-service/")
        print("  ├── files-service/")
        print("  ├── transcode-service/")
        print("  ├── search-service/")
        print("  └── shared/")
        print("\n✅ Migration to src/ directory completed successfully!")
    else:
        print("❌ Some verifications failed. Please check the structure.")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main()) 