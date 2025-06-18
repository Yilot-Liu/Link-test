from flask import Flask, request, jsonify, send_from_directory
import subprocess
import os
import json
from threading import Thread
import logging
import threading
import time
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('server.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

app = Flask(__name__, static_folder='static')

# 存储课程数据
COURSE_DATA = {}
BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

# 确保数据目录存在
os.makedirs(BASE_DIR, exist_ok=True)

FETCH_INTERVAL_MINUTES = 2  # 每2分钟自动运行一次

def load_all_course_data():
    """加载所有已存在的课程数据"""
    try:
        for week in range(1, 21):
            filename = f'number.{week}.json'
            filepath = os.path.join(BASE_DIR, filename)
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    COURSE_DATA[week] = json.load(f)
                    logging.info(f"已加载第{week}周数据")
    except Exception as e:
        logging.error(f"加载课程数据时出错: {str(e)}", exc_info=True)

@app.route('/')
def index():
    return send_from_directory('static', 'class.html')

@app.route('/start-spider', methods=['POST'])
def start_spider():
    try:
        data = request.json
        username = data['username']
        password = data['password']
        
        logging.info(f"收到爬虫启动请求，用户名: {username}")
        
        # 启动爬虫线程
        def run_spider():
            try:
                logging.info("开始执行爬虫程序")
                result = subprocess.run(
                    ['python', 'other.py', '--direct'],
                    input=f"{username}\n{password}\n",
                    text=True,
                    capture_output=True
                )
                
                logging.info(f"爬虫执行完成，返回码: {result.returncode}")
                if result.stdout:
                    logging.info(f"爬虫输出: {result.stdout}")
                if result.stderr:
                    logging.error(f"爬虫错误: {result.stderr}")
                
                if result.returncode == 0:
                    # 重新加载所有数据
                    load_all_course_data()
            
            except Exception as e:
                logging.error(f"爬虫执行错误: {str(e)}", exc_info=True)

        # 启动新线程执行爬虫
        Thread(target=run_spider).start()
        
        return jsonify({
            'success': True,
            'message': '爬虫已启动，数据将在稍后更新'
        })
        
    except Exception as e:
        logging.error(f"处理请求时出错: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/get-course/<int:week>', methods=['GET'])
def get_course(week):
    try:
        # 首先检查内存中是否有数据
        if week in COURSE_DATA:
            return jsonify(COURSE_DATA[week])
        
        # 如果内存中没有，尝试从文件加载
        filename = f'number.{week}.json'
        filepath = os.path.join(BASE_DIR, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                COURSE_DATA[week] = data
                return jsonify(data)
        
        # 如果文件也不存在，返回空数据
        empty_data = [['' for _ in range(7)] for _ in range(6)]
        return jsonify(empty_data)
        
    except Exception as e:
        logging.error(f"获取课程数据时出错: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/like-videos')
def like_videos():
    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'like_videos.json')
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    else:
        return jsonify([])

def run_spider_periodically():
    while True:
        try:
            print("自动启动爬虫...")
            python_exe = sys.executable
            result = subprocess.run(
                [python_exe, 'csuft.py'],
                cwd=os.path.dirname(os.path.abspath(__file__)),
                capture_output=True,
                text=True
            )
            print("stdout:", result.stdout)
            print("stderr:", result.stderr)
            if result.returncode != 0:
                print(f"定时爬虫出错: exit code {result.returncode}")
        except Exception as e:
            print(f"定时爬虫出错: {e}")
        time.sleep(FETCH_INTERVAL_MINUTES * 60)

if __name__ == '__main__':
    logging.info("服务器启动")
    logging.info(f"数据目录: {BASE_DIR}")
    # 启动时加载所有已存在的数据
    load_all_course_data()
    threading.Thread(target=run_spider_periodically, daemon=True).start()
    app.run(port=5000, debug=True)