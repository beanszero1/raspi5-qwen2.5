## 操作流程

在使用脚本前，需要设置以下环境变量：

```bash
# Linux/Mac
export ALIBABA_CLOUD_ACCESS_KEY_ID='您的阿里云访问密钥ID'
export ALIBABA_CLOUD_ACCESS_KEY_SECRET='您的阿里云访问密钥密码'
export WORKSPACE_ID='您的阿里云百炼业务空间ID'

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

 

