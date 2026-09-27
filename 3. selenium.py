from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

# 基本瀏覽器啟動
def basic_browser_launch():
    """啟動瀏覽器並訪問網站"""

    # 創建 Chrome 瀏覽器實例
    driver = webdriver.Chrome()

    # 訪問網站
    driver.get("https://www.google.com")

    # 獲取頁面標題
    print(f"頁面標題: {driver.title}")

    # 獲取當前網址
    print(f"當前網址: {driver.current_url}")

    # 等待 3 秒
    time.sleep(3)

    # 關閉瀏覽器
    driver.quit()

# 進階配置選項
def advanced_browser_setup():
    """使用進階選項配置瀏覽器"""

    # 創建 Chrome 選項
    chrome_options = Options()

    # 無頭模式（不顯示瀏覽器視窗）
    # chrome_options.add_argument("--headless")

    # 禁用 GPU 加速
    chrome_options.add_argument("--disable-gpu")

    # 設置視窗大小
    chrome_options.add_argument("--window-size=1920,1080")

    # 禁用通知彈窗
    chrome_options.add_argument("--disable-notifications")

    # 設置 User-Agent
    chrome_options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )

    # 創建瀏覽器實例
    driver = webdriver.Chrome(options=chrome_options)

    # 設置隱式等待
    driver.implicitly_wait(10)

    return driver

# 執行
if __name__ == "__main__":
    basic_browser_launch()