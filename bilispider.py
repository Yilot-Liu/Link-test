import requests
from bs4 import BeautifulSoup
from urllib.parse import quote, urljoin
import openpyxl as xl
import json
import time
import random
import os
import sys
import logging
import urllib.parse

proxies = {
    "http": "http://127.0.0.1:7890",
    "https": "http://127.0.0.1:7890"
}
# 日志文件夹和路径
LOG_DIR = 'like_data'
LOG_FILE = os.path.join(LOG_DIR, 'bilispider.log')
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

# 更完整的请求头
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'Referer': 'https://www.bilibili.com/',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Origin': 'https://www.bilibili.com',
    'Connection': 'keep-alive'
}

def get_proxies():
    # 你可以在这里更换其他代理或直接返回None不使用代理
    return {
        "http": "http://127.0.0.1:7890",
        "https": "http://127.0.0.1:7890",
    }
    # return None  # 如果不使用代理，取消这行注释

def fetch_data():
    keyword = input("请输入您想要查询的内容：")
    encoded_keyword = quote(keyword)
    num = int(input("您想查询几页: "))

    wb = xl.Workbook()
    sheet = wb.active
    sheet.title = "视频数据"
    sheet.append(["标题", "播放量", "弹幕数", "UP主", "时长", "发布时间", "视频链接"])

    json_results = []
    proxies = get_proxies()

    for page in range(1, num + 1):
        url = f"https://search.bilibili.com/all?keyword={encoded_keyword}&page={page}"
        print(f"正在处理第 {page} 页: {url}")

        try:
            # 添加随机延迟避免被封
            time.sleep(random.uniform(1, 3))
            
            response = requests.get(
                url,
                headers=headers,
                proxies=proxies,
                timeout=10,
                verify=False
            )
            
            if response.status_code != 200:
                print(f"请求失败，状态码: {response.status_code}")
                continue

            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 新的选择器 - 根据B站2023年最新页面结构调整
            video_items = soup.find_all('div', class_='bili-video-card')
            if not video_items:
                video_items = soup.find_all('li', class_='video-item')  # 备用选择器
                
            if not video_items:
                print("⚠️ 警告: 未找到视频元素，可能是页面结构变化或反爬机制")
                # 打印页面内容前500字符用于调试
                print("页面内容片段:", response.text[:500])
                continue

            for item in video_items:
                try:
                    # 提取标题
                    title_elem = item.find('h3', class_='bili-video-card__info--tit') or \
                                item.find('a', class_='title')
                    title = title_elem.get('title') if title_elem else title_elem.get_text(strip=True)
                    
                    # 提取链接
                    link_elem = item.find('a', href=True)
                    link = urljoin("https://www.bilibili.com", link_elem['href']) if link_elem else ""
                    
                    # 提取播放信息
                    play_info = item.find_all('span', class_='bili-video-card__stats--item') or \
                               item.find_all('span', class_='so-icon watch-num')
                    play_count = play_info[0].get_text(strip=True) if len(play_info) > 0 else "0"
                    danmu_count = play_info[1].get_text(strip=True) if len(play_info) > 1 else "0"
                    
                    # 提取UP主
                    up_elem = item.find('span', class_='bili-video-card__info--author') or \
                              item.find('a', class_='up-name')
                    up_name = up_elem.get_text(strip=True) if up_elem else "未知"
                    
                    # 提取时长和发布时间
                    duration = item.find('span', class_='bili-video-card__stats__duration').get_text(strip=True) \
                               if item.find('span', class_='bili-video-card__stats__duration') else "未知"
                    pubdate = item.find('span', class_='bili-video-card__info--date').get_text(strip=True) \
                              if item.find('span', class_='bili-video-card__info--date') else "未知"
                    
                    # 添加到Excel
                    sheet.append([title, play_count, danmu_count, up_name, duration, pubdate, link])
                    
                    # 添加到JSON
                    json_results.append({
                        "title": title,
                        "play_count": play_count,
                        "danmu_count": danmu_count,
                        "up_name": up_name,
                        "duration": duration,
                        "pubdate": pubdate,
                        "url": link,
                        "page": page
                    })
                    
                    print(f"√ 获取: {title[:20]}... 播放:{play_count}")
                    
                except Exception as e:
                    print(f"处理单个视频时出错: {str(e)}")
                    continue

        except Exception as e:
            print(f"处理第 {page} 页时出错: {str(e)}")
            continue

    # 保存文件
    try:
        excel_filename = f"{keyword}_视频数据.xlsx"
        wb.save(excel_filename)
        print(f"\nExcel文件已保存: {excel_filename}")
        
        json_filename = f"{keyword}_视频数据.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(json_results, f, ensure_ascii=False, indent=2)
        print(f"JSON文件已保存: {json_filename}")
        print(f"总计获取了 {len(json_results)} 条视频数据")
    except Exception as e:
        print(f"保存文件时出错: {str(e)}")

