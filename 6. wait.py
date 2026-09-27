from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

driver = webdriver.Chrome()

# ============================================
# 隱式等待 - 全局設置
# ============================================
driver.implicitly_wait(10)  # 所有 find_element 操作最多等待 10 秒

# ============================================
# 顯式等待 - 針對特定條件
# ============================================

wait = WebDriverWait(driver, timeout=10, poll_frequency=0.5)

# 等待元素可見
element = wait.until(
    EC.visibility_of_element_located((By.ID, "dynamic-content"))
)

# 等待元素可點擊
button = wait.until(
    EC.element_to_be_clickable((By.CSS_SELECTOR, "button.submit"))
)

# 等待元素存在於 DOM
element = wait.until(
    EC.presence_of_element_located((By.XPATH, "//div[@class='result']"))
)

# 等待元素消失（加載完成）
wait.until(
    EC.invisibility_of_element_located((By.ID, "loading-spinner"))
)

# ============================================
# 常用 Expected Conditions
# ============================================

conditions = {
    "title_is": EC.title_is("預期標題"),
    "title_contains": EC.title_contains("部分標題"),
    "presence_of_element": EC.presence_of_element_located((By.ID, "id")),
    "visibility_of_element": EC.visibility_of_element_located((By.ID, "id")),
    "element_to_be_clickable": EC.element_to_be_clickable((By.ID, "id")),
    "text_to_be_present": EC.text_to_be_present_in_element(
        (By.ID, "status"), "完成"
    ),
    "element_to_be_selected": EC.element_to_be_selected(
        driver.find_element(By.ID, "checkbox")
    ),
    "alert_is_present": EC.alert_is_present(),
    "frame_to_be_available": EC.frame_to_be_available_and_switch_to_it(
        (By.ID, "iframe")
    )
}