#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Setup script for League Stats project.
Automates the installation and configuration process.
"""

import sys
import subprocess
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required.")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True


def install_dependencies():
    """Install required Python packages."""
    print("\n📦 Installing dependencies...")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
        )
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def setup_config():
    """Set up configuration file."""
    config_example = Path("config.env.example")
    config_file = Path("config.env")

    print("\n⚙️ Setting up configuration...")

    if config_file.exists():
        print("✅ config.env already exists")
        return True

    if not config_example.exists():
        print("❌ config.env.example not found")
        return False

    # Copy example config
    with open(config_example, "r") as src:
        content = src.read()

    with open(config_file, "w") as dst:
        dst.write(content)

    print("✅ Created config.env from template")
    print("⚠️  Please edit config.env and add your RIOT_API_TOKEN")
    return True


def create_directories():
    """Create necessary directories."""
    print("\n📁 Creating directories...")

    directories = ["matches", "logs"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")

    return True


def run_tests():
    """Run test suite to verify installation."""
    print("\n🧪 Running tests...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "tests/", "-v"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print("✅ All tests passed")
            return True
        else:
            print("❌ Some tests failed:")
            print(result.stdout)
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Failed to run tests: {e}")
        return False


def print_next_steps():
    """Print information about next steps."""
    print("\n" + "=" * 60)
    print("🎉 SETUP COMPLETE!")
    print("=" * 60)
    print("\n📋 Next Steps:")
    print("1. Get your Riot API token from: https://developer.riotgames.com/")
    print("2. Edit config.env and add your token:")
    print("   RIOT_API_TOKEN=your_token_here")
    print("3. Fetch some match data:")
    print("   python league.py frowtch blue 5")
    print("4. Analyze the data:")
    print("   python analyze.py --player Frowtch")
    print("5. Create visualizations:")
    print("   python stats_visualization/visualizations/graph_drakes.py")
    print("\n📚 Documentation: README.md")
    print("🐛 Issues: https://github.com/Frowtchie/League-Stats/issues")


def main():
    """Main setup function."""
    print("⚡ League Stats Setup")
    print("=" * 40)

    # Check prerequisites
    if not check_python_version():
        sys.exit(1)

    # Installation steps
    steps = [install_dependencies, setup_config, create_directories, run_tests]

    for step in steps:
        if not step():
            print(f"\n❌ Setup failed at: {step.__name__}")
            sys.exit(1)

    # Success!
    print_next_steps()


if __name__ == "__main__":
    main()
