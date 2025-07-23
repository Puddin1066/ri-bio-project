#!/usr/bin/env python3
"""
Launch script for the AI Data Assistant Chat UI
This script handles dependency installation and server startup
"""

import subprocess
import sys
import os
from pathlib import Path

def install_packages():
    """Install required packages"""
    packages = [
        'flask==3.0.0',
        'flask-cors==4.0.0', 
        'openai==1.40.0',
        'requests==2.31.0',
        'python-dotenv==1.0.0',
        'beautifulsoup4==4.12.2',
        'pandas==2.0.3',
        'lxml==4.9.3'
    ]
    
    print("Installing required packages...")
    for package in packages:
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', 
                '--break-system-packages', package
            ])
            print(f"✓ Installed {package}")
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to install {package}: {e}")
            return False
    return True

def check_env_file():
    """Check if .env file exists and has required variables"""
    env_file = Path('.env')
    if not env_file.exists():
        print("\n⚠️  No .env file found!")
        print("Creating .env file from example...")
        
        # Copy from .env.example
        example_file = Path('.env.example')
        if example_file.exists():
            env_file.write_text(example_file.read_text())
            print("✓ Created .env file")
        else:
            # Create basic .env file
            env_content = """# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Flask Configuration  
FLASK_ENV=development
FLASK_DEBUG=True
"""
            env_file.write_text(env_content)
            print("✓ Created basic .env file")
        
        print("\n🔑 Please edit the .env file and add your OpenAI API key!")
        print("You can get one from: https://platform.openai.com/api-keys")
        print("\nAfter adding your API key, run this script again.")
        return False
    
    # Check if API key is set
    env_content = env_file.read_text()
    if 'your_openai_api_key_here' in env_content:
        print("\n🔑 Please edit the .env file and add your real OpenAI API key!")
        print("Current .env file still contains placeholder text.")
        return False
    
    return True

def start_server():
    """Start the Flask development server"""
    print("\n🚀 Starting AI Data Assistant server...")
    print("Server will be available at: http://localhost:5000")
    print("Press Ctrl+C to stop the server\n")
    
    # Import and run the Flask app
    try:
        from backend.app import app
        app.run(debug=True, host='0.0.0.0', port=5000)
    except ImportError:
        # Fallback - run the app directly
        backend_path = Path('backend/app.py')
        if backend_path.exists():
            subprocess.run([sys.executable, str(backend_path)])
        else:
            print("❌ Could not find backend/app.py")
            return False
    
    return True

def main():
    """Main launch function"""
    print("🤖 AI Data Assistant - EDGAR & StreetEasy Chat UI")
    print("=" * 50)
    
    # Change to the chat_ui directory if we're not already there
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Install packages
    if not install_packages():
        print("❌ Failed to install required packages")
        return False
    
    # Check environment configuration
    if not check_env_file():
        return False
    
    # Start the server
    return start_server()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped. Thanks for using AI Data Assistant!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)