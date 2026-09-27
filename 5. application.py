from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

class ElementLocator:
    """元素定位最佳實踐類"""

    def __init__(self, driver):
        self.driver = driver

    def safe_find_element(self, by, value, timeout=10):
        """安全的元素查找，帶異常處理"""
        try:
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC

            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except Exception as e:
            print(f"元素查找失敗: {value}")
            print(f"錯誤信息: {str(e)}")
            return None

    def find_with_fallback(self, *strategies):
        """
        多策略備援定位
        當首選策略失效時，依次嘗試其他策略
        """
        for by, value in strategies:
            try:
                element = self.driver.find_element(by, value)
                print(f"定位成功: {by} = {value}")
                return element
            except NoSuchElementException:
                continue

        raise NoSuchElementException("所有定位策略均失敗")

# 使用示例
driver = webdriver.Chrome()
locator = ElementLocator(driver)

# 備援定位策略示例
element = locator.find_with_fallback(
    (By.ID, "submit-btn"),           # 首選：ID
    (By.CSS_SELECTOR, "button[type='submit']"),  # 備選：CSS
    (By.XPATH, "//button[contains(text(), '提交')]")  # 最後：XPath
)