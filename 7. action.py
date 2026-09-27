from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.action_chains import ActionChains

driver = webdriver.Chrome()

# ============================================
# 基本元素操作
# ============================================

# 點擊操作
button = driver.find_element(By.ID, "submit")
button.click()

# 輸入文字
text_field = driver.find_element(By.NAME, "username")
text_field.clear()  # 清空現有內容
text_field.send_keys("自動化測試用戶")

# 模擬鍵盤按鍵
text_field.send_keys(Keys.RETURN)  # 按 Enter
text_field.send_keys(Keys.TAB)     # 按 Tab
text_field.send_keys(Keys.CONTROL + "a")  # Ctrl+A 全選
text_field.send_keys(Keys.CONTROL + "c")  # Ctrl+C 複製

# ============================================
# 表單元素操作
# ============================================

# 下拉選單（Select）
select_element = driver.find_element(By.ID, "country")
select = Select(select_element)

select.select_by_visible_text("香港")      # 按可見文字選擇
select.select_by_value("HK")              # 按 value 屬性選擇
select.select_by_index(2)                 # 按索引選擇

# 獲取所有選項
all_options = select.options
for option in all_options:
    print(f"選項: {option.text}, Value: {option.get_attribute('value')}")

# 多選框
select.select_by_visible_text("選項A")
select.select_by_visible_text("選項B")

# 取消選擇
select.deselect_all()

# 單選框/複選框
checkbox = driver.find_element(By.ID, "agree-terms")
if not checkbox.is_selected():
    checkbox.click()

# ============================================
# 進階操作：ActionChains
# ============================================

actions = ActionChains(driver)

# 滑鼠懸停
menu = driver.find_element(By.ID, "main-menu")
submenu = driver.find_element(By.ID, "sub-menu")
actions.move_to_element(menu).pause(1).click(submenu).perform()

# 拖放操作
source = driver.find_element(By.ID, "draggable")
target = driver.find_element(By.ID, "droppable")
actions.drag_and_drop(source, target).perform()

# 右鍵點擊
element = driver.find_element(By.ID, "context-target")
actions.context_click(element).perform()

# 雙擊
element = driver.find_element(By.ID, "double-click-target")
actions.double_click(element).perform()

# 滾動到元素
element = driver.find_element(By.ID, "footer")
actions.move_to_element(element).perform()

# ============================================
# JavaScript 執行
# ============================================

# 滾動到頁面底部
driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

# 滾動到特定元素
element = driver.find_element(By.ID, "target")
driver.execute_script("arguments[0].scrollIntoView(true);", element)

# 修改元素屬性（例如移除 readonly）
driver.execute_script(
    "arguments[0].removeAttribute('readonly');",
    driver.find_element(By.ID, "date-picker")
)

# 獲取頁面信息
page_title = driver.execute_script("return document.title;")
inner_text = driver.execute_script("return document.body.innerText;")