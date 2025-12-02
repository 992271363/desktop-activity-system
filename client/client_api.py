import requests
import os  
from dotenv import load_dotenv  #导入load_dotenv函数
from typing import List, Dict, Any
# 在代码文件加载时，立即执行 load_dotenv()
# 它会自动查找并加载当前目录或父目录下的 .env 文件
load_dotenv() 
# 从环境变量中读取 API 地址
# os.getenv 的第二个参数是“默认值”，如果环境变量里没有定义，就会使用这个默认值
# 这让代码在没有 .env 文件的环境下也能优雅地运行（比如，用于快速本地测试）
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

def send_data_to_api(data_list: List[Dict[str, Any]]):
    if not data_list:
        # ...
        return False
    # 去掉 URL 末尾的斜杠
    clean_base_url = API_BASE_URL.rstrip('/')
    # 这里会使用我们从环境变量加载的 API_BASE_URL
    api_url = f"{API_BASE_URL}/process-data/"

    print(f"通信模块: 准备发送 {len(data_list)} 条数据到 {api_url}...")

    try:
        response = requests.post(api_url, json=data_list, timeout=15) # 增加超时时间

        response.raise_for_status()

        print("通信模块: 数据发送成功！")
        return True

    except requests.exceptions.HTTPError as e:
        # 更具体地捕获HTTP错误
        print(f"通信模块: 数据发送失败！服务器返回错误。状态码: {e.response.status_code}")
        print("错误详情:", e.response.text)
        return False
    except requests.exceptions.RequestException as e:
        # 捕获所有其他网络相关的异常
        print(f"通信模块: 发生网络错误，无法连接到服务器。错误: {e}")
        return False

