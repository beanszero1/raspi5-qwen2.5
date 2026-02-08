## 操作流程

在使用脚本前，需要设置以下环境变量：

```bash
# Linux/Mac
export ALIBABA_CLOUD_ACCESS_KEY_ID='您的阿里云访问密钥ID'
export ALIBABA_CLOUD_ACCESS_KEY_SECRET='您的阿里云访问密钥密码'
export WORKSPACE_ID='您的阿里云百炼业务空间ID'

# 注意这个DASHSCOPE与百炼实际上是阿里的两个平台
# https://dashscope.console.aliyun.com/apiKey
export DASHSCOPE_APP_ID="你的应用ID"
export DASHSCOPE_API_KEY="你的API密钥"

```

其中WORKSPACE_ID可以在左下角的“业务空间详情“查看。



ALIBABA_CLOUD_ACCESS_KEY_ID和SECRET需要在RAM控制台中配置。



需要在左下角的“业务空间”上方的权限管理中，添加你的RAM角色。

如果是个人项目也可以用主用户角色。



```
#nano ~/.bashrc
#添加到.bashrc文件的末尾,在百炼平台找到相应参数

export ALIBABA_CLOUD_ACCESS_KEY_ID='xxxxxxxxxxxxxxx'
export ALIBABA_CLOUD_ACCESS_KEY_SECRET='xxxxxxxxxxxxxxx'
export WORKSPACE_ID='xxxxxxxx'

#source ~/.bashrc
```

 

### 智能体应用参考文档

[大模型服务平台百炼控制台](https://bailian.console.aliyun.com/cn-beijing/?tab=api#/api/?type=app&url=3003869)

test_app.py用于调试智能体应用，需要在阿里云百炼平台的应用管理上发布后，具有应用ID才能调用。

test_SDK.py用来调试知识库，以SDK接口的方式。

建议配置后先用test文件测试一下接口是否正常使用再做后续开发
