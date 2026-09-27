from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time

class AutoLogin:
    """自動登入系統類"""

    def __init__(self):
        self.driver = webdriver.Chrome()
        self.wait = WebDriverWait(self.driver, 10)

    def login(self, url, username, password):
        """執行自動登入"""
        try:
            # 訪問登入頁面
            self.driver.get(url)
            print(f"已訪問: {url}")

            # 等待登入表單加載
            self.wait.until(
                EC.presence_of_element_located((By.ID, "login-form"))
            )

            # 輸入用戶名
            username_field = self.driver.find_element(By.ID, "username")
            username_field.clear()
            username_field.send_keys(username)
            print(f"已輸入用戶名: {username}")

            # 輸入密碼
            password_field = self.driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(password)
            print("已輸入密碼")

            # 點擊登入按鈕
            login_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
            )
            login_button.click()
            print("已點擊登入按鈕")

            # 驗證登入成功
            self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "dashboard"))
            )
            print("登入成功！")
            return True

        except TimeoutException:
            print("登入超時，請檢查頁面元素定位")
            return False
        except Exception as e:
            print(f"登入失敗: {str(e)}")
            return False

    def logout(self):
        """執行登出"""
        try:
            logout_link = self.driver.find_element(By.LINK_TEXT, "登出")
            logout_link.click()
            print("已登出")
        except Exception as e:
            print(f"登出失敗: {str(e)}")

    def close(self):
        """關閉瀏覽器"""
        self.driver.quit()
        print("瀏覽器已關閉")

# 使用示例
if __name__ == "__main__":
    auto_login = AutoLogin()

    # 假設的測試網站
    success = auto_login.login(
        url="https://example.com/login",
        username="test_user",
        password="test_password"
    )

    if success:
        time.sleep(5)  # 模擬操作
        auto_login.logout()

    auto_login.close()