from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

class DynamicContentScraper:
    """動態內容抓取類"""

    def __init__(self):
        self.driver = webdriver.Chrome()

    def scrape_infinite_scroll(self, url, scroll_pause=2, max_scrolls=10):
        """
        抓取無限滾動頁面

        Args:
            url: 目標網址
            scroll_pause: 每次滾動後等待時間（秒）
            max_scrolls: 最大滾動次數
        """
        self.driver.get(url)

        last_height = self.driver.execute_script(
            "return document.body.scrollHeight"
        )

        scroll_count = 0
        while scroll_count < max_scrolls:
            # 滾動到頁面底部
            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);"
            )

            # 等待新內容加載
            time.sleep(scroll_pause)

            # 檢查是否已到達底部
            new_height = self.driver.execute_script(
                "return document.body.scrollHeight"
            )

            if new_height == last_height:
                print("已到達頁面底部")
                break

            last_height = new_height
            scroll_count += 1
            print(f"已完成第 {scroll_count} 次滾動")

        # 抓取所有已加載的內容
        items = self.driver.find_elements(By.CSS_SELECTOR, ".content-item")
        print(f"總共抓取 {len(items)} 個項目")

        return items

    def scrape_lazy_load_images(self):
        """抓取懶加載圖片"""
        images = self.driver.find_elements(By.CSS_SELECTOR, "img[data-src]")

        for img in images:
            # 滾動到圖片位置觸發加載
            self.driver.execute_script(
                "arguments[0].scrollIntoView(true);",
                img
            )
            time.sleep(0.5)

            # 獲取實際圖片 URL
            actual_src = img.get_attribute("src") or img.get_attribute("data-src")
            print(f"圖片 URL: {actual_src}")

    def scrape_ajax_content(self, trigger_selector, content_selector):
        """
        抓取 AJAX 加載的內容

        Args:
            trigger_selector: 觸發加載的元素選擇器
            content_selector: 內容元素選擇器
        """
        all_content = []

        while True:
            # 抓取當前內容
            current_items = self.driver.find_elements(
                By.CSS_SELECTOR, content_selector
            )
            all_content.extend(current_items)

            # 查找加載更多按鈕
            try:
                load_more = self.driver.find_element(
                    By.CSS_SELECTOR, trigger_selector
                )

                if not load_more.is_displayed():
                    break

                # 點擊加載更多
                self.driver.execute_script("arguments[0].click();", load_more)
                time.sleep(2)  # 等待 AJAX 請求完成

            except Exception:
                print("沒有更多內容可加載")
                break

        return all_content

# 使用示例
if __name__ == "__main__":
    scraper = DynamicContentScraper()

    # 抓取無限滾動頁面
    items = scraper.scrape_infinite_scroll(
        url="https://example.com/infinite-scroll",
        scroll_pause=2,
        max_scrolls=5
    )

    scraper.driver.quit()