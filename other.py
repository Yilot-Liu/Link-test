import os
import json
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('spider.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

# 添加启动日志
logging.info("程序启动")
logging.info(f"当前工作目录: {os.getcwd()}")
logging.info(f"Python版本: {sys.version}")

# Configuration
BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
MAX_RETRIES = 3
WAIT_TIMEOUT = 15
WEEK_RANGE = range(1, 21)  # Weeks 1-20

def init_driver():
    """Initialize and configure Edge WebDriver"""
    try:
        edge_options = Options()
        edge_options.add_argument("--headless=new")
        edge_options.add_argument("--disable-gpu")
        edge_options.add_argument("--no-sandbox")
        edge_options.add_argument("--disable-dev-shm-usage")
        edge_options.add_argument("--window-size=1920,1080")
        
        # 使用Edge浏览器
        driver = webdriver.Edge(options=edge_options)

        # Mask selenium detection
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            """
        })

        return driver
    except Exception as e:
        logging.error(f"Driver initialization failed: {str(e)}")
        raise

def login(driver, username, password):
    """Login to the educational system"""
    url = "https://authserver.csuft.edu.cn/authserver/login?service=http%3A%2F%2Fjwgl.csuft.edu.cn%2F"
    
    for attempt in range(MAX_RETRIES):
        try:
            driver.get(url)
            WebDriverWait(driver, WAIT_TIMEOUT).until(
                EC.presence_of_element_located((By.ID, "username"))
            ).send_keys(username)
            
            driver.find_element(By.ID, "password").send_keys(password)
            driver.find_element(By.CSS_SELECTOR, ".auth_login_btn.primary.full_width").click()
            
            # Verify login success
            WebDriverWait(driver, WAIT_TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.block2tex"))
            )
            return True
        except TimeoutException:
            logging.warning(f"Login attempt {attempt + 1} failed")
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(2)

def navigate_to_schedule_page(driver):
    """Navigate to the schedule page"""
    try:
        WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'div.block2tex'))
        ).click()
        
        WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[href="/jsxsd/xskb/xskb_list.do"]'))
        ).click()
    except TimeoutException as e:
        logging.error("Failed to navigate to schedule page")
        raise

def select_week(driver, week_num):
    """Select specific week in the schedule"""
    try:
        select_element = WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.presence_of_element_located((By.ID, "zc"))
        )
        Select(select_element).select_by_value(str(week_num))
        time.sleep(1)  # Wait for page to update
    except Exception as e:
        logging.error(f"Failed to select week {week_num}")
        raise

def extract_schedule(driver):
    """Extract schedule data from the table"""
    try:
        table_data = []
        rows = WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, "//table[@id='kbtable']/tbody/tr[position()>=2 and position()<=7]"))
        )
        
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            table_data.append([cell.text.strip() for cell in cells])
            
        return table_data
    except Exception as e:
        logging.error("Failed to extract schedule data")
        raise

def save_schedule_json(data, week_num):
    """Save schedule data to JSON file"""
    try:
        os.makedirs(BASE_DIR, exist_ok=True)
        filename = f"number.{week_num}.json"
        filepath = os.path.join(BASE_DIR, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        logging.info(f"✅ Week {week_num} schedule saved to: {filepath}")
    except Exception as e:
        logging.error(f"Failed to save week {week_num} schedule: {str(e)}")
        raise

def run_spider(username, password):
    """Main function to run the spider"""
    driver = None
    try:
        driver = init_driver()
        login(driver, username, password)
        navigate_to_schedule_page(driver)

        for week in WEEK_RANGE:
            for attempt in range(MAX_RETRIES):
                try:
                    select_week(driver, week)
                    schedule_data = extract_schedule(driver)
                    save_schedule_json(schedule_data, week)
                    break
                except Exception as e:
                    if attempt == MAX_RETRIES - 1:
                        logging.error(f"Failed to process week {week} after {MAX_RETRIES} attempts")
                        raise
                    logging.warning(f"Retrying week {week}, attempt {attempt + 1}")
                    time.sleep(2)

        return True, "Schedule data successfully collected"
    except Exception as e:
        logging.error(f"Spider failed: {str(e)}")
        return False, str(e)
    finally:
        if driver:
            driver.quit()

if __name__ == '__main__':
    # 这里只保留直接运行爬虫的主流程
    # 例如:
    # username = ...
    # password = ...
    # run_spider(username, password)
    pass  # 你可以根据需要补充主流程