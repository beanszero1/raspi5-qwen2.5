#!/usr/bin/env python3
# new_agent_test.py

import os
import sys
from http import HTTPStatus
from dashscope import Application

class DashScopeAgentTester:
    """
    新版智能体应用测试类
    基于DashScope SDK调用新版智能体应用API
    """
    
    def __init__(self, api_key=None, app_id=None):
        """
        初始化测试器
        
        Args:
            api_key: DashScope API Key (可选，可从环境变量读取)
            app_id: 应用ID (必填)
        """
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        self.app_id = app_id
        
        if not self.api_key:
            print("错误: 未找到DASHSCOPE_API_KEY")
            print("请设置环境变量: export DASHSCOPE_API_KEY='your-api-key'")
            sys.exit(1)
            
        if not self.app_id:
            print("错误: 需要提供app_id参数")
            print("可以在应用管理的应用卡片上获取")
            sys.exit(1)
    
    def call_agent(self, prompt, stream=False, session_id=None):
        """
        调用智能体应用
        
        Args:
            prompt: 用户输入的命令/问题
            stream: 是否使用流式输出 (推荐True)
            session_id: 历史对话标识 (用于多轮对话)
            
        Returns:
            响应对象
        """
        try:
            # 构建调用参数
            call_params = {
                'api_key': self.api_key,
                'app_id': self.app_id,
                'prompt': prompt
            }
            
            # 可选参数
            if stream:
                call_params['stream'] = True
                
            if session_id:
                call_params['session_id'] = session_id
            
            print(f"📤 发送请求...")
            print(f"   应用ID: {self.app_id}")
            print(f"   输入内容: {prompt}")
            print(f"   流式输出: {'是' if stream else '否'}")
            if session_id:
                print(f"   会话ID: {session_id}")
            
            # 调用应用
            response = Application.call(**call_params)
            
            return response
            
        except Exception as e:
            print(f"调用失败: {e}")
            return None
    
    def test_single_turn(self):
        """测试单轮对话"""
        print("\n" + "="*50)
        print("测试1: 单轮对话 (非流式)")
        print("="*50)
        
        prompt = "你知道婚前的债务和财产在结婚后再离婚应该怎么划分吗,回答总结成30字左右"
        response = self.call_agent(prompt, stream=False)
        
        self._handle_response(response, "单轮对话")
    
    def _handle_response(self, response, test_name=""):
        """处理响应结果"""
        if not response:
            print(f"{test_name}: 响应为空")
            return
        
        print(f"状态码: {response.status_code}")
        print(f"请求ID: {response.request_id}")
        
        if response.status_code != HTTPStatus.OK:
            print(f"错误代码: {response.code if hasattr(response, 'code') else 'N/A'}")
            print(f"错误信息: {response.message if hasattr(response, 'message') else 'N/A'}")
            print("请参考文档: https://help.aliyun.com/alhmlw-studio/developer-reference/error-code")
        else:
            print(f"响应内容:")
            if hasattr(response.output, 'text'):
                print(response.output.text)
            else:
                print("输出格式未知，完整响应:")
                print(response)
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 DashScope 新版智能体应用测试")
        print("="*50)
        
        self.test_single_turn()



def main():
    """主函数"""
    
    # 方式1: 从环境变量读取配置（推荐）
    api_key = os.getenv("DASHSCOPE_API_KEY")
    app_id = os.getenv("DASHSCOPE_APP_ID")
    
    # 方式2: 如果环境变量未设置，可以在这里硬编码（仅用于测试）
    if not api_key or not app_id:
        print("⚠️  未找到环境变量，请手动输入:")
        api_key = input("请输入DASHSCOPE_API_KEY: ").strip()
        app_id = input("请输入应用ID (APP_ID): ").strip()
    
    # 创建测试器
    tester = DashScopeAgentTester(api_key=api_key, app_id=app_id)
    
    # 运行测试
    try:
        tester.run_all_tests()
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()