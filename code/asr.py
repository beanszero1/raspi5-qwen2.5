# -*- coding: utf-8 -*-
"""
语音识别模块 (ASR)
使用 SenseVoice FastAPI 进行在线语音识别
树莓派录音，调用本机SenseVoice FastAPI服务
"""

import os
import json
import time
import wave
import pyaudio
import tts
import requests
import sys
from ctypes import *
import config

# 添加utils目录到Python路径，以便导入子目录中的模块
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'utils'))
import logging_utils

# 设置日志
logger = logging_utils.setup_module_logging("asr")

# 全局变量
p = None
stream = None


def _init_asr():
    """初始化语音识别（麦克风）"""
    global p, stream
    
    if p is not None and stream is not None:
        return
    
    # 使用全局logger
    logger.info("开始初始化ASR模块（SenseVoice FastAPI）")
    
    # 设置标准错误重定向
    logging_utils.setup_log_redirection('sensevoice_stderr.log')
    
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
            logger.warning(f"ALSA错误处理设置失败: {e}")

        print("正在初始化麦克风...", flush=True)
        logger.info("开始初始化麦克风")
        
        # 初始化麦克风
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
        
        logger.info("麦克风初始化完成")
        
    except Exception as e:
        logger.error(f"ASR初始化失败: {e}")
        logging_utils.restore_stderr()
        raise e
    finally:
        logging_utils.restore_stderr()
    
    # 确保在新行开始输出助手消息
    # 输出回车换行，确保光标在新行开始
    sys.stdout.write('\r\n')
    sys.stdout.flush()
    tts.speak("您好，有什么可以为您服务的吗")


def cleanup_asr():
    """清理语音识别资源"""
    global stream, p
    logger.info("开始清理ASR资源")
    
    if stream:
        try:
            stream.stop_stream()
            stream.close()
            logger.debug("音频流已关闭")
        except Exception as e:
            logger.warning(f"关闭音频流时出错: {e}")
    
    if p:
        try:
            p.terminate()
            logger.debug("PyAudio已终止")
        except Exception as e:
            logger.warning(f"终止PyAudio时出错: {e}")
    
    logger.info("ASR资源清理完成")


def get_audio_data():
    """获取音频数据"""
    global stream
    if stream is None:
        _init_asr()
    
    try:
        data = stream.read(config.FRAMES_PER_BUFFER, exception_on_overflow=False)
        return data
    except Exception as e:
        logger.error(f"获取音频数据时出错: {e}")
        # 尝试重新初始化
        cleanup_asr()
        _init_asr()
        return b""


def reset_recognizer():
    """重置识别器，开始新的录音会话（为兼容性保留）"""
    logger.info("识别器重置（SenseVoice API不需要重置）")


def recognize_audio(data):
    """
    实时识别音频数据（为兼容性保留，但SenseVoice API不支持实时流式识别）
    此函数将数据累积到缓冲区，实际识别由recognize_buffer完成
    """
    # 这里不做实际识别，因为SenseVoice API需要整个音频文件
    # 原项目已改为使用录音缓冲区，所以这里返回空字符串
    return ""


