#!/usr/bin/env python3
# simple_stream_test.py

import os
from dashscope import Application

def main():
    # 配置信息
    api_key = os.getenv("DASHSCOPE_API_KEY") or "你的API密钥"
    app_id = os.getenv("DASHSCOPE_APP_ID") or "你的应用ID"
    
    # 调用智能体（流式输出）
    response = Application.call(
        api_key=api_key,
        app_id=app_id,
        prompt="你知道婚前的债务和财产在结婚后再离婚应该怎么划分吗,回答总结成30字左右",
        stream=True
    )
    
    print("流式输出开始:")
    full_text = ""
    
    for chunk in response:
        if chunk.status_code == 200:
            if hasattr(chunk.output, 'text'):
                text = chunk.output.text
                full_text += text
                print(text, end='', flush=True)
        else:
            print(f"\n错误: {chunk.message}")
            break
    
    print(f"\n\n完整回复: {full_text}")

if __name__ == "__main__":
    main()
