#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
百炼知识库检索接口测试脚本
使用阿里云百炼SDK调用retrieve接口访问知识库
"""



import os
import json
from alibabacloud_bailian20231229 import models as bailian_20231229_models
from alibabacloud_bailian20231229.client import Client as bailian20231229Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient


def check_environment_variables():
    """检查并提示设置必要的环境变量"""
    required_vars = {
        'ALIBABA_CLOUD_ACCESS_KEY_ID': '请输入你的ACCESS_KEYID',
        'ALIBABA_CLOUD_ACCESS_KEY_SECRET': '请输入你的ACCESS_KEY密钥',
        'WORKSPACE_ID': '请输入你的业务空间ID'
    }
    
    missing_vars = []
    for var, description in required_vars.items():
        if not os.environ.get(var):
            missing_vars.append(var)
            print(f"错误：请设置 {var} 环境变量 ({description})")
    
    return len(missing_vars) == 0

def create_client():
    """
    创建并配置客户端（Client）
    
    返回:
        bailian20231229Client: 配置好的客户端
    """
    config = open_api_models.Config(
        access_key_id=os.environ.get('ALIBABA_CLOUD_ACCESS_KEY_ID'),
        access_key_secret=os.environ.get('ALIBABA_CLOUD_ACCESS_KEY_SECRET')
    )
    # 下方接入地址以公有云的公网接入地址为例，可按需更换接入地址
    config.endpoint = 'bailian.cn-beijing.aliyuncs.com'
    return bailian20231229Client(config)

def retrieve_knowledge_base(client, workspace_id, index_id, query):
    """
    在指定的知识库中检索信息
    
    参数:
        client: 客户端实例
        workspace_id: 业务空间ID
        index_id: 知识库ID
        query: 检索query
        
    返回:
        检索结果
    """
    headers = {}
    retrieve_request = bailian_20231229_models.RetrieveRequest(
        index_id=index_id,
        query=query
    )
    runtime = util_models.RuntimeOptions()
    return client.retrieve_with_options(workspace_id, retrieve_request, headers, runtime)

def main():
    """主函数"""
    # 检查环境变量
    if not check_environment_variables():
        print("环境变量校验未通过，请先设置必要的环境变量")
        return
    
    try:
        print("步骤1：初始化Client")
        client = create_client()
        
        print("步骤2：检索知识库")
        
        # 从环境变量获取业务空间ID
        workspace_id = os.environ.get('WORKSPACE_ID')
        
        # 请替换为您的实际知识库ID
        # 知识库ID即 CreateIndex 接口返回的 Data.Id，您也可以在阿里云百炼控制台的知识库页面获取
        index_id = "vzoj5pzc3x"  # 请替换为实际的知识库ID
        
        # 请替换为您的实际检索query
        query = "智能马桶的使用方法"  # 请替换为实际的检索内容
        
        print(f"业务空间ID: {workspace_id}")
        print(f"知识库ID: {index_id}")
        print(f"检索query: {query}")
        
        # 执行检索
        resp = retrieve_knowledge_base(client, workspace_id, index_id, query)
        
        # 将响应转换为JSON字符串并打印
        result = UtilClient.to_jsonstring(resp.body)
        print("检索结果:")
        print(result)
        
        # 解析并格式化显示检索到的内容
        if resp.body and resp.body.data and resp.body.data.nodes:
            print("\n检索到的文本切片:")
            for i, node in enumerate(resp.body.data.nodes):
                print(f"\n--- 切片 {i+1} ---")
                print(f"相关度分数: {node.score}")
                print(f"内容: {node.text}")
                if hasattr(node, 'metadata') and node.metadata:
                    print(f"元数据: {json.dumps(node.metadata, ensure_ascii=False, indent=2)}")
        
        return result
        
    except Exception as e:
        print(f"发生错误：{e}")
        return None

if __name__ == '__main__':
    main()
