"""
Installation and Setup Script
Helps with initial setup and dependency verification
"""

import subprocess
import sys
import os


def check_python_version():
    """Check if Python version is compatible"""
    print("Checking Python version...")
    version = sys.version_info
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8+ required. Current version: {version.major}.{version.minor}")
        return False
    
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    return True


def check_ffmpeg():
    """Check if FFmpeg is installed"""
    print("\nChecking FFmpeg...")
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✓ FFmpeg is installed")
            return True
    except FileNotFoundError:
        pass
    
    print("❌ FFmpeg not found")
    print("\nPlease install FFmpeg:")
    print("  Windows: choco install ffmpeg")
    print("  Or download from: https://ffmpeg.org/download.html")
    return False


def install_dependencies():
    """Install Python dependencies"""
    print("\nInstalling Python dependencies...")
    print("This may take several minutes...\n")
    
    try:
        # Upgrade pip first
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'],
            check=True
        )
        
        # Install requirements
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'],
            check=True
        )
        
        print("\n✓ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error installing dependencies: {e}")
        return False


def check_torch_cuda():
    """Check if PyTorch has CUDA support"""
    print("\nChecking GPU support...")
    try:
        import torch
        if torch.cuda.is_available():
            print(f"✓ CUDA available - GPU: {torch.cuda.get_device_name(0)}")
            print(f"  CUDA version: {torch.version.cuda}")
        else:
            print("ℹ CUDA not available - will use CPU")
            print("  For GPU acceleration, install PyTorch with CUDA:")
            print("  https://pytorch.org/get-started/locally/")
    except ImportError:
        print("⚠ PyTorch not installed yet")


def create_directories():
    """Create necessary directories"""
    print("\nCreating directories...")
    
    dirs = ['recordings', 'transcriptions', 'models']
    for directory in dirs:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ {directory}/")


def main():
    """Main setup function"""
    print("=" * 60)
    print("Local Speech-to-Text - Setup")
    print("=" * 60 + "\n")
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check FFmpeg
    ffmpeg_ok = check_ffmpeg()
    
    # Install dependencies
    print("\n" + "=" * 60)
    response = input("\nInstall/Update Python dependencies? (y/n): ")
    if response.lower() == 'y':
        if not install_dependencies():
            sys.exit(1)
        
        # Check CUDA
        check_torch_cuda()
    
    # Create directories
    create_directories()
    
    # Final message
    print("\n" + "=" * 60)
    print("SETUP COMPLETE")
    print("=" * 60)
    
    if not ffmpeg_ok:
        print("\n⚠ Warning: FFmpeg is not installed.")
        print("  Some features may not work properly.")
    
    print("\nYou can now run the application:")
    print("  GUI: python main.py")
    print("  CLI: python cli_app.py --help")
    print("\nOr use the quick launcher:")
    print("  run_gui.bat")
    print()


if __name__ == "__main__":
    main()
