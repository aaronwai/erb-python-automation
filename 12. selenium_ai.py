from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException
from openai import OpenAI
import os
import time
from dotenv import load_dotenv
import re

# Load env
load_dotenv()

class AIAssistedAutomation:
    """AI 輔助自動化類"""
    def __init__(self):
        self.driver = webdriver.Chrome()
        self.wait = WebDriverWait(self.driver, 10)
        # OpenAI client (v1+ syntax)
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.ai_client = OpenAI(api_key=self.openai_api_key) if self.openai_api_key else None

    def ai_find_element(self, description):
        """
        使用 AI 輔助定位元素
        當傳統定位失敗時，將頁面結構發送給 AI，獲取建議的定位策略
        """
        if not self.ai_client:
            print("OpenAI API key not set, skip AI locate")
            return None
        try:
            page_source = self.driver.page_source
            prompt = f"""
Based on the HTML snippet below, output ONLY a valid CSS selector for element: "{description}".
No explanation, just the selector.
HTML snippet:
{page_source[:4000]}
"""
            response = self.ai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=80
            )
            raw_selector = response.choices[0].message.content.strip()
            # Clean AI output, extract selector only
            cleaned_selector = re.search(r"([#.\[\w][\w\-\[\]\=\"':,.> ~+]*)", raw_selector)
            if cleaned_selector:
                suggested_selector = cleaned_selector.group(1).strip()
            else:
                suggested_selector = raw_selector

            element = self.driver.find_element(By.CSS_SELECTOR, suggested_selector)
            print(f"AI 定位成功: {suggested_selector}")
            return element
        except Exception as e:
            print(f"AI 輔助定位失敗: {str(e)}")
            return None

    def smart_wait(self, condition_func, timeout=30):
        """智能等待 - 根據網絡狀況動態調整等待時間"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                if condition_func():
                    return True
            except Exception:
                pass
            elapsed = time.time() - start_time
            if elapsed < 5:
                time.sleep(0.5)
            elif elapsed < 15:
                time.sleep(1)
            else:
                time.sleep(2)
        raise TimeoutException("智能等待超時")

    def self_healing_locator(self, primary_selector, backup_selectors, target_desc=""):
        """
        自修復定位器 - 當首選定位失敗時自動嘗試備選方案
        :param target_desc: element description passed to AI fallback
        """
        selectors = [primary_selector] + backup_selectors
        for selector in selectors:
            try:
                by_strategy, value = self._parse_selector(selector)
                element = self.driver.find_element(by_strategy, value)
                print(f"定位成功: {selector}")
                return element
            except WebDriverException:
                continue
        # All selectors failed, trigger AI healing
        print("所有定位策略失敗，嘗試 AI 輔助...")
        return self.ai_find_element(target_desc)

    def _parse_selector(self, selector):
        """解析定位字符串為 By 策略"""
        if selector.startswith("//"):
            return By.XPATH, selector
        elif selector.startswith("#"):
            return By.ID, selector[1:]
        else:
            # .class / [data-attr] / plain tag → use CSS_SELECTOR
            return By.CSS_SELECTOR, selector

# 使用示例
if __name__ == "__main__":
    ai_auto = AIAssistedAutomation()
    try:
        # 使用自修復定位器，傳入元素描述給AI
        element = ai_auto.self_healing_locator(
            primary_selector="#submit-button",
            backup_selectors=[
                ".btn-submit",
                "//button[contains(text(), '提交')]",
                "[data-testid='submit']"
            ],
            target_desc="提交按鈕"
        )
        if element:
            element.click()
    finally:
        ai_auto.driver.quit()