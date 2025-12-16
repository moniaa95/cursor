#!/usr/bin/env python3
"""
Helper script to check if all dependencies and API keys are configured correctly.

Usage:
    python check_setup.py
"""

import sys
import os

def check_dependencies():
    """Check if all required packages are installed."""
    print("🔍 Checking Python dependencies...")
    
    required = [
        "openai",
        "pandas",
        "numpy",
        "requests",
        "tqdm",
        "bs4",
        "sklearn",
        "scipy",
        "hdbscan",
    ]
    
    missing = []
    for package in required:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} - NOT INSTALLED")
            missing.append(package)
    
    if missing:
        print("\n⚠️ Missing packages. Install with:")
        print(f"  pip install {' '.join(missing)}")
        return False
    
    print("\n✅ All dependencies installed!\n")
    return True


def check_api_keys():
    """Check if API keys are set in environment."""
    print("🔑 Checking API keys...")
    
    keys = {
        "OPENROUTER_API_KEY": "OpenRouter (REQUIRED)",
        "SERPDATA_KEY": "SerpData (REQUIRED)",
        "JINA_API_KEY": "Jina AI (OPTIONAL)",
    }
    
    missing_required = []
    
    for key, description in keys.items():
        value = os.getenv(key)
        if value:
            masked = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
            print(f"  ✅ {key}: {masked}")
        else:
            print(f"  ❌ {key}: NOT SET ({description})")
            if "REQUIRED" in description:
                missing_required.append(key)
    
    if missing_required:
        print("\n⚠️ Missing required API keys. Set them with:")
        for key in missing_required:
            print(f"  export {key}='your-key-here'")
        return False
    
    print("\n✅ All required API keys set!\n")
    return True


def check_python_version():
    """Check Python version."""
    print("🐍 Checking Python version...")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"  ❌ Python {version.major}.{version.minor} - UNSUPPORTED")
        print("  ⚠️ Python 3.8+ required")
        return False
    
    print(f"  ✅ Python {version.major}.{version.minor}.{version.micro}")
    print()
    return True


def test_api_connectivity():
    """Test if APIs are reachable."""
    print("🌐 Testing API connectivity...")
    
    # Test OpenRouter
    try:
        import requests
        key = os.getenv("OPENROUTER_API_KEY")
        if key:
            headers = {"Authorization": f"Bearer {key}"}
            r = requests.get("https://openrouter.ai/api/v1/models", headers=headers, timeout=10)
            if r.status_code == 200:
                print("  ✅ OpenRouter API: Connected")
            else:
                print(f"  ⚠️ OpenRouter API: Status {r.status_code}")
        else:
            print("  ⏭️ OpenRouter API: Skipped (no key)")
    except Exception as e:
        print(f"  ❌ OpenRouter API: Error - {e}")
    
    # Test SerpData
    try:
        key = os.getenv("SERPDATA_KEY")
        if key:
            headers = {"Authorization": f"Bearer {key}"}
            # Small test query
            r = requests.get(
                "https://api.serpdata.io/v1/search",
                headers=headers,
                params={"keyword": "test", "hl": "pl"},
                timeout=10
            )
            if r.status_code in [200, 400]:  # 400 is OK (invalid query, but API works)
                print("  ✅ SerpData API: Connected")
            else:
                print(f"  ⚠️ SerpData API: Status {r.status_code}")
        else:
            print("  ⏭️ SerpData API: Skipped (no key)")
    except Exception as e:
        print(f"  ❌ SerpData API: Error - {e}")
    
    # Test Jina (optional)
    try:
        key = os.getenv("JINA_API_KEY")
        if key:
            headers = {"Authorization": f"Bearer {key}"}
            r = requests.get("https://api.jina.ai/v1/models", headers=headers, timeout=10)
            if r.status_code == 200:
                print("  ✅ Jina AI API: Connected")
            else:
                print(f"  ⚠️ Jina AI API: Status {r.status_code}")
        else:
            print("  ⏭️ Jina AI API: Skipped (no key, OPTIONAL)")
    except Exception as e:
        print(f"  ⚠️ Jina AI API: Error - {e} (OPTIONAL)")
    
    print()


def main():
    print("="*70)
    print("🏥 AESTHETIC MEDICINE SEARCH ENGINE - SETUP CHECK")
    print("="*70)
    print()
    
    all_ok = True
    
    # Check Python version
    if not check_python_version():
        all_ok = False
    
    # Check dependencies
    if not check_dependencies():
        all_ok = False
    
    # Check API keys
    if not check_api_keys():
        all_ok = False
    
    # Test connectivity
    if all_ok:
        test_api_connectivity()
    
    # Final summary
    print("="*70)
    if all_ok:
        print("✅ SETUP COMPLETE! You're ready to run the pipeline.")
        print("\nNext steps:")
        print("  1. Open aesthetic_medicine_search_engine.ipynb in Google Colab")
        print("  2. Or run: python standalone_version.py --output-dir ./output")
    else:
        print("❌ SETUP INCOMPLETE. Fix the issues above and run again.")
        sys.exit(1)
    print("="*70)


if __name__ == "__main__":
    main()
