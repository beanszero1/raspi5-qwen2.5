# -*- coding: utf-8 -*-
"""
配置文件模块
包含常量配置和全局变量
"""

# --- 全局变量 ---
exit_flag = False

# --- ASR配置 ---
MODEL_PATH = "model"  # Vosk模型路径
SAMPLE_RATE = 16000  # 音频采样率
FRAMES_PER_BUFFER = 4000  # 音频缓冲区大小
CHANNELS = 1  # 音频通道数
FORMAT = "pyaudio.paInt16"  # 音频格式

# --- TTS配置 ---
TTS_RATE = 165  # 语音合成语速
TTS_VOLUME = 1.0  # 语音合成音量

# --- AI模型配置 ---
OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
OLLAMA_TAGS_URL = "http://127.0.0.1:11434/api/tags"
AI_MODEL = "qwen2.5:1.5b"  
AI_TIMEOUT = 15  # AI请求超时时间
SERVICE_CHECK_TIMEOUT = 5  # 服务检查超时时间

# --- 唤醒词配置 ---
WAKE_WORDS = ["助手", "你好", "请问", "帮助"]

# --- 系统提示词 ---
SYSTEM_PROMPT = """
你是一个智能语音助手小Q，运行在树莓派上。
请跳过思考，直接回答。
回答要简洁，控制在10~25字之内。
你是离线运行的语音助手。
"""

# --- 音频处理配置 ---
MIN_TEXT_LENGTH = 2  # 最小文本长度
MIN_NON_WAKE_TEXT_LENGTH = 3  # 非唤醒词的最小文本长度

