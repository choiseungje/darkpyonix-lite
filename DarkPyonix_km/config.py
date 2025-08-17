# DarkPyonix_km/config.py
"""DarkPyonix Configuration Management Utility"""

import os
import sys
import argparse
from pathlib import Path

def get_venv_jupyter_config_dir():
    """Get Jupyter config directory in current virtual environment"""
    venv_path = Path(sys.prefix)
    return venv_path / "etc" / "jupyter"

def create_config():
    """Create or recreate Jupyter server configuration file"""
    config_dir = get_venv_jupyter_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)

    config_file = config_dir / "jupyter_server_config.py"

    config_content = '''# DarkPyonix Configuration
# Sticky Kernel Manager for file-based kernel reuse

c.ServerApp.kernel_manager_class = 'DarkPyonix_km.manager.StickyMappingKernelManager'
c.ServerApp.session_manager_class = 'DarkPyonix_km.manager.StickySessionManager'

# Basic server settings
c.ServerApp.ip = '127.0.0.1'
c.ServerApp.open_browser = False
c.ServerApp.allow_root = True

# Optional: Enable debug logging
# import logging
# logging.getLogger("StickyKM").setLevel(logging.DEBUG)
# logging.getLogger("StickySM").setLevel(logging.DEBUG)

print("🚀 [DarkPyonix] Sticky Kernel Manager activated!")
print("📝 [DarkPyonix] Same file path → Same kernel reuse")
'''

    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(config_content)

    return config_file

def check_installation():
    """Check DarkPyonix installation status and configuration"""
    print("🔍 DarkPyonix Installation Check")
    print("=" * 40)

    issues = []

    # 1. Check package import
    try:
        from DarkPyonix_km.manager import StickyMappingKernelManager, StickySessionManager
        print("✅ DarkPyonix package: OK")
    except ImportError as e:
        print(f"❌ DarkPyonix package: Failed - {e}")
        issues.append("Package import failed")

    # 2. Check Jupyter Server installation
    try:
        import jupyter_server
        print(f"✅ Jupyter Server: OK (v{jupyter_server.__version__})")
    except ImportError as e:
        print(f"❌ Jupyter Server: Failed - {e}")
        issues.append("Jupyter Server not installed")

    # 3. Check config file
    config_dir = get_venv_jupyter_config_dir()
    config_file = config_dir / "jupyter_server_config.py"

    if config_file.exists():
        print(f"✅ Config file: {config_file}")

        # Check if config contains DarkPyonix settings
        try:
            with open(config_file, 'r') as f:
                content = f.read()
                if 'StickyMappingKernelManager' in content:
                    print("✅ DarkPyonix settings: Found in config")
                else:
                    print("⚠️  DarkPyonix settings: Missing from config")
                    issues.append("Config file exists but missing DarkPyonix settings")
        except Exception as e:
            print(f"⚠️  Config file: Cannot read - {e}")
            issues.append("Config file unreadable")
    else:
        print(f"❌ Config file: Missing - {config_file}")
        issues.append("Config file missing")

    # 4. Check environment variables
    jupyter_config_env = os.environ.get('JUPYTER_CONFIG_DIR')
    if jupyter_config_env:
        print(f"✅ JUPYTER_CONFIG_DIR: {jupyter_config_env}")
        if str(config_dir) != jupyter_config_env:
            print("⚠️  Warning: JUPYTER_CONFIG_DIR points to different location")
    else:
        print("ℹ️  JUPYTER_CONFIG_DIR: Not set (using default)")

    # 5. Check virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print(f"✅ Virtual environment: {sys.prefix}")
    else:
        print("⚠️  Virtual environment: Not detected (system Python)")
        issues.append("Not in virtual environment")

    print("=" * 40)

    if issues:
        print("⚠️  Issues found:")
        for issue in issues:
            print(f"   - {issue}")
        print("\n🔧 Run 'darkpyonix-config create' to fix configuration issues")
        return False
    else:
        print("🎉 All checks passed! DarkPyonix is ready to use.")
        return True

def show_usage():
    """Show comprehensive usage guide"""
    print("""
🚀 DarkPyonix Usage Guide

📦 INSTALLATION
   pip install git+https://github.com/choiseungje/darkpyonix-lite.git

🖥️  STARTING JUPYTER SERVER
   jupyter server --port=8888
   
   # Access in browser: http://localhost:8888

🔧 CONFIGURATION COMMANDS
   darkpyonix-config check    # Check installation status
   darkpyonix-config create   # Create/recreate config file
   darkpyonix-config usage    # Show this guide
   darkpyonix-config clean    # Remove configuration

🌐 ENVIRONMENT VARIABLES
   # Optional: Project isolation
   export STICKYKM_NAMESPACE="my-project-2025"
   
   # Optional: Custom config location
   export JUPYTER_CONFIG_DIR="/path/to/config"
""")

def clean_config():
    """Remove DarkPyonix configuration"""
    config_dir = get_venv_jupyter_config_dir()
    config_file = config_dir / "jupyter_server_config.py"

    if config_file.exists():
        # Check if file contains only DarkPyonix config
        try:
            with open(config_file, 'r') as f:
                content = f.read()

            if 'DarkPyonix' in content and content.count('\n') < 20:
                # Looks like our auto-generated config, safe to remove
                config_file.unlink()
                print(f"✅ Removed DarkPyonix config: {config_file}")
            else:
                # File contains other settings, just remove our parts
                lines = content.split('\n')
                new_lines = []
                skip_block = False

                for line in lines:
                    if 'DarkPyonix' in line or 'StickyMappingKernelManager' in line or 'StickySessionManager' in line:
                        skip_block = True
                        continue
                    if skip_block and line.strip() == '':
                        continue
                    if skip_block and not line.startswith('c.') and not line.startswith('#') and not line.startswith('print'):
                        skip_block = False
                    if not skip_block:
                        new_lines.append(line)

                if new_lines and any(line.strip() for line in new_lines):
                    with open(config_file, 'w') as f:
                        f.write('\n'.join(new_lines))
                    print(f"✅ Removed DarkPyonix settings from: {config_file}")
                else:
                    config_file.unlink()
                    print(f"✅ Removed empty config file: {config_file}")

        except Exception as e:
            print(f"⚠️  Could not clean config file: {e}")
            print("   You may need to manually edit:", config_file)
    else:
        print(f"ℹ️  No config file found: {config_file}")

    # Remove empty directory if possible
    try:
        if config_dir.exists() and not any(config_dir.iterdir()):
            config_dir.rmdir()
            print(f"✅ Removed empty config directory: {config_dir}")
    except OSError:
        pass  # Directory not empty or other issue

def main():
    """Main command line interface"""
    parser = argparse.ArgumentParser(
        description='DarkPyonix Configuration Manager',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  darkpyonix-config check           # Verify installation
  darkpyonix-config create          # Setup configuration
  darkpyonix-config usage           # Show usage guide
  darkpyonix-config clean           # Remove configuration
        """
    )
    parser.add_argument('command', nargs='?',
                        choices=['check', 'create', 'usage', 'clean'],
                        default='check',
                        help='Command to execute (default: check)')

    args = parser.parse_args()

    if args.command == 'check':
        success = check_installation()
        sys.exit(0 if success else 1)
    elif args.command == 'create':
        config_file = create_config()
        print(f"✅ Configuration file created: {config_file}")
        print("🚀 Ready! Start with: jupyter server --port=8888")
    elif args.command == 'usage':
        show_usage()
    elif args.command == 'clean':
        clean_config()
        print("🧹 Cleanup complete!")

if __name__ == "__main__":
    main()