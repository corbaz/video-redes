#!/usr/bin/env python3
"""
Startup script for Instagram Video Downloader
"""

import subprocess
import sys
import os
import time


def check_requirements():
    """Check if required packages are installed"""
    try:
        import requests
        print("✅ requests is installed")
    except ImportError:
        print("❌ requests not found. Installing...")
        subprocess.check_call(
            [sys.executable, '-m', 'pip', 'install', 'requests'])

    try:
        import moviepy
        print("✅ moviepy is installed (for precise audio detection)")
    except ImportError:
        print("❌ moviepy not found. Installing...")
        subprocess.check_call(
            [sys.executable, '-m', 'pip', 'install', 'moviepy'])

    try:
        result = subprocess.run(['yt-dlp', '--version'],
                                capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ yt-dlp is installed: {result.stdout.strip()}")
        else:
            raise FileNotFoundError
    except FileNotFoundError:
        print("❌ yt-dlp not found. Installing...")
        subprocess.check_call(
            [sys.executable, '-m', 'pip', 'install', 'yt-dlp'])


def main():
    print("🚀 Instagram Video Downloader - Starting...")
    print("=" * 50)

    # Check requirements
    print("🔍 Checking requirements...")
    check_requirements()

    print("\n📋 Available options:")
    print("1. Start server (recommended)")
    print("2. Run tests")
    print("3. Install requirements only")

    choice = input("\nSelect option (1-3, default=1): ").strip() or "1"

    if choice == "1":
        print("\n🚀 Starting Instagram downloader server...")
        port = input("Enter port (default=8000): ").strip() or "8000"
        try:
            port = int(port)
            print(f"\n🌐 Starting server on port {port}...")
            print(f"📱 Open in browser: http://localhost:{port}")
            print("🛑 Press Ctrl+C to stop")
            print("=" * 50)
            subprocess.run([sys.executable, 'server.py', str(port)])
        except ValueError:
            print("❌ Invalid port number")
        except KeyboardInterrupt:
            print("\n🛑 Server stopped")

    elif choice == "2":
        print("\n🧪 Running tests...")
        subprocess.run([sys.executable, 'test.py'])

    elif choice == "3":
        print("\n✅ Requirements installed successfully!")

    else:
        print("❌ Invalid option")


if __name__ == "__main__":
    main()
