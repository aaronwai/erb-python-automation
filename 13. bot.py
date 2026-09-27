from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import random
import time

class SmartFormFiller:
    """智能表單填寫機器人"""
    def __init__(self):
        self.driver = webdriver.Chrome()
        self.driver.implicitly_wait(10)

    def fill_form_intelligently(self, form_data):
        inputs = self.driver.find_elements(By.CSS_SELECTOR, "input, textarea, select")
        for input_field in inputs:
            try:
                # Skip invisible / disabled
                if not (input_field.is_displayed() and input_field.is_enabled()):
                    continue
                field_info = self._analyze_field(input_field)
                matched_value = self._match_data(field_info, form_data)
                if matched_value is not None:
                    self._fill_field(input_field, field_info, matched_value)
                    time.sleep(random.uniform(0.5, 1.5))
            except Exception as e:
                print(f"跳過欄位失敗: {str(e)}")
                continue

    def _analyze_field(self, element):
        return {
            'type': element.get_attribute('type') or 'text',
            'name': element.get_attribute('name'),
            'id': element.get_attribute('id'),
            'placeholder': element.get_attribute('placeholder'),
            'tag': element.tag_name
        }

    def _match_data(self, field_info, form_data):
        # Remove class from identifiers to avoid false match
        field_identifiers = [
            field_info['name'],
            field_info['id'],
            field_info['placeholder']
        ]
        for identifier in field_identifiers:
            if not identifier:
                continue
            identifier_lower = identifier.lower()
            for key, value in form_data.items():
                key_lower = key.lower()
                # Better matching: exact substring, but can tweak later
                if key_lower in identifier_lower:
                    return value
        return None

    def _fill_field(self, element, field_info, value):
        field_type = field_info['type']
        tag = field_info['tag']

        if tag == "textarea" or field_type in ['text', 'email', 'tel', 'password']:
            element.clear()
            element.send_keys(value)
        elif field_type == 'radio':
            # Match radio value instead of boolean
            if element.get_attribute("value") == str(value):
                element.click()
        elif field_type == 'checkbox':
            desired = str(value).lower() in ['true', '1', 'yes']
            if element.is_selected() != desired:
                element.click()
        elif field_type == 'date':
            self.driver.execute_script("arguments[0].value = arguments[1];", element, value)
        elif tag == "select":
            select = Select(element)
            try:
                select.select_by_visible_text(str(value))
            except:
                select.select_by_value(str(value))

if __name__ == "__main__":
    filler = SmartFormFiller()
    try:
        filler.driver.get("https://example.com/form")
        user_data = {
            "姓名": "張偉明",
            "email": "zhang@example.com",
            "電話": "91234567",
            "公司": "科技有限公司",
            "地址": "香港九龍"
        }
        filler.fill_form_intelligently(user_data)
        input("完成，按Enter關閉瀏覽器...")
    finally:
        filler.driver.quit()