def bilibili_search(keyword, page=1):
    url = (
        f'https://api.bilibili.com/x/web-interface/search/type'
        f'?search_type=video&keyword={urllib.parse.quote(keyword)}&page={page}'
    )
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        'Referer': 'https://www.bilibili.com/',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Origin': 'https://www.bilibili.com',
        'Connection': 'keep-alive',
        'Cookie': 'DedeUserID=397409402; SESSDATA=8853c48a%2C1753258690%2C34523%2A12CjA5xug9dLMSV2uuYqnYw903pKClfx5NQBzuefQtC4KuqKDfJXDKfa2vj9lzfhopQhkSVmV5ZmVyODBCQklKTF9Vcjl1NGJpM1Axelc1djFHektGTUo1QXA1R09mYXNTU09iMkx6YkxUbjhOUkZ5WHJWYjBodW44REN2UHFpQXdzWkZ6OXoxY0pBIIEC; buvid4=164C2F53-D523-6E46-88A2-597E93A60EDF71906-025012408-lr%2FXgVMsN9mcKYHl2lT7Kw%3D%3D; bili_jct=0d75b814a7bec6977c24be1397cba973'
    }
    try:
        resp = requests.get(url, timeout=10, proxies=proxies, headers=headers)
        logging.info(f'响应内容: {resp.text[:200]}')  # 打印前200字符
        data = resp.json()
        result = []
        for item in data.get('data', {}).get('result', []):
            title = item.get('title', '').replace('<em class="keyword">', '').replace('</em>', '')
            bvid = item.get('bvid')
            if title and bvid:
                result.append({
                    'title': title,
                    'url': f'https://www.bilibili.com/video/{bvid}'
                })
        return result
    except Exception as e:
        with open('like_data/last_error.html', 'w', encoding='utf-8') as f:
            f.write(resp.text)
        logging.error(f'爬取第{page}页失败: {e}，已保存响应内容到like_data/last_error.html')
        return []

def main():
    if len(sys.argv) < 2:
        logging.error('用法: python bilispider.py <视频标题关键词> [页数]')
        sys.exit(1)
    title = sys.argv[1]
    pages = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    logging.info(f'开始爬取B站视频，关键词：{title}，页数：{pages}')
    all_videos = []
    for page in range(1, pages+1):
        logging.info(f'正在爬取第{page}页...')
        video_list = bilibili_search(title, page)
        logging.info(f'本页爬取到{len(video_list)}条视频')
        all_videos.extend(video_list)
    # 保存到json
    safe_title = urllib.parse.quote(title, safe='')
    json_path = os.path.join(LOG_DIR, f'like_{safe_title}.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(all_videos, f, ensure_ascii=False, indent=2)
    logging.info(f'已保存到 {json_path}')
    logging.info('爬虫运行结束')

if __name__ == '__main__':
    main()