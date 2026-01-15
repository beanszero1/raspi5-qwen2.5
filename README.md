# 树莓派离线语音助手  Qwen2.5 + Vosk + pyttsx3

一个运行在树莓派5上的完全离线的中文语音助手系统，结合了本地AI模型、离线语音识别和语音合成技术。



## 项目概述

本项目实现了一个在树莓派上运行的智能语音助手，具有以下特点：
- **完全离线运行**：所有处理都在本地完成，无需网络连接
- **中文语音交互**：支持中文语音识别和语音合成
- **本地AI模型**：使用Qwen2.5:1.5b模型进行对话理解
- **轻量级设计**：针对树莓派等嵌入式设备性能选择轻量化方案

## 核心特性

-  **离线语音识别**：使用Vosk进行实时语音识别

-  **本地AI对话**：基于Qwen2.5:1.5b模型进行智能对话

-  **离线语音合成**：使用pyttsx3进行中文语音合成

-  **可配置唤醒词**：支持自定义唤醒词触发

  

## 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   麦克风输入      │───▶│   Vosk ASR      │───▶│    文本处理    │
│  (实时音频流)     │    │  (语音转文字)     │    │  (唤醒词检测)  │
└─────────────────┘    └─────────────────┘    └────────┬────────┘
                                                       │
┌─────────────────┐    ┌─────────────────┐    ┌───────▼────────┐
│   音箱输出       │◀──│  pyttsx3 TTS    │◀── │   Qwen2.5      │
│  (语音播放)      │    │                 │    │    思考 回答    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 硬件要求

- Raspberry Pi 5 
- 麦克风（USB麦克风，需支持16000HZ采样率）
- 音箱或耳机
- 至少4GB RAM（运行Qwen2.5:1.5b模型）

## 软件依赖

### 系统依赖
- Python 3.7+
- 中文语音包

### Python包依赖
所有Python依赖已列在 `requirements.txt` 文件中。推荐使用以下命令安装：

```bash
pip install -r requirements.txt
```





## 安装步骤

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



### 4. 下载Vosk中文模型

```bash
# 创建模型目录
mkdir -p model

# 下载中文模型（42M）
# 从 https://alphacephei.com/vosk/models 手动下载，通过MobaXterm或者VNC放到树莓派中
# 解压到 model/ 目录
unzip vosk-model-cn-0.22.zip -d ~/../your_proj/model/
```

## 项目结构

```
.
├── README.md                    # 项目说明文档
├── LICENSE                      # Apache 2.0许可证
├── requirements.txt             # Python依赖包列表
├── config.py                    # 配置文件
├── main.py                      # 主程序入口
├── asr.py                       # 语音识别模块（Vosk）
├── tts.py                       # 语音合成模块（pyttsx3）
├── model_api.py                 # AI模型交互模块（Qwen2.5）
└── keyboard_listener.py         # 键盘监听模块
```

## 使用方法

### 启动程序
```bash
# 确保在虚拟环境中
source ~/your_venv/bin/activate

# 运行主程序
python main.py
```

### 交互方式
1. 程序启动后，会进行系统服务检查
2. 检查通过后，语音助手会提示"语音助手启动完成，随时为您服务"
3. 直接对麦克风说话即可开始对话
4. 说出唤醒词（默认："助手"、"你好"、"请问"、"帮助"）可以触发对话



### 配置说明

所有配置都在 `config.py` 文件中，可以修改以下参数：

```python
# AI模型配置
AI_MODEL = "qwen2.5:1.5b"  # 可以改为其他Ollama支持且已部署在本地的模型

# 语音识别配置
MODEL_PATH = "model"  
SAMPLE_RATE = 16000   # 音频采样率

# 语音合成配置
TTS_RATE = 180       
TTS_VOLUME = 0.8      

# 唤醒词配置
WAKE_WORDS = ["助手", "你好", "请问", "帮助"]

# 系统提示词
SYSTEM_PROMPT = """你是一个智能语音助手小Q..."""
```



## 故障排除

### 常见问题

1. 没有音源输出

   可以通过可以把.asoundrc文件放到/home/你的用户名/，用于绑定树莓派的音源输入和输出。



### API扩展
项目采用模块化设计，可以轻松替换或扩展：
- ASR模块：替换为其他语音识别引擎
- TTS模块：替换为其他语音合成引擎
- AI模块：替换为其他本地AI模型



