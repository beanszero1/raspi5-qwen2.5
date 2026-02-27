import requests
import json

# Dify API 配置
API_KEY = "app-d2XDnd"  # 替换为你的Dify API密钥
BASE_URL = "http://localhost"  # 如果是本地部署，改为 http://localhost:端口号
ENDPOINT = "/v1/chat-messages"  # 对话类应用端点

# 请求头
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# 请求数据
payload = {
    "inputs": {},  # 输入参数，根据你的应用配置可能需要填写
    "query": "你好，请介绍一下你自己",  # 用户输入的问题
    "response_mode": "blocking",  # 响应模式：blocking阻塞式，streaming流式
    "conversation_id": "",  # 首次对话留空，后续使用返回的conversation_id维持会话
    "user": "test-user-123"  # 用户ID，用于区分用户
}

try:
    # 发送POST请求
    response = requests.post(
        f"{BASE_URL}{ENDPOINT}",
        headers=headers,
        data=json.dumps(payload)
    )
    
    # 检查响应状态
    response.raise_for_status()
    
    # 解析响应数据
    result = response.json()
    
    # 输出结果
    print("API调用成功！")
    print("回答内容:", result.get("answer", ""))
    print("会话ID:", result.get("conversation_id", ""))
    print("完整响应:", json.dumps(result, indent=2, ensure_ascii=False))
    
except requests.exceptions.RequestException as e:
    print(f"API调用失败: {e}")
    if hasattr(e, 'response') and e.response:
        print("错误详情:", e.response.text)