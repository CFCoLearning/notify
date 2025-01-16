import os
import sys
import requests
import subprocess
import datetime
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from tempfile import TemporaryDirectory

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# 检查并获取环境变量
def get_env_var(env_name, default=None):
    value = os.getenv(env_name, default)
    if not value:
        logging.warning(f"Environment variable {env_name} is not set.")
    return value

# 环境变量或默认值
OUTPUT_DIR = get_env_var("OUTPUT_DIR", "/tmp/table")
LOCAL_API_URL = get_env_var("LOCAL_API_URL", "http://localhost:3000/send_group_msg")
REPO_README_URL = get_env_var("REPO_README_URL")
GROUP_ID = get_env_var("GROUP_ID")

# 确保输出目录存在
os.makedirs(OUTPUT_DIR, exist_ok=True)

def fetch_readme_content(url):
    """从指定 URL 获取 README 内容"""
    try:
        logging.info(f"Fetching README content from {url}")
        response = requests.get(url)
        response.raise_for_status()
        logging.info("Fetched README content successfully.")
        return response.text
    except requests.RequestException as e:
        logging.error(f"Failed to fetch README content: {e}")
        return None

def extract_table_content(content, start_marker="<!-- START_COMMIT_TABLE -->", end_marker="<!-- END_COMMIT_TABLE -->"):
    """从 README 内容中提取表格"""
    logging.info("Extracting table content from README...")
    table_start = content.find(start_marker)
    table_end = content.find(end_marker)
    if table_start == -1 or table_end == -1:
        logging.warning("Table markers not found in README content.")
        return None
    logging.info("Extracted table content successfully.")
    return content[table_start + len(start_marker):table_end].strip()

def convert_markdown_to_html(markdown_content, output_dir):
    """将 Markdown 转换为 HTML 文件"""
    logging.info("Converting Markdown to HTML...")
    try:
        markdown_path = os.path.join(output_dir, "table.md")
        html_path = os.path.join(output_dir, "table.html")
        with open(markdown_path, "w") as md_file:
            md_file.write(markdown_content)
        subprocess.run(["pandoc", markdown_path, "-o", html_path], check=True)
        logging.info("Converted Markdown to HTML successfully.")
        return html_path
    except Exception as e:
        logging.error(f"Failed to convert Markdown to HTML: {e}")
        return None

def capture_screenshot(html_path, output_dir):
    """使用 Selenium 截取 HTML 文件的屏幕截图"""
    logging.info("Capturing screenshot of the HTML...")
    try:
        # screenshot_path = os.path.join(output_dir, f"table_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        screenshot_path = os.path.join(output_dir, "table.png")
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--remote-debugging-port=9222")

        with webdriver.Chrome(options=chrome_options) as driver:
            driver.get(f"file://{html_path}")

            page_width = driver.execute_script("return document.body.scrollWidth")
            page_height = driver.execute_script("return document.body.scrollHeight")
            driver.set_window_size(page_width, page_height)

            driver.save_screenshot(screenshot_path)
        logging.info(f"Screenshot captured successfully: {screenshot_path}")
        return screenshot_path
    except Exception as e:
        logging.error(f"Failed to capture screenshot: {e}")
        return None

def send_image_to_group(image_path):
    """发送截图到指定群组"""
    logging.info(f"Sending screenshot to group {GROUP_ID}...")
    if not os.path.exists(image_path):
        logging.error("Image file does not exist.")
        return
    message_body = {
        "group_id": GROUP_ID,
        "message": [{"type": "image", "data": {"file": f"file://{image_path}"}}]
    }
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(LOCAL_API_URL, json=message_body)
        response.raise_for_status()
        logging.info("Image sent successfully.")
    except requests.RequestException as e:
        logging.error(f"Failed to send image to group: {e}")

def send_message_to_group(text):
    """发送文本消息到指定群组"""
    logging.info(f"Sending text message to group {GROUP_ID}...")
    message_body = {
        "group_id": GROUP_ID,
        "message": [{"type": "text", "data": {"text": text}}]
    }
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(LOCAL_API_URL, json=message_body)
        response.raise_for_status()
        logging.info("Text message sent successfully.")
    except requests.RequestException as e:
        logging.error(f"Failed to send text message: {e}")

def fetch_and_process_table(repository=None, trigger_user=None):
    """主逻辑：获取表格内容、生成 HTML 和截图并发送"""
    if repository:
        global REPO_README_URL
        REPO_README_URL = f"https://raw.githubusercontent.com/CFCoLearning/{repository}/main/README.md"
        logging.info(f"Using custom REPO_README_URL: {REPO_README_URL}")

    content = fetch_readme_content(REPO_README_URL)
    if not content:
        return

    table_content = extract_table_content(content)
    if not table_content:
        return

    with TemporaryDirectory() as temp_dir:
        html_path = convert_markdown_to_html(table_content, temp_dir)
        if not html_path:
            return

        screenshot_path = capture_screenshot(html_path, OUTPUT_DIR)
        if not screenshot_path:
            return

        if trigger_user and repository:
            notification_text = f"{trigger_user} 提交了 {repository} 共学记录"
            send_message_to_group(notification_text)

        send_image_to_group(screenshot_path)

if __name__ == "__main__":
    # 获取命令行参数：repository 和 trigger_user
    trigger_user = sys.argv[1] if len(sys.argv) > 1 else None
    repository = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        if not repository:
            raise EnvironmentError("Repository must be provided as the first argument.")
        fetch_and_process_table(repository, trigger_user)
    except EnvironmentError as e:
        logging.error(e)
