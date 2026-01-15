# -*- coding: utf-8 -*-
"""
语音合成模块 (TTS)
使用 pyttsx3 进行离线语音合成
"""

import pyttsx3

from config import TTS_RATE,TTS_VOLUME


# 全局变量
engine = None


def speak(text):
    """ 文字转语音输出 """
    global engine
    if engine is None:
        _init_engine()
    
    print(f"助手: {text}")
    try:
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"TTS 错误: {e}")



def _init_engine():

    global engine
    if engine is not None:
        return
    
    engine = pyttsx3.init()

    voices = engine.getProperty('voices')
    found_zh = False
    for v in voices:
        if 'zh' in v.id or 'chinese' in v.name.lower():
            engine.setProperty('voice', v.id)
            found_zh = True
            print(f"TTS 已切换中文: {v.id}")
            
            break

    if not found_zh:
        try:
            engine.setProperty('voice', 'zh')
        except:
            pass

    engine.setProperty('rate', TTS_RATE)  
    engine.setProperty('volume', TTS_VOLUME) 
    
