#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pyttsx3语音测试工具
"""

import pyttsx3
import time
import sys

def main():
    print("开始测试pyttsx3...")
    
    try:
        # 初始化引擎
        engine = pyttsx3.init()
        print("✅ pyttsx3初始化成功")
        
        # 获取语音列表
        voices = engine.getProperty('voices')
        print(f"找到 {len(voices)} 个语音:")
        
        for i, voice in enumerate(voices):
            print(f"[{i}] {voice.name}")
        
        # 测试第一个语音
        if voices:
            engine.setProperty('voice', voices[0].id)
            engine.say("你好，这是测试语音")
            engine.runAndWait()
            print("✅ 语音测试完成")
        
    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    main()
