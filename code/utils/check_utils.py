# -*- coding: utf-8 -*-
"""
检查工具模块
提供系统服务检查功能
"""

import os
import requests
import logging_utils

import config

# 设置日志
logger = logging_utils.setup_module_logging("check_utils")


def check_sensevoice_service():
    """
    检查SenseVoice FastAPI服务是否可用
    
    Returns:
        tuple: (bool, str) 是否可用, 错误信息
    """
    try:
        # 尝试访问根路径或健康检查端点
        response = requests.get(config.SENSEVOICE_API_URL.replace('/api/v1/asr', '').rstrip('/'), timeout=5)
        # 接受200-399的状态码
        if 200 <= response.status_code < 400:
            return True, f"SenseVoice FastAPI服务在线 (HTTP {response.status_code})"
        else:
            return False, f"SenseVoice服务返回HTTP {response.status_code}"
    except Exception as e:
        return False, f"无法连接到SenseVoice FastAPI服务: {e}"


def check_ollama_service():
    """
    检查Ollama服务是否可用
    
    Returns:
        tuple: (bool, str, list) 是否可用, 错误信息, 可用模型列表
    """
    try:
        response = requests.get(config.OLLAMA_TAGS_URL, timeout=config.SERVICE_CHECK_TIMEOUT)
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [m['name'] for m in models]
            return True, "Ollama服务正常", model_names
        else:
            return False, f"Ollama服务返回HTTP {response.status_code}", []
    except Exception as e:
        return False, f"无法连接Ollama服务: {e}", []


def check_dify_service():
    """
    检查DIFY环境变量配置
    
    Returns:
        tuple: (bool, str) 是否可用, 错误信息
    """
    # 检查环境变量
    api_key = os.getenv(config.DIFY_API_KEY_ENV)
    if not api_key:
        return False, f"环境变量{config.DIFY_API_KEY_ENV}未设置，法律案例查询功能将不可用"
    
    return True, "DIFY配置正常"


def check_all_services():
    """
    检查所有所需服务是否可用
    
    Returns:
        bool: 所有服务是否可用
    """
    logger.info("开始检查系统服务...")
    
    print("检查SenseVoice服务...")
    # 检查SenseVoice服务
    sensevoice_ok, sensevoice_msg = check_sensevoice_service()
    if not sensevoice_ok:
        print(f"SenseVoice服务异常: {sensevoice_msg}")
        logger.error(f"SenseVoice服务异常: {sensevoice_msg}")
        return False
    print(f"SenseVoice服务正常")
    logger.info(f"SenseVoice服务正常")
    
    print("检查Ollama服务...")
    # 检查Ollama服务
    ollama_ok, ollama_msg, models = check_ollama_service()
    if not ollama_ok:
        print(f"Ollama服务异常: {ollama_msg}")
        logger.error(f"Ollama服务异常: {ollama_msg}")
        return False
    print(f"Ollama服务正常")
    logger.info(f"Ollama服务正常")
    
    if models:
        print(f"可用模型: {models}")
        logger.info(f"可用模型: {models}")
        # 检查是否有所需模型
        if config.AI_MODEL not in models:
            warning_msg = f"未找到配置的模型 '{config.AI_MODEL}'，将使用可用模型"
            print(f"警告: {warning_msg}")
            logger.warning(warning_msg)
    else:
        warning_msg = f"没有找到模型，请先拉取模型: ollama pull {config.AI_MODEL}"
        print(f"警告: {warning_msg}")
        logger.warning(warning_msg)
    
    print("检查DIFY配置...")
    # 检查DIFY配置
    dify_ok, dify_msg = check_dify_service()
    if not dify_ok:
        print(f"DIFY配置警告: {dify_msg}")
        logger.warning(f"DIFY配置警告: {dify_msg}")
        print("注意: 法律案例查询功能将不可用，但其他功能正常")
        logger.warning("法律案例查询功能将不可用，但其他功能正常")
    else:
        print(f"DIFY配置正常")
        logger.info(f"DIFY配置正常")
    
    return True
