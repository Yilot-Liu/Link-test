from flask import Flask, request, jsonify, send_file
import subprocess
import os
import json
from threading import Thread
import urllib.parse

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
                script_path = os.path.join(os.path.dirname(__file__), 'spider1.py')
                result = subprocess.run(
                    ['python', script_path, username, password],
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
                else:
                    print("爬虫返回错误：", result.stderr)

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

@app.route('/start-like-spider', methods=['POST'])
def start_like_spider():
    try:
        data = request.json
        title = data.get('title')
        pages = int(data.get('pages', 1))
        if not title:
            return jsonify({'success': False, 'message': '缺少视频标题参数'}), 400
        # 调用 bilispider.py
        result = subprocess.run(['python', 'bilispider.py', title, str(pages)], capture_output=True, text=True)
        if result.returncode == 0:
            return jsonify({'success': True, 'message': '爬虫已完成'})
        else:
            return jsonify({'success': False, 'message': result.stderr or '爬虫执行失败'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/get-like', methods=['GET'])
def get_like():
    try:
        title = request.args.get('title', '')
        if not title:
            return jsonify([])
        safe_title = urllib.parse.quote(title, safe='')
        filename = f'like_data/like_{safe_title}.json'
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return jsonify(json.load(f))
        else:
            return jsonify([])
    except Exception as e:
        return jsonify([])

if __name__ == '__main__':
    app.run(port=5000, debug=False, use_reloader=False)
