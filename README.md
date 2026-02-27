# 树莓派语音助手

基于树莓派5的开源中文语音助手，该系统结合本地Qwen2.5模型与Dify开源法律知识库，智能识别问题类型，提供精准回答。支持离线语音识别、语音合成、OLED屏幕实时显示和语音唤醒功能。模块化设计便于扩展，适用于家庭助理、教育学习和隐私敏感的智能交互场景。



**核心特性**：

- 智能任务分类：自动区分法律案例与通用问题
- 本地优先：Qwen2.5模型本地运行，保护隐私
- 离线语音：SenseVoice语音识别，无需云端
- 视觉反馈：OLED屏幕实时显示对话内容
- 模块化设计：各组件可独立替换升级



## 更新日志

### [2026/2/27]

将阿里云百炼平台提供的知识库应用服务，转换到本地服务器使用Dify开源平台部署的应用服务。

添加了OLED屏幕相关模块，用于展示每次用户与AI的对话。



### [2026/2/5]

- **接入百炼应用服务**：集成阿里百炼SDK，实现了多轮对话记忆功能
- **智能任务分类**：新增问题分类系统，自动区分法律案例、通用问题和其他专业知识
- **TTS流式输出**：重构语音合成模块，支持队列管理和伪流式语音输出



###   [2026/1/26]

- **ASR升级**：从Vosk离线识别改为SenseVoice识别服务，支持多语言自动识别
- **交互模式优化**：新增空格键录音控制，支持手动开始/停止录音
- **错误处理完善**：统一日志系统，优化音频缓冲区处理流程



## 硬件要求

- Raspberry Pi 5 
- 麦克风（USB麦克风，需支持16000HZ采样率）
- 音箱或耳机
- 至少4GB RAM

## 软件依赖

### 系统依赖
- Python 3.7+
- RASPi OS 64bit
- 中文语音包




## 环境配置步骤

### 1. 配置中文环境

```
# 1. 打开树莓派配置工具
sudo raspi-config

# 2. 选择 "Localisation Options" -> "Locale"
# 3. 在语言列表中找到 "zh_CN.UTF-8 UTF-8"，按空格键选中
# 4. 按回车确认，系统会开始配置中文环境
# 5. 完成后重启树莓派
sudo reboot

# 6. 安装中文输入法
sudo apt-get install -y fcitx-googlepinyin

# 7. 再次重启使输入法生效
sudo reboot
```



### 2. 安装系统依赖和对应Python包

```bash
sudo apt install espeak espeak-ng python3-pyaudio libasound2-dev
    
# 激活虚拟环境
source ~/your_venv/bin/activate

pip install -r requirements.txt
```



### 3. 安装和配置Ollama

```bash
# 方案一 树莓派上配置了代理，可以直接科学上网
# 安装Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 启动Ollama服务
ollama serve

# 在另一个终端中拉取Qwen2.5模型
ollama run qwen2.5:1.5b

# 方案二 树莓派上不能科学上网
# 在github上的ollama的release上找一个linux-arm64的版本
# 这里以0.13.5为例， https://github.com/ollama/ollama/releases/tag/v0.13.5
# 通过MobaXterm或者VNC放到树莓派中,直接解压

# 创建service配置文件
sudo nano /etc/systemd/system/ollama.service

```



在ollama.service中复制以下内容，保存退出：

```
[Unit]
Description=Ollama Service
After=network-online.target

[Service]
Type=simple
User=pi
Group=pi
Environment="HOME=/home/pi"
Environment="PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=/usr/local/bin/ollama serve
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```



使用systemd命令启动

```
# 重载systemd配置
sudo systemctl daemon-reload

# 启用开机自启
sudo systemctl enable ollama

# 启动ollama服务
sudo systemctl start ollama
```





### 4. Dify开源平台配置

Dify是一个开源LLM应用开发平台，本项目使用Dify来处理法律案例问答。系统会自动判断用户问题类型，如果是法律相关问题会转发到Dify应用进行处理。

#### 部署Dify服务

