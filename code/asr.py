# -*- coding: utf-8 -*-
"""
语音识别模块 (ASR)
使用 Vosk 进行离线语音识别
"""

import os
import json
import pyaudio
import tts
import logging
from vosk import Model, KaldiRecognizer
from ctypes import *
import config

# 全局变量
model = None
rec = None
p = None
stream = None
original_stderr_fd = None
devnull_fd = None


def setup_log_redirection():
    """设置标准错误重定向到日志文件"""
    global original_stderr_fd, devnull_fd
    

    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    

    original_stderr_fd = os.dup(2)  
    

    log_file = os.path.join(log_dir, 'vosk_stderr.log')
    devnull_fd = os.open(log_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
    

    os.dup2(devnull_fd, 2)



def restore_stderr():

    global original_stderr_fd, devnull_fd
    
    if original_stderr_fd is not None:
        os.dup2(original_stderr_fd, 2) 
        os.close(original_stderr_fd)
        original_stderr_fd = None
    
    if devnull_fd is not None:
        os.close(devnull_fd)
        devnull_fd = None


def setup_logging():

    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_dir, 'asr_python.log'), encoding='utf-8'),
        ]
    )


def _init_asr():
    """初始化语音识别）"""
    global model, rec, p, stream
    
    if model is not None:
        return
    
    # 设置Python日志
    setup_logging()
    logging.info("开始初始化ASR模块")
    
    # 检查模型是否存在
    if not os.path.exists(config.MODEL_PATH):
        error_msg = f"错误：找不到 '{config.MODEL_PATH}' 文件夹，请下载 Vosk 中文模型"
        logging.error(error_msg)
        print(error_msg)
        exit(1)

    setup_log_redirection()
    
    
    try:
        # 屏蔽 ALSA 冗余报错
        try:
            ERROR_HANDLER_FUNC = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)
            def py_error_handler(filename, line, function, err, fmt): 
                return
            c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)
            asound = cdll.LoadLibrary('libasound.so')
            asound.snd_lib_error_set_handler(c_error_handler)
        except Exception as e:
            logging.warning(f"ALSA错误处理设置失败: {e}")

        print("正在加载 Vosk 离线模型...")
        logging.info("开始加载Vosk模型")
        
        # 加载Vosk模型（此时所有stderr输出会被重定向到文件）
        model = Model(config.MODEL_PATH)
        rec = KaldiRecognizer(model, config.SAMPLE_RATE)
        p = pyaudio.PyAudio()

        # 打开麦克风流
        stream = p.open(
            format=pyaudio.paInt16,
            channels=config.CHANNELS,
            rate=config.SAMPLE_RATE,
            input=True,
            frames_per_buffer=config.FRAMES_PER_BUFFER,
            input_device_index=None,
            input_host_api_specific_stream_info=None
        )
        stream.start_stream()
        
        logging.info("Vosk模型加载完成")
        
    except Exception as e:
        logging.error(f"ASR初始化失败: {e}")
        restore_stderr()
        raise e
    finally:

        restore_stderr()
    
    tts.speak("初始化已完成，现在可以开始对话")

def cleanup_asr():
    """清理语音识别资源"""
    global stream, p
    logging.info("开始清理ASR资源")
    
    if stream:
        try:
            stream.stop_stream()
            stream.close()
            logging.debug("音频流已关闭")
        except Exception as e:
            logging.warning(f"关闭音频流时出错: {e}")
    
    if p:
        try:
            p.terminate()
            logging.debug("PyAudio已终止")
        except Exception as e:
            logging.warning(f"终止PyAudio时出错: {e}")
    
    logging.info("ASR资源清理完成")


def get_audio_data():
    """获取音频数据"""
    global stream
    if stream is None:
        _init_asr()
    
    try:
        data = stream.read(config.FRAMES_PER_BUFFER, exception_on_overflow=False)
        return data
    except Exception as e:
        logging.error(f"获取音频数据时出错: {e}")
        # 尝试重新初始化
        cleanup_asr()
        _init_asr()
        return b""



def recognize_audio(data):

    global rec
    if rec is None:
        _init_asr()
    
    try:
        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            text = result['text'].replace(" ", "")
            
            # 记录识别结果（调试用）
            if text:
                logging.debug(f"语音识别结果: '{text}'")
            
            return text
        
        return ""
    
    except Exception as e:
        logging.error(f"语音识别过程中出错: {e}")
        return ""


import atexit
atexit.register(restore_stderr)


if not os.path.exists("logs"):
    os.makedirs("logs")
