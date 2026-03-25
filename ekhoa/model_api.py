# -*- coding: utf-8 -*-
"""
AI模型API模块
通过Ollama与模型进行交互，集成DIFY API调用
"""

import os
import requests
import config

# 添加utils目录到Python路径
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'utils'))
import timing_utils

# 改用本地llama.cpp
# _dify_conversation_id = None


def classify_query(text):
    """
    使用qwen3对用户问题进行分类
    Returns: "法律案例", "通用问题", "其他专业知识" 或分类失败时的默认值
    """
    try:
        response = requests.post(config.OLLAMA_URL, json={
            "model": config.AI_MODEL,
            "messages": [
                {'role': 'system', 'content': config.CLASSIFICATION_PROMPT},
                {'role': 'user', 'content': text}
            ],
            "stream": False,
            "think": False
        }, timeout=config.AI_TIMEOUT)
        
        if response.status_code == 200:
            result = response.json()
            classification = result['message']['content'].strip()
            
            # 简化分类结果
            if "法律案例" in classification:
                return "法律案例"
            elif "通用问题" in classification:
                return "通用问题"
            elif "其他专业知识" in classification:
                return "其他专业知识"
            else:
                # 如果没有明确分类，默认作为通用问题处理
                return "通用问题"
        else:
            return "通用问题"  # 分类失败时默认处理为通用问题
            
    except Exception as e:
        # 分类失败时默认处理为通用问题
        return "通用问题"




def ask_ai_general(text):
    """
    处理所有问题（使用llama.cpp OpenAI兼容API）
    """
    # 记录AI思考开始时间戳
    timing_utils.record_timestamp("ai_start")
    
    try:
        # 使用llama.cpp OpenAI兼容API
        response = requests.post(config.LLAMACPP_API_URL, json={
            "model": config.AI_MODEL,  # 使用现有模型配置
            "messages": [
                {'role': 'system', 'content': config.SYSTEM_PROMPT},
                {'role': 'user', 'content': text}
            ],
            "stream": False,
            "max_tokens": 500,
            "temperature": 0.7
        }, timeout=config.AI_TIMEOUT)
        
        if response.status_code == 200:
            result = response.json()
            # OpenAI兼容API格式
            if "choices" in result and len(result["choices"]) > 0:
                reply = result["choices"][0]["message"]["content"].strip()
                # 记录AI回答生成完成时间戳
                timing_utils.record_timestamp("ai_complete")
                return reply
            else:
                # 即使格式异常也记录完成时间戳
                timing_utils.record_timestamp("ai_complete")
                return "抱歉，AI服务返回格式异常"
        else:
            # 即使服务不可用也记录完成时间戳
            timing_utils.record_timestamp("ai_complete")
            return "抱歉，AI服务暂时不可用"
            
    except requests.exceptions.ConnectionError:
        # 异常情况下也记录完成时间戳
        timing_utils.record_timestamp("ai_complete")
        return "无法连接到AI服务，请检查llama.cpp是否启动（127.0.0.1:8080）"
    except requests.exceptions.Timeout:
        timing_utils.record_timestamp("ai_complete")
        return "AI响应超时，请稍后再试"
    except Exception as e:
        timing_utils.record_timestamp("ai_complete")
        return f"处理请求时出现错误: {str(e)}"


def ask_ai(text, use_stream_callback=None, conversation_history=None):
    """
    主AI问答函数，保持向后兼容
    新增use_stream_callback参数用于流式处理回调
    新增conversation_history参数用于对话记忆
    
    Args:
        text: 用户输入的文本
        use_stream_callback: 可选回调函数，用于流式处理文本片段
        conversation_history: 可选，对话历史列表（保留参数，用于兼容性）
        
    Returns:
        如果使用回调函数则返回None，否则返回完整回复文本
        恢复原有行为：使用回调时不返回文本，避免重复输出
    """
    # 不再进行分类，直接使用llama.cpp处理所有问题
    reply = ask_ai_general(text)
    
    # 如果提供了回调函数，调用它并返回None
    if use_stream_callback is not None:
        if reply:
            # 在播放前打印计时摘要（不考虑TTS合成与播放的延迟）
            timing_utils.print_timing_summary()
            use_stream_callback(reply)
        return None
    else:
        return reply
