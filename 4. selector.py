from selenium import webdriver
from selenium.webdriver.common.by import By

driver = webdriver.Chrome()

# ============================================
# 1. ID 定位 - 最推薦，唯一且穩定
# ============================================
element = driver.find_element(By.ID, "username")

# ============================================
# 2. Name 定位 - 常用於表單元素
# ============================================
element = driver.find_element(By.NAME, "email")

# ============================================
# 3. Class Name 定位 - 適用於樣式類
# ============================================
element = driver.find_element(By.CLASS_NAME, "btn-primary")

# 注意：class 可能包含多個類名，需使用 CSS Selector
elements = driver.find_elements(By.CSS_SELECTOR, ".btn.primary")

# ============================================
# 4. Tag Name 定位 - 按 HTML 標籤
# ============================================
all_links = driver.find_elements(By.TAG_NAME, "a")
all_images = driver.find_elements(By.TAG_NAME, "img")

# ============================================
# 5. Link Text 定位 - 精確匹配連結文字
# ============================================
element = driver.find_element(By.LINK_TEXT, "忘記密碼？")

# ============================================
# 6. Partial Link Text 定位 - 部分匹配連結文字
# ============================================
element = driver.find_element(By.PARTIAL_LINK_TEXT, "密碼")

# ============================================
# 7. CSS Selector 定位 - 靈活強大，推薦使用
# ============================================

# 基本選擇器
element = driver.find_element(By.CSS_SELECTOR, "#login-form")  # ID
element = driver.find_element(By.CSS_SELECTOR, ".input-field")  # class
element = driver.find_element(By.CSS_SELECTOR, "div.container")  # 元素+class

# 屬性選擇器
element = driver.find_element(By.CSS_SELECTOR, "[type='submit']")
element = driver.find_element(By.CSS_SELECTOR, "[data-testid='login-btn']")

# 層級選擇器
element = driver.find_element(By.CSS_SELECTOR, "nav ul li a")
element = driver.find_element(By.CSS_SELECTOR, "div > p > span")

# 偽類選擇器
element = driver.find_element(By.CSS_SELECTOR, "li:first-child")
element = driver.find_element(By.CSS_SELECTOR, "tr:nth-child(3)")

# 組合選擇器
element = driver.find_element(
    By.CSS_SELECTOR,
    "input[type='text'].required:focus"
)

# ============================================
# 8. XPath 定位 - 最靈活，適用複雜場景
# ============================================

# 絕對路徑（不推薦，易失效）
element = driver.find_element(By.XPATH, "/html/body/div[1]/div[2]/form")

# 相對路徑（推薦）
element = driver.find_element(By.XPATH, "//form[@id='login']")

# 屬性定位
element = driver.find_element(By.XPATH, "//input[@name='username']")
element = driver.find_element(By.XPATH, "//button[contains(@class, 'btn')]")

# 文字定位
element = driver.find_element(By.XPATH, "//a[text()='登入']")
element = driver.find_element(By.XPATH, "//span[contains(text(), '歡迎')]")

# 軸定位（父子、兄弟關係）
element = driver.find_element(By.XPATH, "//td[text()='產品A']/following-sibling::td[2]")
element = driver.find_element(By.XPATH, "//div[@class='parent']/child::input")

# 邏輯運算
element = driver.find_element(
    By.XPATH,
    "//input[@type='text' and @required and contains(@class, 'email')]"
)