1. **安装Dify**（参考官方文档：https://docs.dify.ai/getting-started/install-self-hosted）
   ```bash
   # 使用Docker Compose安装（推荐）
   git clone https://github.com/langgenius/dify.git
   cd dify/docker
   docker compose up -d
   ```

2. **配置Dify应用**
   - 访问Dify控制台（默认地址：http://localhost）
   - 创建新的对话型应用
   - 配置知识库（上传法律文档）或使用工作流
   - 获取应用API密钥

#### 配置环境变量

在树莓派上设置Dify环境变量：

```bash
# 设置Dify API密钥
export DIFY_API_KEY="你的Dify应用API密钥"

# 添加到.bashrc文件永久生效
echo 'export DIFY_API_KEY="你的Dify应用API密钥"' >> ~/.bashrc


# 重新加载配置
source ~/.bashrc
```

#### 验证配置

启动程序时，系统会自动检查Dify服务连接。如果配置正确，会显示"DIFY服务检查通过"。

**注意**：如果不需要Dify服务或未配置环境变量，系统会自动回退到本地Qwen2.5模型处理所有问题。




## 使用方法

### 启动程序
```bash
# 确保在虚拟环境中
source ~/your_venv/bin/activate

cd ~/.../raspi5-qwen2.5/SenseVoice

# 启动API服务,第一次启动可能会自动下载SenseVoice模型的本体文件
python api.py

# 
# 运行主程序
cd ~/.../raspi5-qwen2.5/code
python main.py
```

### 交互方式

1. 程序启动后，会进行系统服务检查
2. 检查通过后，语音助手会提示"语音助手启动完成，随时为您服务"
3. 直接对麦克风说话即可开始对话
4. 说出唤醒词（默认："助手"、"你好"、"请问"、"帮助"）可以触发对话



### 配置说明

所有配置都在 `config.py` 文件中，主要配置参数如下：

#### AI模型配置
```python
AI_MODEL = "qwen2.5:0.5b"     # 本地Ollama模型
OLLAMA_URL = "http://127.0.0.1:11434/api/chat"  # Ollama服务地址
```

#### Dify服务配置
```python
DIFY_API_BASE_URL = "http://192.168.31.147:5001"  # Dify服务地址
DIFY_API_ENDPOINT = "/v1/chat-messages"           # Dify API端点
DIFY_API_KEY_ENV = "DIFY_API_KEY"                 # 环境变量名称
```

#### 语音识别配置
```python
SENSEVOICE_API_URL = "http://127.0.0.1:7860/api/v1/asr"  # SenseVoice服务地址
SAMPLE_RATE = 16000       # 音频采样率
```

#### OLED显示配置
```python
OLED_ENABLED = True                           # 是否启用OLED显示
OLED_WIDTH = 128                              # OLED屏幕宽度
OLED_HEIGHT = 64                              # OLED屏幕高度
OLED_FONT_SIZE = 10                           # 字体大小 (10px)
OLED_STARTUP_ANIMATION_DURATION = 2.0         # 开机动画持续时间(秒)
OLED_SHOW_BORDER = False                      # 是否显示完整边框
```

#### 唤醒词配置
```python
WAKE_WORDS = ["助手", "你好", "请问", "帮助"]  # 唤醒词列表
```

**注意**：百炼SDK已从项目中移除，法律案例问答现在由Dify开源平台处理。



## 故障排除

### 1.没有音源输出

可以在/home/你的用户名/目录下，新建.asoundrc文件，用于绑定树莓派的音源输入和输出。

```bash

sudo nano ~/.asoundrc

# 输入以下内容
# 默认播放设备   这里用的端口号是2，设备的端口号可以用arecord -l 和 aplay -l查看
pcm.!default {
    type plug
    slave {
        pcm "hw:2,0"
    }
}

# 默认录音设备
pcm.!dsnoop {
    type dsnoop
    ipc_key 1024
    slave {
        pcm "hw:2,0"
    }
}

# 默认控制设备
ctl.!default {
    type hw
    card 2
}

```



## API扩展

项目采用模块化设计，可以轻松替换或扩展：
- ASR模块：替换为其他语音识别引擎
- TTS模块：替换为其他语音合成引擎
- AI模块：替换为其他本地AI模型













