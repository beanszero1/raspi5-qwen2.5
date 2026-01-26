# -*- coding: utf-8 -*-
"""
配置文件模块
包含常量配置和全局变量
"""

# --- 全局变量 ---
exit_flag = False
recording_flag = False  # 录音状态标志，空格键控制
audio_buffer = bytearray()  # 录音数据缓冲区
processing_pending = False  # 是否有待处理的录音缓冲区

# --- ASR配置 ---
# SenseVoice FastAPI 配置
SENSEVOICE_API_URL = "http://192.168.31.147:7860/api/v1/asr"  # FastAPI端点地址,这里可以改为本地主机部署了SenseVoice模型的IP,注意主机需运行api.py而不是webui.py
SENSEVOICE_LANGUAGE = "auto"  # 识别语言：auto, zh, en, yue, ja, ko, nospeech
SENSEVOICE_TIMEOUT = 30  # API请求超时时间（秒）

# 保留原有音频参数（用于录音）
SAMPLE_RATE = 16000  # 音频采样率
FRAMES_PER_BUFFER = 4000  # 音频缓冲区大小
CHANNELS = 1  # 音频通道数
FORMAT = "pyaudio.paInt16"  # 音频格式

# --- TTS配置 ---
TTS_RATE = 200  # 语音合成语速
TTS_VOLUME = 0.8  # 语音合成音量

# --- AI模型配置 ---
OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
OLLAMA_TAGS_URL = "http://127.0.0.1:11434/api/tags"
AI_MODEL = "qwen2.5-coder:0.5b"     
AI_TIMEOUT = 15  # AI请求超时时间
SERVICE_CHECK_TIMEOUT = 5  # 服务检查超时时间

# --- 唤醒词配置 ---
WAKE_WORDS = ["助手", "你好", "请问", "帮助"]

# --- 系统提示词 ---
SYSTEM_PROMPT = """
你是一个离线运行的智能语音助手小Q，运行在树莓派上。
请仔细理解用户的问题，然后给出有帮助的回答。
不要简单地重复用户的问题，要进行思考并提供有用的信息。
如果用户的问题不清楚，可以请求澄清。
回答要简洁，控制在15~30字之内。
"""

# --- 音频处理配置 ---
MIN_TEXT_LENGTH = 2  # 最小文本长度
MIN_NON_WAKE_TEXT_LENGTH = 3 # 非唤醒词的最小文本长度
