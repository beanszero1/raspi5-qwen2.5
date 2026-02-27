#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DIFY API集成测试脚本
测试model_api.py中的DIFY API调用功能
"""

import os
import sys
import config
from model_api import ask_ai_dify_stream, reset_dify_session, classify_query

def test_classification():
    """测试问题分类功能"""
    print("测试问题分类功能...")
    
    test_cases = [
        ("邻居半夜放音乐扰民，我该怎么办？", "法律案例"),
        ("今天天气怎么样？", "通用问题"),
        ("如何治疗感冒？", "其他专业知识"),
    ]
    
    for text, expected in test_cases:
        result = classify_query(text)
        print(f"问题: '{text}'")
        print(f"预期: {expected}, 实际: {result}")
        print(f"结果: {'通过' if expected in result else '失败'}")
        print()

def test_dify_api():
    """测试DIFY API调用功能"""
    print("测试DIFY API调用功能...")
    
    # 检查环境变量
    api_key = os.getenv(config.DIFY_API_KEY_ENV)
    if not api_key:
        print(f"警告: 环境变量 {config.DIFY_API_KEY_ENV} 未设置")
        print("请先设置环境变量: export DIFY_API_KEY='您的API密钥'")
        return False
    
    print(f"环境变量 {config.DIFY_API_KEY_ENV} 已设置")
    print(f"DIFY API URL: {config.DIFY_API_BASE_URL}{config.DIFY_API_ENDPOINT}")
    
    # 重置会话
    reset_dify_session()
    
    # 测试简单问题
    test_question = "你好，请介绍一下你自己"
    print(f"测试问题: '{test_question}'")
    
    try:
        # 调用DIFY API
        responses = list(ask_ai_dify_stream(test_question))
        
        if responses:
            response_text = " ".join(responses).strip()
            print(f"DIFY API响应: {response_text}")
            
            if "错误" in response_text:
                print("测试失败: API返回错误")
                return False
            elif "DIFY API无返回结果" in response_text:
                print("测试失败: API无返回结果")
                return False
            else:
                print("测试成功: API调用正常")
                return True
        else:
            print("测试失败: 无响应")
            return False
            
    except Exception as e:
        print(f"测试异常: {e}")
        return False

def test_ask_ai_function():
    """测试主ask_ai函数"""
    print("测试主ask_ai函数...")
    
    # 测试法律案例（应该调用DIFY）
    legal_question = "交通事故责任如何划分？"
    print(f"测试法律案例问题: '{legal_question}'")
    
    response = ask_ai_dify_stream(legal_question)
    for sentence in response:
        print(f"DIFY响应: {sentence}")
    
    # 测试通用问题（应该调用本地Qwen2.5）
    general_question = "今天天气怎么样？"
    print(f"测试通用问题: '{general_question}'")
    
    from model_api import ask_ai_general
    response = ask_ai_general(general_question)
    print(f"本地Qwen2.5响应: {response}")
    
    return True

def main():
    """主测试函数"""
    print("开始DIFY API集成测试")
    print("=" * 50)
    
    # 测试配置
    print("检查配置...")
    print(f"DIFY_API_BASE_URL: {config.DIFY_API_BASE_URL}")
    print(f"DIFY_API_ENDPOINT: {config.DIFY_API_ENDPOINT}")
    print(f"DIFY_API_KEY_ENV: {config.DIFY_API_KEY_ENV}")
    print(f"DIFY_RESPONSE_MODE: {config.DIFY_RESPONSE_MODE}")
    print()
    
    # 运行测试
    test_results = []
    
    # 测试分类功能
    test_results.append(("问题分类", test_classification()))
    
    # 测试DIFY API（需要环境变量）
    print("\n" + "=" * 50)
    test_results.append(("DIFY API调用", test_dify_api()))
    
    # 测试主函数
    print("\n" + "=" * 50)
    test_results.append(("主ask_ai函数", test_ask_ai_function()))
    
    # 输出测试结果
    print("\n" + "=" * 50)
    print("测试结果汇总:")
    print("=" * 50)
    
    all_passed = True
    for test_name, passed in test_results:
        status = "通过" if passed else "失败"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("所有测试通过！DIFY API集成成功。")
        print("\n使用说明:")
        print("1. 确保DIFY服务运行在 http://localhost:5001")
        print("2. 设置环境变量: export DIFY_API_KEY='您的API密钥'")
        print("3. 运行主程序: python main.py")
    else:
        print("部分测试失败，请检查配置和环境。")
        
    return all_passed

if __name__ == "__main__":
    # 添加当前目录到Python路径
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    success = main()
    sys.exit(0 if success else 1)