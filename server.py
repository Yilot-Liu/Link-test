from flask import Flask, request, jsonify
import subprocess
import os
import json
from threading import Thread

app = Flask(__name__)

# 存储课程数据
COURSE_DATA = {}

@app.route('/start-spider', methods=['POST'])
def start_spider():
    try:
        data = request.json
        username = data['username']
        password = data['password']
        
        # 启动爬虫线程
        def run_spider():
            try:
                result = subprocess.run(
                    ['python', 'other.py', username, password],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    # 加载爬取的数据
                    for week in range(1, 21):
                        filename = f'class_data/number.{week}.json'
                        if os.path.exists(filename):
                            with open(filename, 'r', encoding='utf-8') as f:
                                COURSE_DATA[week] = json.load(f)
            
            except Exception as e:
                print(f"爬虫执行错误: {str(e)}")

        # 启动新线程执行爬虫
        Thread(target=run_spider).start()
        
        return jsonify({
            'success': True,
            'message': '爬虫已启动，数据将在稍后更新'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/get-course/<int:week>', methods=['GET'])
def get_course(week):
    try:
        if week in COURSE_DATA:
            return jsonify(COURSE_DATA[week])
        else:
            # 尝试从文件加载
            filename = f'class_data/number.{week}.json'
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    return jsonify(json.load(f))
            else:
                return jsonify({'error': '数据不存在'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=False, use_reloader=False)