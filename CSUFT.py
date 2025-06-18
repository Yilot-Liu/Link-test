import json
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

try:
    options = Options()
    options.add_argument('--start-maximized')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    chromedriver_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chromedriver.exe')
    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=options)

    keywords = ["大学物理", "高等数学"]
    results = []

    for keyword in keywords:
        driver.get("https://www.bilibili.com/")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "nav-search-input"))
        )
        search_box = driver.find_element(By.CLASS_NAME, "nav-search-input")
        search_box.clear()
        search_box.send_keys(keyword)
        search_btn = driver.find_element(By.CLASS_NAME, "nav-search-btn")
        search_btn.click()
        time.sleep(5)  # 等待第一页加载

        # 跳到第2页
        try:
            next_btn = driver.find_element(By.CSS_SELECTOR, ".pagination-btn-next")
            next_btn.click()
            time.sleep(5)  # 等待第2页加载
        except Exception as e:
            print(f"{keyword} 没有第2页")
            continue

        # 爬取第2页前5个标题
        h3s = driver.find_elements(By.CSS_SELECTOR, "h3.bili-video-card__info--tit")[:5]
        print(f"{keyword} 第2页搜索到 {len(h3s)} 个视频")
        for h3 in h3s:
            title = h3.get_attribute("title") or h3.text
            results.append({"title": title})

        # 跳到第3页
        try:
            next_btn = driver.find_element(By.CSS_SELECTOR, ".pagination-btn-next")
            next_btn.click()
            time.sleep(5)  # 等待第3页加载
        except Exception as e:
            print(f"{keyword} 没有第3页")
            continue

        # 爬取第3页前5个标题
        h3s = driver.find_elements(By.CSS_SELECTOR, "h3.bili-video-card__info--tit")[:5]
        print(f"{keyword} 第3页搜索到 {len(h3s)} 个视频")
        for h3 in h3s:
            title = h3.get_attribute("title") or h3.text
            results.append({"title": title})

    # 保存到 data/like_videos.json
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    os.makedirs(data_dir, exist_ok=True)
    with open(os.path.join(data_dir, 'like_videos.json'), 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("已保存到 data/like_videos.json")
    print(f"共爬取到 {len(results)} 个视频")
    input("按任意键退出程序")

except Exception as e:
    print(f"程序运行出错: {e}")
finally:
    try:
        driver.quit()
    except:
        pass
