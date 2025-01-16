from flask import Flask, request, jsonify
import threading
import os
import subprocess
import logging

app = Flask(__name__)

# 设置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def run_python_script(username, repository):
    """运行主 Python 逻辑"""
    try:
        logging.info(f"Running script for username={username}, repository={repository}")
        subprocess.run(["python3", "snapshoot.py", username, repository], check=True, timeout=300)
    except subprocess.TimeoutExpired:
        logging.error(f"Script timeout for user {username}, repository {repository}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running script: {e}")

@app.route('/trigger', methods=['POST'])
def trigger_action():
    data = request.json
    app.logger.info(f"Received request: {data}")

    if not data or "username" not in data or "repository" not in data:
        return jsonify({"error": "Invalid payload"}), 400
    if not isinstance(data["username"], str) or not isinstance(data["repository"], str):
        return jsonify({"error": "Invalid data types"}), 400

    username = data["username"]
    repository = data["repository"]

    # 异步运行脚本
    threading.Thread(target=run_python_script, args=(username, repository)).start()

    return jsonify({"message": "Triggered successfully", "username": username, "repository": repository})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=50001)
