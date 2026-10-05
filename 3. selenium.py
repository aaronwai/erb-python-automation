from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

# ==============================================
# Selenium Chrome Browser Basic Demo
# Function: Launch Chrome browser, visit webpage, get page info, close browser
# ==============================================


def basic_browser_launch():
    """
    Basic browser launch function
    - Initialize Chrome browser
    - Navigate to target website (Google)
    - Print page title and current URL
    - Pause for observation, then close browser
    """
    # Create Chrome browser instance, use default settings
    driver = webdriver.Chrome()

    # Navigate browser to target URL
    driver.get("https://www.google.com")

    # Get and print HTML page title
    print(f"頁面標題: {driver.title}")
    # Get and print current loaded url
    print(f"當前網址: {driver.current_url}")

    # Pause script execution for 3 seconds (simple static wait)
    time.sleep(3)

    # Quit browser completely, release browser process
    driver.quit()


def advanced_browser_setup():
    """
    Advanced Chrome browser configuration
    Customize browser startup arguments to simulate real user environment
    Return configured selenium driver object for further operations
    """
    # Initialize Chrome options object for custom startup arguments

    chrome_options = Options()

    # Headless mode: run browser without GUI window
    # chrome_options.add_argument("--headless")

    # Disable GPU hardware acceleration (avoid rendering crash in headless mode)
    chrome_options.add_argument("--disable-gpu")

    # Set browser window resolution
    chrome_options.add_argument("--window-size=1920,1080")

    # Block website notification popup permission requests
    chrome_options.add_argument("--disable-notifications")
    #     chrome_options.add_argument("--proxy-server=http://myproxy:8080")
    # chrome_options.add_argument("--user-agent=MyCustomUA")
    # Custom User-Agent string, disguise selenium bot as normal desktop Chrome browser
    chrome_options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )
    # chrome_options.add_extension("path/to/extension.crx")
    # Add Chrome extension
    # Create Chrome instance with custom options
    driver = webdriver.Chrome(options=chrome_options)

    # Implicit wait: up to 10s, wait for element to appear before throw exception
    # Applies globally for all element lookup actions
    driver.implicitly_wait(10)

    # Return configured driver for reuse in other functions
    return driver


# Main entry point: run when execute this python file directly
if __name__ == "__main__":
    # Run basic browser demo
    basic_browser_launch()
