# -*- coding: utf-8 -*-
"""
计时工具模块
提供语音助手各阶段的时间戳记录和统计功能
"""

import time
import threading
import config

# 全局输出锁，用于确保计时摘要输出不与其他输出交错
_output_lock = threading.RLock()

def record_timestamp(event_name):
    """
    记录指定事件的时间戳
    
    Args:
        event_name: 事件名称，对应config.timing_data中的键
    """
    if not config.TIMING_ENABLED:
        return
    
    if event_name in config.timing_data:
        config.timing_data[event_name] = time.perf_counter()
        # print(f"[TIMING] {event_name}: {config.timing_data[event_name]:.2f}s")  # 调试用
    else:
        print(f"警告: 未知计时事件: {event_name}")


def calculate_duration(start_event, end_event):
    """
    计算两个事件之间的时间差（秒）
    
    Args:
        start_event: 开始事件名称
        end_event: 结束事件名称
        
    Returns:
        float: 时间差（秒），精确到0.01秒
    """
    if not config.TIMING_ENABLED:
        return 0.0
    
    if start_event in config.timing_data and end_event in config.timing_data:
        start_time = config.timing_data[start_event]
        end_time = config.timing_data[end_event]
        
        if start_time > 0 and end_time > 0:
            duration = end_time - start_time
            return round(duration, 2)  # 保留2位小数
        else:
            return 0.0
    else:
        print(f"警告: 无法计算 {start_event} 到 {end_event} 的时长")
        return 0.0


def reset_timing_data():
    """重置所有计时数据"""
    if not config.TIMING_ENABLED:
        return
    
    for key in config.timing_data:
        config.timing_data[key] = 0.0
    # print("[TIMING] 计时数据已重置")  # 调试用


def format_timing_summary():
    """
    生成格式化的计时摘要
    
    Returns:
        str: 格式化的计时摘要字符串
    """
    if not config.TIMING_ENABLED:
        return "计时功能已禁用"
    
    # 计算各阶段时长
    recording_duration = calculate_duration("start_recording", "end_recording")
    asr_duration = calculate_duration("end_recording", "asr_complete")
    ai_thinking_duration = calculate_duration("ai_start", "ai_complete")
    tts_synthesis_duration = calculate_duration("ai_complete", "tts_start")
    tts_playback_duration = calculate_duration("tts_start", "tts_playback_start")
    
    # 格式化时间戳（相对时间）
    start_recording_time = config.timing_data.get("start_recording", 0)
    if start_recording_time > 0:
        base_time = start_recording_time
    else:
        base_time = 0
    
    # 生成摘要
    summary_lines = []
    
    # 时间戳部分
    if config.timing_data["start_recording"] > 0:
        summary_lines.append(f"开始录音: {config.timing_data['start_recording'] - base_time:.2f}s")
    
    if config.timing_data["end_recording"] > 0:
        summary_lines.append(f"录音结束: {config.timing_data['end_recording'] - base_time:.2f}s")
    
    if config.timing_data["asr_complete"] > 0:
        summary_lines.append(f"语音识别完成: {config.timing_data['asr_complete'] - base_time:.2f}s")
    
    if config.timing_data["ai_start"] > 0 and config.timing_data["ai_complete"] > 0:
        summary_lines.append(f"AI回答生成完成: {config.timing_data['ai_complete'] - base_time:.2f}s")
    
    if config.timing_data["tts_start"] > 0:
        summary_lines.append(f"语音合成开始: {config.timing_data['tts_start'] - base_time:.2f}s")
    
    if config.timing_data["tts_playback_start"] > 0:
        summary_lines.append(f"语音播放开始: {config.timing_data['tts_playback_start'] - base_time:.2f}s")
    
    # 空行分隔
    if summary_lines:
        summary_lines.append("")
    
    # 时长统计部分
    stats_lines = []
    
    if recording_duration > 0:
        stats_lines.append(f"- 录音时长: {recording_duration:.2f}s")
    
    if asr_duration > 0:
        stats_lines.append(f"- ASR处理: {asr_duration:.2f}s")
    
    if ai_thinking_duration > 0:
        stats_lines.append(f"- AI思考: {ai_thinking_duration:.2f}s")
    
    if tts_synthesis_duration > 0:
        stats_lines.append(f"- TTS合成: {tts_synthesis_duration:.2f}s")
    
    if tts_playback_duration > 0:
        stats_lines.append(f"- TTS播放: {tts_playback_duration:.2f}s")
    
    # 计算总时长
    if (config.timing_data["start_recording"] > 0 and 
        config.timing_data["tts_playback_start"] > 0):
        total_duration = config.timing_data["tts_playback_start"] - config.timing_data["start_recording"]
        stats_lines.append(f"- 总耗时: {total_duration:.2f}s")
    
    if stats_lines:
        summary_lines.append("时间统计:")
        summary_lines.extend(stats_lines)
    
    return "\n".join(summary_lines)

def print_timing_summary():
    """打印计时摘要到控制台"""
    if not config.TIMING_ENABLED:
        return
    
    summary = format_timing_summary()
    if summary and summary != "计时功能已禁用":
        # 使用模块级别的锁确保输出不与其他线程交错
        with _output_lock:
            _print_summary_internal(summary)

def _print_summary_internal(summary):
    """内部函数：实际打印计时摘要"""
    import sys
    # 使用一个缓冲区收集所有输出，然后一次性写入
    output_lines = []
    output_lines.append("")  # 先换行
    output_lines.append("=" * 40)
    output_lines.append("计时摘要:")
    output_lines.append("=" * 40)
    
    # 添加summary的每一行
    lines = summary.split('\n')
    for line in lines:
        if line.strip():  # 只打印非空行
            output_lines.append(line)
    
    output_lines.append("=" * 40)
    output_lines.append("")  # 最后再加一个空行分隔
    
    # 一次性输出所有行，确保每行都刷新
    for line in output_lines:
        sys.stdout.write(line + '\r\n')  # 修改为使用\r\n作为换行符，与控制台输入处理一致
        sys.stdout.flush()
    
    # 额外刷新一次，确保所有输出都被写入
    sys.stdout.flush()

def get_timing_data():
    """获取当前计时数据副本"""
    return config.timing_data.copy() if config.TIMING_ENABLED else {}