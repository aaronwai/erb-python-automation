# auto_setup.py - 自動化環境設置腳本
import subprocess
import sys
import os

def create_virtual_environment(env_name="automation_env"):
    """自動創建虛擬環境"""
    if os.path.exists(env_name):
        print(f"虛擬環境 {env_name} 已存在")
        return False

    print(f"正在創建虛擬環境: {env_name}")
    subprocess.run([sys.executable, "-m", "venv", env_name])
    print("虛擬環境創建成功！")
    return True

def install_packages(env_name, packages):
    """在指定虛擬環境中安裝套件"""
    pip_path = os.path.join(env_name, "Scripts", "pip.exe")
    if not os.path.exists(pip_path):
        pip_path = os.path.join(env_name, "bin", "pip")

    print(f"正在安裝套件: {', '.join(packages)}")
    subprocess.run([pip_path, "install"] + packages)
    print("套件安裝完成！")

if __name__ == "__main__":
    # 定義所需套件
    required_packages = [
        "selenium",
        "pandas",
        "requests",
        "openpyxl",
        "python-dotenv"
    ]

    # 執行自動化設置
    create_virtual_environment()
    install_packages("automation_env", required_packages)