# auto_setup.py - Auto venv setup + generate bat + ps1 launcher
import subprocess
import sys
import os
import platform

def create_virtual_environment(env_name="automation_env"):
    """Create python virtual environment"""
    if os.path.exists(env_name):
        print(f"Virtual environment {env_name} already exists")
        return False
    print(f"Creating virtual environment: {env_name}")
    subprocess.run([sys.executable, "-m", "venv", env_name])
    print("Virtual environment created successfully!")
    return True

def install_packages(env_name, packages):
    """Install packages inside venv"""
    pip_path = os.path.join(env_name, "Scripts", "pip.exe")
    if not os.path.exists(pip_path):
        pip_path = os.path.join(env_name, "bin", "pip")
    print(f"Installing packages: {', '.join(packages)}")
    subprocess.run([pip_path, "install"] + packages)
    print("Package installation finished!")

def generate_bat_launcher(env_name="automation_env", bat_filename="start_env.bat"):
    bat_content = f'''@echo off
chcp 65001 >nul
echo ======================================
echo Activating virtual environment [{env_name}]
echo ======================================
call {env_name}\\Scripts\\activate.bat
echo.
echo Venv activated, (automation_env) prompt ready.
echo Run your python scripts here.
echo.
cmd /k
'''
    with open(bat_filename, "w", encoding="utf-8") as f:
        f.write(bat_content)
    print(f"\n✅ CMD Launcher created: {bat_filename}")

def generate_ps1_launcher(env_name="automation_env", ps1_filename="start_env.ps1"):
    ps1_content = f'''<#
PowerShell launcher for {env_name} venv
Run with: .\\start_env.ps1
#>
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Activating virtual environment [{env_name}]" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
.\\{env_name}\\Scripts\\Activate.ps1
Write-Host ""
Write-Host "✅ Venv activated, (automation_env) prompt ready." -ForegroundColor Green
Write-Host "Run your python scripts in this PowerShell session." -ForegroundColor Green
'''
    with open(ps1_filename, "w", encoding="utf-8") as f:
        f.write(ps1_content)
    print(f"✅ PowerShell Launcher created: {ps1_filename}")

if __name__ == "__main__":
    required_packages = [
        "selenium",
        "pandas",
        "requests",
        "openpyxl",
        "python-dotenv"
    ]
    env_name = "automation_env"

    create_virtual_environment(env_name)
    install_packages(env_name, required_packages)
    generate_bat_launcher(env_name)
    generate_ps1_launcher(env_name)

    print("\n==== ALL DONE ====")
    print("👉 For CMD: double click start_env.bat")
    print("👉 For PowerShell, run: .\\start_env.ps1")