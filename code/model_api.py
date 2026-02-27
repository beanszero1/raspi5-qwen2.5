# -*- coding: utf-8 -*-
"""
AI模型API模块
通过Ollama与模型进行交互，集成百炼SDK流式调用
"""

import os
import requests
import config

try:
    from dashscope import Application
    from http import HTTPStatus
    DASHSCOPE_AVAILABLE = True
except ImportError:
    DASHSCOPE_AVAILABLE = False

# 百炼SDK会话管理
_bailian_session_id = None


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
            "stream": False
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


def ask_ai_bailian_stream(text, conversation_history=None):
    """
    使用百炼SDK进行非流式调用
    在用户问题后添加"将回答总结成30~50字左右"以缩短回答
    使用百炼SDK内置的session_id机制实现多轮对话记忆
    （conversation_history参数保留但不使用，仅用于兼容性）
    
    Args:
        text: 当前用户问题
        conversation_history: 保留参数，仅用于兼容性
        
    Returns: 生成器，只产生一个完整的回答文本
    """
    global _bailian_session_id
    
    if not DASHSCOPE_AVAILABLE:
        yield "错误：dashscope库未安装"
        return
        
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        yield "错误：环境变量DASHSCOPE_API_KEY未设置"
        return
        
    if not config.BAILIAN_APP_ID:
        yield "错误：百炼应用ID未配置"
        return
    
    try:
        # 构建prompt：在用户问题后添加总结要求
        prompt_with_summary = f"{text}。将回答总结成30~50字左右"
        
        # 非流式调用，使用session_id实现多轮对话
        response = Application.call(
            api_key=api_key,
            app_id=config.BAILIAN_APP_ID,
            prompt=prompt_with_summary,
            session_id=_bailian_session_id,  # 使用之前保存的session_id（如果有）
            stream=False  # 非流式
        )
        
        # 检查响应状态
        if response.status_code != HTTPStatus.OK:
            # 如果调用失败，重置session_id
            _bailian_session_id = None
            yield f"错误: {response.status_code} - {response.message}"
            return
        
        # 处理完整响应
        full_text = ""
        if hasattr(response.output, 'text'):
            full_text = response.output.text
        elif hasattr(response, 'output') and hasattr(response.output, 'choices'):
            # 备用方式获取文本
            full_text = response.output.choices[0].message.content if response.output.choices else ""
        
        # 更新session_id用于下一轮对话
        if hasattr(response.output, 'session_id') and response.output.session_id:
            _bailian_session_id = response.output.session_id
        
        if not full_text:
            yield "百炼SDK返回空响应"
            return
        
        # 清理文本：移除markdown格式，去除多余空白
        def clean_text(text):
            if not text:
                return text
            
            # 移除markdown粗体符号
            text = text.replace('**', '')
            text = text.replace('*', '')
            text = text.replace('__', '')
            
            # 移除其他markdown符号
            import re
            text = re.sub(r'#{1,6}\s+', '', text)  # 移除标题
            text = re.sub(r'`{1,3}(.*?)`{1,3}', r'\1', text)  # 移除代码块
            text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)  # 移除链接
            
            # 去除多余空白
            text = ' '.join(text.split())
            
            # 确保文本以合适的标点结束
            if text and text[-1] not in '。！？.!?':
                text += '。'
                
            return text
        
        cleaned_text = clean_text(full_text)
        
        # 返回完整文本（不分割句子）
        yield cleaned_text
            
    except Exception as e:
        # 发生异常时重置session_id
        _bailian_session_id = None
        yield f"百炼SDK调用失败: {str(e)}"


def reset_bailian_session():
    """
    重置百炼SDK会话
    用于开始新的对话或处理错误后重置
    """
    global _bailian_session_id
    _bailian_session_id = None
    return "百炼SDK会话已重置"


def ask_ai_general(text):
    """
    处理通用问题（使用原有qwen3逻辑）
    """
    try:
        # 尝试请求本地 LLM
        response = requests.post(config.OLLAMA_URL, json={
            "model": config.AI_MODEL,
            "messages": [
                {'role': 'system', 'content': config.SYSTEM_PROMPT},
                {'role': 'user', 'content': text}
            ],
            "stream": False
        }, timeout=config.AI_TIMEOUT)
        
        if response.status_code == 200:
            result = response.json()
            reply = result['message']['content'].strip()
            return reply
        else:
            return "抱歉，AI服务暂时不可用"
            
    except requests.exceptions.ConnectionError:
        return "无法连接到AI服务，请检查Ollama是否启动"
    except requests.exceptions.Timeout:
        return "AI响应超时，请稍后再试"
    except Exception as e:
        return f"处理请求时出现错误: {str(e)}"


def ask_ai(text, use_stream_callback=None, conversation_history=None):
    """
    主AI问答函数，保持向后兼容
    新增use_stream_callback参数用于流式处理回调
    新增conversation_history参数用于对话记忆
    
    Args:
        text: 用户输入的文本
        use_stream_callback: 可选回调函数，用于流式处理文本片段
        conversation_history: 可选，对话历史列表
        
    Returns:
        如果使用回调函数则返回None，否则返回完整回复文本
        恢复原有行为：使用回调时不返回文本，避免重复输出
    """
    # 1. 分类问题
    query_type = classify_query(text)
    
    # 2. 根据类型处理
    if query_type == "法律案例":
        # 收集所有文本（ask_ai_bailian_stream现在只返回一个完整文本）
        full_response = ""
        for sentence in ask_ai_bailian_stream(text, conversation_history):
            full_response += sentence + " "
        
        full_response = full_response.strip()
        if not full_response:
            full_response = "百炼SDK无返回结果"
        
        # 如果提供了回调函数，调用它并返回None（避免重复输出）
        if use_stream_callback is not None:
            # 无论是否有回复内容，只要使用了回调就返回None
            if full_response:
                use_stream_callback(full_response)
            return None
        else:
            # 没有回调，返回完整回复文本
            return full_response
            
    elif query_type == "通用问题":
        # 通用问题目前不支持历史
        reply = ask_ai_general(text)
        
        # 如果提供了回调函数，调用它并返回None
        if use_stream_callback is not None:
            if reply:
                use_stream_callback(reply)
            return None
        else:
            return reply
        
    else:  # "其他专业知识"
        reply = config.UNKNOWN_REPLY
        
        # 如果提供了回调函数，调用它并返回None
        if use_stream_callback is not None:
            if reply:
                use_stream_callback(reply)
            return None
        else:
            return reply
