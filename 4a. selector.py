from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def demoqa_login_demo():
    """
    Working demo: open demoqa login page, input username and password, click login button
    Website: https://demoqa.com/login
    Test account:
        username: admin
        password: admin123
    """
    # Initialize Chrome browser
    driver = webdriver.Chrome()
    # Maximize browser window
    driver.maximize_window()

    try:
        # Navigate to demoqa login page
        driver.get("https://demoqa.com/login")

        # Explicit wait: wait up to 10 seconds for elements to load
        wait = WebDriverWait(driver, 10)

        # Locate username input field and type username
        username_input = wait.until(
            EC.presence_of_element_located((By.ID, "userName"))
        )
        username_input.clear()  # Clear existing text inside input box
        username_input.send_keys("admin")

        # Locate password input field and type password
        password_input = wait.until(
            EC.presence_of_element_located((By.ID, "password"))
        )
        password_input.clear()
        password_input.send_keys("admin123")

        # Locate login button and click it
        login_button = wait.until(
            EC.element_to_be_clickable((By.ID, "login"))
        )
        login_button.click()

        # Wait and verify login result
        # Check if welcome label appears after login
        welcome_text = wait.until(
            EC.presence_of_element_located((By.ID, "userName-value"))
        )
        print(f"✅ Login success! User info: {welcome_text.text}")

    except Exception as e:
        print(f"❌ Error occurred: {str(e)}")
    finally:
        # Always close browser whether success or fail
        driver.quit()

if __name__ == "__main__":
    demoqa_login_demo()