# -*- coding: utf-8 -*-
"""
日志工具模块
提供日志设置和标准错误重定向功能
"""

import os
import logging
import atexit

# 全局变量用于标准错误重定向
original_stderr_fd = None
devnull_fd = None


def setup_logging(log_name="app"):
    """
    设置Python日志
    
    Args:
        log_name: 日志文件名前缀，默认为'app'
    
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_dir, f'{log_name}.log'), encoding='utf-8'),
        ]
    )
    
    return logging.getLogger(log_name)


def setup_log_redirection(log_file_name='sensevoice_stderr.log'):
    """
    设置标准错误重定向到日志文件
    
    Args:
        log_file_name: 标准错误日志文件名
    
    Returns:
        bool: 是否成功设置重定向
    """
    global original_stderr_fd, devnull_fd
    
    try:
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 保存原始标准错误文件描述符
        original_stderr_fd = os.dup(2)
        
        # 打开日志文件用于写入
        log_file = os.path.join(log_dir, log_file_name)
        devnull_fd = os.open(log_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
        
        # 将标准错误重定向到日志文件
        os.dup2(devnull_fd, 2)
        
        # 注册退出时的清理函数
        atexit.register(restore_stderr)
        
        return True
    except Exception as e:
        logging.error(f"设置标准错误重定向失败: {e}")
        return False


def restore_stderr():
    """
    恢复标准错误输出
    """
    global original_stderr_fd, devnull_fd
    
    if original_stderr_fd is not None:
        try:
            os.dup2(original_stderr_fd, 2)
            os.close(original_stderr_fd)
            original_stderr_fd = None
        except Exception as e:
            print(f"恢复标准错误时出错: {e}")
    
    if devnull_fd is not None:
        try:
            os.close(devnull_fd)
            devnull_fd = None
        except Exception as e:
            print(f"关闭日志文件时出错: {e}")


def setup_module_logging(module_name):
    """
    为指定模块设置日志
    
    Args:
        module_name: 模块名称
    
    Returns:
        logging.Logger: 模块的日志记录器
    """
    return setup_logging(module_name)
