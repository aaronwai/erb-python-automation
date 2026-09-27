from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

class FormAutomation:
    """自動化表單填寫類"""

    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)

    def fill_registration_form(self, user_data):
        """填寫註冊表單"""
        self.driver.get("https://example.com/register")

        # 填寫文字輸入
        self._fill_text_field("first-name", user_data["first_name"])
        self._fill_text_field("last-name", user_data["last_name"])
        self._fill_text_field("email", user_data["email"])
        self._fill_text_field("phone", user_data["phone"])

        # 選擇下拉選單
        self._select_dropdown("country", user_data["country"])
        self._select_dropdown("city", user_data["city"])

        # 選擇單選按鈕
        self._select_radio("gender", user_data["gender"])

        # 選擇興趣（複選框）
        for interest in user_data["interests"]:
            self._select_checkbox("interests", interest)

        # 填寫日期
        self._fill_date_field("birth-date", user_data["birth_date"])

        # 填寫文本區域
        self._fill_textarea("bio", user_data["bio"])

        # 上傳文件
        self._upload_file("profile-photo", user_data["photo_path"])

        # 提交表單
        self._submit_form()

    def _fill_text_field(self, field_id, value):
        """填寫文字欄位"""
        field = self.wait.until(
            EC.presence_of_element_located((By.ID, field_id))
        )
        field.clear()
        field.send_keys(value)
        print(f"已填寫 {field_id}: {value}")

    def _select_dropdown(self, field_id, visible_text):
        """選擇下拉選單"""
        dropdown = Select(self.driver.find_element(By.ID, field_id))
        dropdown.select_by_visible_text(visible_text)
        print(f"已選擇 {field_id}: {visible_text}")

    def _select_radio(self, name, value):
        """選擇單選按鈕"""
        radio = self.driver.find_element(
            By.CSS_SELECTOR,
            f"input[name='{name}'][value='{value}']"
        )
        radio.click()
        print(f"已選擇 {name}: {value}")

    def _select_checkbox(self, name, value):
        """選擇複選框"""
        checkbox = self.driver.find_element(
            By.CSS_SELECTOR,
            f"input[name='{name}'][value='{value}']"
        )
        if not checkbox.is_selected():
            checkbox.click()
        print(f"已勾選 {name}: {value}")

    def _fill_date_field(self, field_id, date_value):
        """填寫日期欄位（處理不同日期格式）"""
        field = self.driver.find_element(By.ID, field_id)

        # 移除 readonly 屬性（如有）
        self.driver.execute_script(
            "arguments[0].removeAttribute('readonly');",
            field
        )

        field.clear()
        field.send_keys(date_value)
        print(f"已填寫日期 {field_id}: {date_value}")

    def _fill_textarea(self, field_id, text):
        """填寫文本區域"""
        textarea = self.driver.find_element(By.ID, field_id)
        textarea.clear()
        textarea.send_keys(text)
        print(f"已填寫 {field_id}")

    def _upload_file(self, field_id, file_path):
        """上傳文件"""
        upload_input = self.driver.find_element(By.ID, field_id)
        upload_input.send_keys(file_path)
        print(f"已上傳文件: {file_path}")

    def _submit_form(self):
        """提交表單"""
        submit_btn = self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
        )
        submit_btn.click()
        print("表單已提交")

# 使用示例
if __name__ == "__main__":
    user_info = {
        "first_name": "張",
        "last_name": "偉明",
        "email": "zhang.weiming@example.com",
        "phone": "91234567",
        "country": "香港",
        "city": "九龍",
        "gender": "male",
        "interests": ["科技", "音樂", "運動"],
        "birth_date": "1990-05-15",
        "bio": "熱愛自動化技術的開發者",
        "photo_path": "C:/Users/Photos/profile.jpg"
    }

    form = FormAutomation()
    form.fill_registration_form(user_info)