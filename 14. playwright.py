# 安裝 Playwright
# pip install playwright
# playwright install

from playwright.sync_api import sync_playwright, devices

def playwright_basic_example():
    """Playwright 基本示例"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()

        page.goto("https://www.google.com")
        # Fix selector: Google search box is input[name="q"], not textarea
        search_locator = page.locator('[name="q"]')
        search_locator.fill("Playwright automation")

        # Wrap enter press inside expect_navigation
        with page.expect_navigation():
            search_locator.press("Enter")

        page.wait_for_load_state("networkidle")
        page.screenshot(path="search_results.png")

        # Use Locator API (recommended instead of query_selector_all)
        results = page.locator("h3").all()
        for result in results[:5]:
            print(result.inner_text())

        browser.close()

def playwright_advanced_example():
    """Playwright 進階示例：自動登入"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        # Explicit context
        context = browser.new_context()
        page = context.new_page()
        page.set_default_timeout(30000)

        page.goto("https://example.com/login")
        page.fill("#username", "test_user")
        page.fill("#password", "test_pass")

        with page.expect_navigation():
            page.click("button[type='submit']")

        # Wait for dashboard instead of instant is_visible check
        page.wait_for_selector(".dashboard")
        print("登入成功")

        context.storage_state(path="auth_state.json")
        browser.close()

def playwright_api_vs_selenium():
    """Playwright 與 Selenium API 對比"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={'width':1920, 'height':1080})
        page = context.new_page()

        # === 元素定位 ===
        # Selenium: driver.find_element(By.ID, "id")
        # Playwright: page.locator("#id")
        # === 點擊操作 ===
        # Selenium: element.click()
        # Playwright: page.click("#id") 或 locator.click()
        # === 輸入文字 ===
        # Selenium: element.send_keys("text")
        # Playwright: page.fill("#id", "text")
        # === 獲取文字 ===
        # Selenium: element.text
        # Playwright: locator.inner_text()
        # === 等待元素 ===
        # Selenium: WebDriverWait(driver, 10).until(...)
        # Playwright: page.wait_for_selector("#id")
        # Playwright 獨有功能
        # 自動等待：所有操作自動等待元素就緒
        # 網絡攔截：page.route("**/*.{png,jpg,jpeg}", lambda route: route.abort())
        # 移動端模擬（CORRECT API）：
        # mobile_context = browser.new_context(**devices["iPhone 14"])

        browser.close()

if __name__ == "__main__":
    playwright_basic_example()