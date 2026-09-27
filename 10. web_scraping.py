from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import json
import csv
from dataclasses import dataclass
from typing import List

@dataclass
class Product:
    """產品數據類"""
    name: str
    price: float
    rating: str
    review_count: int
    url: str
    image_url: str

class EcommerceScraper:
    """電商數據抓取類"""

    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")  # 無頭模式
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 15)
        self.products: List[Product] = []

    def scrape_products(self, search_url, max_pages=3):
        """抓取產品數據"""
        self.driver.get(search_url)

        for page in range(1, max_pages + 1):
            print(f"\n正在抓取第 {page} 頁...")

            # 等待產品列表加載
            self.wait.until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, ".product-item")
                )
            )

            # 解析當前頁面產品
            products_on_page = self._parse_product_list()
            self.products.extend(products_on_page)
            print(f"第 {page} 頁抓取完成，獲得 {len(products_on_page)} 個產品")

            # 嘗試點擊下一頁
            if not self._go_to_next_page():
                print("已達到最後一頁")
                break

        print(f"\n總共抓取 {len(self.products)} 個產品")
        return self.products

    def _parse_product_list(self):
        """解析產品列表"""
        products = []
        items = self.driver.find_elements(By.CSS_SELECTOR, ".product-item")

        for item in items:
            try:
                product = self._parse_single_product(item)
                if product:
                    products.append(product)
            except Exception as e:
                print(f"解析產品時出錯: {str(e)}")
                continue

        return products

    def _parse_single_product(self, element):
        """解析單個產品數據"""
        try:
            name = element.find_element(
                By.CSS_SELECTOR, ".product-name"
            ).text

            price_text = element.find_element(
                By.CSS_SELECTOR, ".product-price"
            ).text
            price = self._parse_price(price_text)

            rating = element.find_element(
                By.CSS_SELECTOR, ".product-rating"
            ).get_attribute("title")

            review_text = element.find_element(
                By.CSS_SELECTOR, ".review-count"
            ).text
            review_count = self._parse_number(review_text)

            url = element.find_element(
                By.CSS_SELECTOR, "a"
            ).get_attribute("href")

            image_url = element.find_element(
                By.CSS_SELECTOR, "img"
            ).get_attribute("src")

            return Product(
                name=name,
                price=price,
                rating=rating,
                review_count=review_count,
                url=url,
                image_url=image_url
            )

        except NoSuchElementException:
            return None

    def _parse_price(self, price_text):
        """解析價格文字"""
        # 移除貨幣符號和逗號
        clean = price_text.replace("$", "").replace("HK$", "").replace(",", "")
        # 提取數字
        import re
        numbers = re.findall(r'\d+\.?\d*', clean)
        return float(numbers[0]) if numbers else 0.0

    def _parse_number(self, text):
        """解析數字"""
        import re
        numbers = re.findall(r'\d+', text.replace(",", ""))
        return int(numbers[0]) if numbers else 0

    def _go_to_next_page(self):
        """前往下一頁"""
        try:
            next_btn = self.driver.find_element(
                By.CSS_SELECTOR, ".pagination .next"
            )
            if "disabled" in next_btn.get_attribute("class"):
                return False

            next_btn.click()
            # 等待頁面加載
            self.wait.until(
                EC.staleness_of(self.driver.find_element(By.CSS_SELECTOR, ".product-item"))
            )
            return True

        except NoSuchElementException:
            return False

    def save_to_json(self, filename):
        """保存為 JSON 格式"""
        data = [
            {
                "name": p.name,
                "price": p.price,
                "rating": p.rating,
                "review_count": p.review_count,
                "url": p.url,
                "image_url": p.image_url
            }
            for p in self.products
        ]

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"數據已保存至 {filename}")

    def save_to_csv(self, filename):
        """保存為 CSV 格式"""
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(["名稱", "價格", "評分", "評論數", "連結", "圖片連結"])

            for p in self.products:
                writer.writerow([
                    p.name, p.price, p.rating,
                    p.review_count, p.url, p.image_url
                ])
        print(f"數據已保存至 {filename}")

    def close(self):
        """關閉瀏覽器"""
        self.driver.quit()

# 使用示例
if __name__ == "__main__":
    scraper = EcommerceScraper()

    # 抓取產品數據
    scraper.scrape_products(
        search_url="https://example-shop.com/search?q=laptop",
        max_pages=3
    )

    # 保存數據
    scraper.save_to_json("products.json")
    scraper.save_to_csv("products.csv")

    scraper.close()