def recognize_buffer(audio_buffer):
    """
    处理整个录音缓冲区的数据，返回识别文本
    将音频缓冲区保存为WAV文件，然后调用SenseVoice FastAPI进行识别
    参考test_API_sucessfulVersion.py的调用格式
    """
    # 检查缓冲区长度
    if len(audio_buffer) == 0:
        logger.debug("音频缓冲区为空")
        return ""
    
    # 计算录音时长（秒）
    duration = len(audio_buffer) / (config.SAMPLE_RATE * 2)  # 每秒字节数 = 采样率 * 2（16位）
    logger.debug(f"音频缓冲区长度: {len(audio_buffer)} 字节, 时长: {duration:.2f} 秒")
    
    # 如果录音太短，直接返回空
    if duration < 0.3:
        logger.debug("录音时长太短，小于0.3秒")
        return ""
    
    # 保存音频缓冲区为WAV文件
    try:
        # 确保wav文件夹存在
        wav_dir = os.path.join(os.path.dirname(__file__), "wav")
        if not os.path.exists(wav_dir):
            os.makedirs(wav_dir)
            logger.debug(f"创建wav文件夹: {wav_dir}")
        
        wav_filename = f"recording_{int(time.time())}.wav"
        wav_path = os.path.join(wav_dir, wav_filename)
        
        with wave.open(wav_path, 'wb') as wav_file:
            wav_file.setnchannels(config.CHANNELS)
            wav_file.setsampwidth(2)  # 16位=2字节
            wav_file.setframerate(config.SAMPLE_RATE)
            wav_file.writeframes(bytes(audio_buffer))
        
        logger.debug(f"音频缓冲区已保存为: {wav_path}")
        
        # 调用SenseVoice FastAPI进行识别
        logger.debug("调用SenseVoice FastAPI进行识别...")
        logger.info(f"调用SenseVoice FastAPI识别文件: {wav_path}")
        
        # 按照test_API_sucessfulVersion.py的格式构造请求
        files = [
            ('files', (wav_filename, open(wav_path, 'rb'), 'audio/wav'))
        ]
        
        data = {
            'keys': 'audio1',  # 固定为audio1，对应files中的文件名
            'lang': config.SENSEVOICE_LANGUAGE
        }
        
        try:
            response = requests.post(
                config.SENSEVOICE_API_URL, 
                files=files, 
                data=data, 
                timeout=config.SENSEVOICE_TIMEOUT
            )
            
            # 清理WAV文件（可选，调试时可保留）
            # os.remove(wav_path)
            
            if response.status_code == 200:
                result = response.json()
                logger.debug(f"API返回原始结果: {result}")
                
                # 根据FastAPI返回格式，提取识别文本
                # API返回格式可能是列表: [{'key': 'audio1', 'text': '识别文本', ...}]
                # 也可能是字典: {'result': [{'key': 'audio1', 'text': '识别文本', ...}]}
                text = ""
                
                # 首先检查是否为列表
                if isinstance(result, list) and len(result) > 0:
                    first_item = result[0]
                    if isinstance(first_item, dict):
                        # 优先使用clean_text，如果没有则使用text
                        text = first_item.get('clean_text') or first_item.get('text')
                        # 如果text为空，则返回空字符串
                        if not text:
                            return ""
                
                # 如果不是列表，检查是否为字典且包含result字段
                elif isinstance(result, dict) and 'result' in result:
                    result_list = result['result']
                    if isinstance(result_list, list) and len(result_list) > 0:
                        first_item = result_list[0]
                        if isinstance(first_item, dict):
                            # 优先使用clean_text，如果没有则使用text
                            text = first_item.get('clean_text') or first_item.get('text')
                            # 如果text为空，则返回空字符串
                            if not text:
                                return ""
                
                # 如果上述提取失败，尝试其他方式
                if not text:
                    # 如果result是字典，尝试从其他字段提取
                    if isinstance(result, dict):
                        # 尝试从可能的字段中提取文本
                        text_fields = ['text', 'result', 'transcription', 'asr_result']
                        for field in text_fields:
                            if field in result:
                                text = result[field]
                                break
                    elif isinstance(result, str):
                        text = result
                    else:
                        # 其他情况，转换为字符串，但如果是列表或字典，我们期望上面已经处理了
                        # 这里防止意外情况，但尽量不输出整个JSON
                        if isinstance(result, (list, dict)):
                            # 对于复杂结构，返回空字符串而不是整个结构
                            return ""
                        else:
                            text = str(result)
                
                # 确保text是字符串类型
                if not isinstance(text, str):
                    logger.warning(f"text不是字符串，类型为 {type(text)}，值: {text}")
                    text = str(text)
                
                # 去除首尾空白字符
                text = text.strip()
                
                if text:
                    logger.info(f"识别结果: '{text}'")
                    return text
                else:
                    logger.debug("SenseVoice识别结果为空")
                    return ""
            else:
                logger.error(f"SenseVoice FastAPI返回错误: {response.status_code} - {response.text}")
                return ""
                
        except Exception as e:
            logger.error(f"SenseVoice FastAPI调用失败: {e}")
            return ""
        finally:
            # 确保关闭文件
            for file_tuple in files:
                if hasattr(file_tuple[1][1], 'close'):
                    try:
                        file_tuple[1][1].close()
                    except:
                        pass
        
    except Exception as e:
        logger.error(f"处理录音缓冲区时出错: {e}")
        return ""


