# setup.py
import os
import sys
from pathlib import Path
from setuptools import setup, find_packages
from setuptools.command.install import install
from setuptools.command.develop import develop

def create_jupyter_config():
    """Create Jupyter configuration file in current virtual environment"""

    # Check virtual environment path
    venv_path = Path(sys.prefix)

    # Create jupyter config directory inside virtual environment
    jupyter_config_dir = venv_path / "etc" / "jupyter"
    jupyter_config_dir.mkdir(parents=True, exist_ok=True)

    # Create jupyter_server_config.py
    config_file = jupyter_config_dir / "jupyter_server_config.py"

    config_content = '''# DarkPyonix Auto-Generated Configuration
# This file was automatically generated during DarkPyonix installation.

# Activate Sticky Kernel Manager
c.ServerApp.kernel_manager_class = 'DarkPyonix_km.manager.StickyMappingKernelManager'
c.ServerApp.session_manager_class = 'DarkPyonix_km.manager.StickySessionManager'

# Basic settings
c.ServerApp.ip = '127.0.0.1'
c.ServerApp.open_browser = False
c.ServerApp.allow_root = True

# Logging level (for development)
# c.Application.log_level = 'DEBUG'

print("[DarkPyonix] Sticky Kernel Manager activated!")
print("[DarkPyonix] Notebooks with same file path will share kernels.")
'''

    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(config_content)

    print(f"[OK] Jupyter config file created: {config_file}")

    # Also create environment variable setup script
    env_script = venv_path / "bin" / "darkpyonix-env.sh"
    if os.name == "nt":  # Windows
        env_script = venv_path / "Scripts" / "darkpyonix-env.bat"

    if os.name == "nt":
        env_content = f'''@echo off
REM DarkPyonix Environment Setup
set JUPYTER_CONFIG_DIR={jupyter_config_dir}
set STICKYKM_NAMESPACE=default-{venv_path.name}
echo DarkPyonix environment activated!
'''
    else:
        env_content = f'''#!/bin/bash
# DarkPyonix Environment Setup
export JUPYTER_CONFIG_DIR="{jupyter_config_dir}"
export STICKYKM_NAMESPACE="default-{venv_path.name}"
echo "DarkPyonix environment activated!"
'''

    with open(env_script, 'w') as f:
        f.write(env_content)

    if not os.name == "nt":
        os.chmod(env_script, 0o755)

    print(f"[OK] Environment script created: {env_script}")

    # Modify virtual environment activate script
    try:
        modify_activate_script(venv_path, jupyter_config_dir)
    except Exception as e:
        print(f"[WARNING] Failed to modify activate script (manual setup required): {e}")

def modify_activate_script(venv_path, jupyter_config_dir):
    """Add automatic configuration to virtual environment activate script"""

    if os.name == "nt":
        activate_script = venv_path / "Scripts" / "activate.bat"
        env_line = f'set JUPYTER_CONFIG_DIR={jupyter_config_dir}'
    else:
        activate_script = venv_path / "bin" / "activate"
        env_line = f'export JUPYTER_CONFIG_DIR="{jupyter_config_dir}"'

    if not activate_script.exists():
        return

    # Read existing content
    with open(activate_script, 'r') as f:
        content = f.read()

    # Check if DarkPyonix configuration already exists
    if "DarkPyonix" in content:
        return

    # Add configuration to end of script
    darkpyonix_config = f'''

# DarkPyonix Auto Configuration
{env_line}
export STICKYKM_NAMESPACE="default-{venv_path.name}"
'''

    with open(activate_script, 'a') as f:
        f.write(darkpyonix_config)

    print(f"[OK] Activate script modification complete: {activate_script}")

class PostInstallCommand(install):
    """Execute automatic configuration after installation"""
    def run(self):
        install.run(self)
        print("\n" + "="*50)
        print("DarkPyonix Installation Complete!")
        print("="*50)
        create_jupyter_config()
        print("\n[SUCCESS] Setup complete! Now run jupyter server:")
        print(f"   jupyter server --port=8888")
        print("\nUsage:")
        print("   - Same file opened multiple times will reuse the same kernel")
        print("   - Multiple users can share kernels for the same file")
        print("="*50 + "\n")

class PostDevelopCommand(develop):
    """Execute automatic configuration after development installation"""
    def run(self):
        develop.run(self)
        print("\n" + "="*50)
        print("DarkPyonix Development Mode Installation Complete!")
        print("="*50)
        create_jupyter_config()
        print("="*50 + "\n")

setup(
    name="darkpyonix",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Sticky Kernel Manager for Jupyter - File-based kernel reuse",
    long_description=open("README.md", encoding='utf-8').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/DarkPyonix",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Framework :: Jupyter",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=[
        "jupyter-server>=2.0.0",  # Core server (required)
        "ipykernel>=6.0.0",       # Kernel execution (required)
        "notebook-shim>=0.2.0",   # Compatibility (required)
        "jupyter-client>=8.0.0",  # Kernel communication (required)
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "darkpyonix-config=DarkPyonix_km.config:main",
        ],
    },
    cmdclass={
        'install': PostInstallCommand,
        'develop': PostDevelopCommand,
    },
    include_package_data=True,
    zip_safe=False,
)