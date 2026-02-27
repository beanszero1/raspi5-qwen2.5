#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OLED屏幕显示模块 - 改进版本
用于在0.96英寸OLED屏幕上显示对话内容
屏幕分辨率: 128x64像素
显示模式: 全屏单句显示，提高可读性
字体: 10px中文字体
"""

import os
import time
import sys

# 尝试导入PIL库（用于字体和图像处理）
try:
    from PIL import ImageFont, Image, ImageDraw
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("警告: Pillow库未安装，OLED将以模拟模式运行")
    print("安装命令: pip install pillow")

# 尝试导入luma库，如果不可用则提供模拟模式
try:
    from luma.core.interface.serial import i2c
    from luma.oled.device import ssd1306
    from luma.core.render import canvas
    OLED_AVAILABLE = True
except ImportError:
    OLED_AVAILABLE = False
    print("警告: luma.oled库未安装，OLED将以模拟模式运行")
    print("安装命令: pip install luma.oled")

# 添加utils目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'utils'))
import logging_utils

# 设置日志
logger = logging_utils.setup_module_logging("oled_display")

# 导入配置
import config

# OLED配置常量
OLED_WIDTH = config.OLED_WIDTH
OLED_HEIGHT = config.OLED_HEIGHT
OLED_FONT_SIZE = config.OLED_FONT_SIZE
OLED_LINE_HEIGHT = config.OLED_LINE_HEIGHT
OLED_STARTUP_ANIMATION_DURATION = config.OLED_STARTUP_ANIMATION_DURATION  # 开机动画持续时间

# 边框配置
OLED_SHOW_BORDER = getattr(config, 'OLED_SHOW_BORDER', False)  # 是否显示完整边框


def get_chinese_font(size=10):
    """
    获取中文字体，如果没有中文系统字体，则使用Pillow的默认字体
    参考simple_oled_test.py的实现
    返回一个可用于显示中文字符的字体对象
    """
    if not PIL_AVAILABLE:
        logger.warning("Pillow库未安装，无法加载字体")
        return None
    
    # 尝试加载系统可用的中文字体（按优先级排序）
    chinese_font_paths = [
        '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',  # 文泉驿微米黑
        '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',    # 文泉驿正黑
        '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',  # Droid字体
        '/usr/share/fonts/truetype/arphic/uming.ttc',      # AR PL UMing
        '/usr/share/fonts/truetype/arphic/ukai.ttc',       # AR PL UKai
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',  # Noto Sans CJK
    ]
    
    for font_path in chinese_font_paths:
        if os.path.exists(font_path):
            try:
                font = ImageFont.truetype(font_path, size)
                logger.info(f"已加载中文字体: {font_path} (大小: {size}px)")
                return font
            except Exception as e:
                logger.warning(f"字体加载失败 {font_path}: {e}")
                continue
    
    # 如果找不到中文字体，使用Pillow的默认字体
    logger.warning("未找到中文字体，使用Pillow默认字体")
    return ImageFont.load_default()


def wrap_text(text, font, max_width):
    """
    将文本按最大宽度换行
    返回换行后的文本列表
    """
    if not text:
        return []
    
    words = text
    lines = []
    current_line = ""
    
    # 中文字符处理：逐个字符添加
    for char in words:
        # 测试添加字符后的宽度
        test_line = current_line + char
        text_width = font.getlength(test_line)
        
        if text_width <= max_width:
            current_line = test_line
        else:
            # 当前行已满，保存并开始新行
            if current_line:
                lines.append(current_line)
            current_line = char
    
    # 添加最后一行
    if current_line:
        lines.append(current_line)
    
    return lines


class OLEDDisplay:
    """
    OLED显示管理类 - 改进版本
    支持开机动画和全屏单句显示
    """
    
    def __init__(self, simulate=False):
        """
        初始化OLED显示器
        Args:
            simulate: 是否使用模拟模式（用于测试）
        """
        logger.info(f"OLEDDisplay.__init__()开始，simulate={simulate}")
        self.simulate = simulate or not OLED_AVAILABLE
        self.device = None
        self.chinese_font = None
        self.default_font = None
        
        # 屏幕尺寸
        self.width = OLED_WIDTH
        self.height = OLED_HEIGHT
        
        # 字体大小
        self.font_size = OLED_FONT_SIZE
        self.line_height = OLED_LINE_HEIGHT
        
        # 显示模式控制
        self.current_display_text = ""  # 当前显示的文本
        self.current_display_lines = []  # 当前显示的文本行
        
        # 初始化
        self._init_display()
        
        logger.info("OLED显示模块初始化完成")
    
    def _init_display(self):
        """初始化OLED设备"""
        try:
            if not self.simulate:
                # 初始化真实OLED设备
                serial = i2c(port=1, address=0x3C)
                self.device = ssd1306(serial, width=self.width, height=self.height)
                logger.info("OLED硬件初始化成功")
            else:
                logger.info("OLED模拟模式启用")
            
            # 加载字体
            self.chinese_font = get_chinese_font(self.font_size)
            self.default_font = ImageFont.load_default()
            
            # 显示开机动画
            self.show_startup_animation()
            
        except Exception as e:
            logger.error(f"OLED初始化失败: {e}")
            self.simulate = True
            logger.info("已切换到模拟模式")
    
    def show_startup_animation(self):
        """
        显示丰富的开机动画
        持续约7.0秒，包含图形、大字体和系统信息
        """
        logger.info("显示丰富的开机动画...")
        

        self._display_title_screen()
        time.sleep(2.0)
        
        self._display_system_info()
        time.sleep(2.0)
        

        self._display_loading_animation()
        time.sleep(1.5)
        

        self._display_ready_state()

        
        logger.info("开机动画完成")
    
    def show_shutdown_animation(self):
        """
        显示关机动画,持续2秒
        """
        logger.info("显示关机动画...")
        
        self._display_shutdown_message()
        time.sleep(1.0)
        

        self._display_goodbye_message()
        time.sleep(1.5)
        
        logger.info("关机动画完成")
    
    def _display_shutdown_message(self):
        """显示正在退出消息"""
        with self._get_canvas() as draw:
            # 清屏
            draw.rectangle([0, 0, self.width-1, self.height-1], fill="black")
            
            # 显示"正在退出..."
            shutdown_text = "正在退出..."
            text_width = self.chinese_font.getlength(shutdown_text)
            
            # 垂直居中
            text_x = (self.width - text_width) // 2
            text_y = (self.height - self.line_height) // 2
            
            draw.text((text_x, text_y), shutdown_text, font=self.chinese_font, fill="white")
            
            # 底部显示提示
            hint_text = "语音助手"
            hint_font = get_chinese_font(10)
            hint_width = hint_font.getlength(hint_text)
            draw.text(((self.width - hint_width) // 2, self.height - 15), hint_text, font=hint_font, fill="white")
    
    def _display_goodbye_message(self):
        """显示再见消息"""
        with self._get_canvas() as draw:
            # 清屏
            draw.rectangle([0, 0, self.width-1, self.height-1], fill="black")
            
            # 显示"再见"
            goodbye_text = "再见"
            text_width = self.chinese_font.getlength(goodbye_text)
            
            # 垂直居中
            text_x = (self.width - text_width) // 2
            text_y = (self.height - self.line_height) // 2
            
            draw.text((text_x, text_y), goodbye_text, font=self.chinese_font, fill="white")
            
            # 底部显示提示
            hint_text = "感谢使用"
            hint_font = get_chinese_font(10)
            hint_width = hint_font.getlength(hint_text)
            draw.text(((self.width - hint_width) // 2, self.height - 15), hint_text, font=hint_font, fill="white")
    
    def _display_title_screen(self):
        """显示标题屏幕 - 大字体和图形"""
        with self._get_canvas() as draw:
            # 清屏
            draw.rectangle([0, 0, self.width-1, self.height-1], fill="black")
            
            # 绘制顶部和底部的装饰线条
            draw.line([10, 5, self.width-10, 5], fill="white", width=2)
            draw.line([10, self.height-6, self.width-10, self.height-6], fill="white", width=2)
            

            try:
                if PIL_AVAILABLE:
                    title_font = get_chinese_font(16)
                else:
                    title_font = self.chinese_font
            except:
                title_font = self.chinese_font
            
            # 显示大标题
            title_text = "语音助手"
            title_width = title_font.getlength(title_text)
            title_x = (self.width - title_width) // 2
            draw.text((title_x, 15), title_text, font=title_font, fill="white")
            
            # 显示版本信息
            version_text = "v1.0"
            version_font = get_chinese_font(10)
            version_width = version_font.getlength(version_text)
            version_x = (self.width - version_width) // 2
            draw.text((version_x, 35), version_text, font=version_font, fill="white")
    
    def _display_system_info(self):
        """显示系统信息"""
        with self._get_canvas() as draw:
            # 清屏
            draw.rectangle([0, 0, self.width-1, self.height-1], fill="black")
            
            # 显示标题
            title_text = "系统信息"
            title_width = self.chinese_font.getlength(title_text)
            draw.text(((self.width - title_width) // 2, 5), title_text, font=self.chinese_font, fill="white")
            

            
            # 显示系统状态信息
            info_lines = [
                "Raspberry Pi 5",
                "OLED 128x64",
                "中文语音助手"
            ]
            
            # 计算垂直居中位置
            total_height = len(info_lines) * self.line_height
            start_y = (self.height - total_height) // 2
            
            # 显示每行信息
            for i, line in enumerate(info_lines):
                y_pos = start_y + i * self.line_height
                draw.text((10, y_pos), line, font=self.chinese_font, fill="white")
    
    def _display_loading_animation(self):
        """显示加载动画"""
        with self._get_canvas() as draw:
            # 清屏
            draw.rectangle([0, 0, self.width-1, self.height-1], fill="black")
            
            # 显示加载中文字
            loading_text = "正在初始化..."
            text_width = self.chinese_font.getlength(loading_text)
            draw.text(((self.width - text_width) // 2, 15), loading_text, font=self.chinese_font, fill="white")
            
            # 绘制进度条背景
            progress_bar_y = 35
            progress_bar_height = 8
            progress_bar_width = self.width - 30
            
            # 进度条背景
            draw.rectangle([15, progress_bar_y, 15+progress_bar_width, progress_bar_y+progress_bar_height], 
                          outline="white", fill="black")
            
            # 进度条前景（动态增长）
            for i in range(4):  # 4个阶段
                segment_width = progress_bar_width // 4
                segment_x = 15 + i * segment_width
                
                draw.rectangle([segment_x, progress_bar_y+1, segment_x+segment_width-2, progress_bar_y+progress_bar_height-1], 
                              fill="white")
                
                # 在实际硬件上，这里应该有延迟，但模拟模式下我们直接画完
                if not self.simulate:
                    time.sleep(0.05)
    
    def _display_ready_state(self):
        """显示就绪状态（简化版，只显示等待指令）"""
        with self._get_canvas() as draw:
            # 清屏
            draw.rectangle([0, 0, self.width-1, self.height-1], fill="black")
            
            # 只显示"等待指令"居中
            prompt_text = "等待指令"
            prompt_width = self.chinese_font.getlength(prompt_text)
            
            # 垂直居中
            prompt_x = (self.width - prompt_width) // 2
            prompt_y = (self.height - self.line_height) // 2
            
            draw.text((prompt_x, prompt_y), prompt_text, font=self.chinese_font, fill="white")
            
            # 底部小提示（10pt字体，根据用户要求）
            hint_text = "按空格键说话"
            hint_font = get_chinese_font(10)  # 从8pt改为10pt，更大更清晰
            hint_width = hint_font.getlength(hint_text)
            draw.text(((self.width - hint_width) // 2, self.height - 15), hint_text, font=hint_font, fill="white")
    
    def _get_canvas(self):
        """获取画布上下文管理器"""
        if self.simulate:
            # 模拟模式：创建虚拟画布
            class SimulatedCanvas:
                def __init__(self, width, height):
                    self.image = Image.new("1", (width, height))
                    self.draw = ImageDraw.Draw(self.image)
                
                def __enter__(self):
                    return self.draw
                
                def __exit__(self, exc_type, exc_val, exc_tb):
                    # 在模拟模式下，可以在这里输出图像信息
                    pass
            
            return SimulatedCanvas(self.width, self.height)
        else:
            return canvas(self.device)
    
    def clear_screen(self):
        """清屏"""
        with self._get_canvas() as draw:
            # 绘制完整的黑色填充矩形
            if OLED_SHOW_BORDER:
                # 显示完整边框：绘制带边框的黑色矩形
                draw.rectangle([0, 0, self.width-1, self.height-1], outline="white", fill="black")
            else:
                # 无边框：只填充黑色
                draw.rectangle([0, 0, self.width-1, self.height-1], fill="black")
        
        # 清空当前显示内容
        self.current_display_text = ""
        self.current_display_lines = []
        
        logger.debug("屏幕已清除")
    
    def _display_full_screen_text(self, text):
        """
        全屏显示单句文本（内部方法）
        自动换行，确保文本在屏幕内可读
        """
        if not text:
            return
        
        clean_text = text.strip()
        
        # 文本换行处理
        max_width = self.width - 20  # 留边距
        max_lines = self.height // self.line_height
        
        lines = wrap_text(clean_text, self.chinese_font, max_width)
        
        # 如果行数超过屏幕容量，进行截断
        if len(lines) > max_lines:
            lines = lines[:max_lines]
            lines[-1] = lines[-1] + "..."
        
        # 保存当前显示内容
        self.current_display_text = clean_text
        self.current_display_lines = lines
        
        # 绘制到屏幕
        with self._get_canvas() as draw:
            # 清屏（根据配置决定是否有边框）
            if OLED_SHOW_BORDER:
                # 显示完整边框：绘制带边框的黑色矩形
                draw.rectangle([0, 0, self.width-1, self.height-1], outline="white", fill="black")
            else:
                # 无边框：只填充黑色
                draw.rectangle([0, 0, self.width-1, self.height-1], fill="black")
            
            # 计算起始Y位置（垂直居中）
            total_text_height = len(lines) * self.line_height
            start_y = (self.height - total_text_height) // 2
            
            # 绘制每一行文本
            for i, line in enumerate(lines):
                y_pos = start_y + i * self.line_height
                
                # 计算文本宽度以水平居中
                text_width = self.chinese_font.getlength(line)
                x_pos = (self.width - text_width) // 2
                
                draw.text((x_pos, y_pos), line, font=self.chinese_font, fill="white")
    
    def display_text(self, text, text_type=None):
        """
        显示文本到OLED屏幕（主要接口）
        全屏显示单句话，可以指定文本类型（用于添加标签）
        
        Args:
            text: 要显示的文本
            text_type: 文本类型，可选 "user"（用户）或 "ai"（助手），用于添加标签
        """
        if not text or not text.strip():
            return
        
        clean_text = text.strip()
        
        # 根据文本类型添加标签
        if text_type == "user":
            display_text = f"用户: {clean_text}"
            logger.info(f"显示用户输入: {clean_text}")
        elif text_type == "ai":
            display_text = f"助手: {clean_text}"
            logger.info(f"显示AI输出: {clean_text[:50]}...")
        else:
            display_text = clean_text
            logger.info(f"显示文本: {clean_text[:50]}...")
        
        # 全屏显示文本
        self._display_full_screen_text(display_text)
    
    def display_user_input(self, text):
        """显示用户输入（便捷函数）"""
        self.display_text(text, text_type="user")
    
    def display_ai_output(self, text):
        """显示AI输出（便捷函数）"""
        self.display_text(text, text_type="ai")
    
    def show_error(self, error_message):
        """显示错误信息"""
        logger.error(f"OLED显示错误: {error_message}")
        
        with self._get_canvas() as draw:
            # 清屏（根据配置决定是否有边框）
            if OLED_SHOW_BORDER:
                # 显示完整边框：绘制带边框的黑色矩形
                draw.rectangle([0, 0, self.width-1, self.height-1], outline="white", fill="black")
            else:
                # 无边框：只填充黑色
                draw.rectangle([0, 0, self.width-1, self.height-1], fill="black")
            
            # 显示错误标题
            draw.text((10, 10), "错误", font=self.chinese_font, fill="white")
            
            # 错误信息换行显示
            max_width = self.width - 20
            error_lines = wrap_text(error_message, self.default_font, max_width)
            
            for i, line in enumerate(error_lines[:3]):  # 最多显示3行
                y_pos = 30 + i * self.line_height
                draw.text((10, y_pos), line, font=self.default_font, fill="white")
    
    def cleanup(self):
        """清理资源"""
        if not self.simulate and self.device:
            try:
                self.device.clear()
                logger.info("OLED资源已清理")
            except Exception as e:
                logger.error(f"清理OLED资源时出错: {e}")


# 全局OLED实例
_oled_instance = None


def get_oled_instance(simulate=False):
    """
    获取OLED显示实例（单例模式）
    Args:
        simulate: 是否使用模拟模式
    Returns:
        OLEDDisplay实例
    """
    global _oled_instance
    if _oled_instance is None:
        _oled_instance = OLEDDisplay(simulate=simulate)
    return _oled_instance


def display_text(text, text_type=None):
    """显示文本（便捷函数）"""
    try:
        oled = get_oled_instance()
        oled.display_text(text, text_type)
    except Exception as e:
        logger.error(f"显示文本失败: {e}")


def display_user_input(text):
    """显示用户输入（便捷函数）"""
    try:
        oled = get_oled_instance()
        oled.display_user_input(text)
    except Exception as e:
        logger.error(f"显示用户输入失败: {e}")


def display_ai_output(text):
    """显示AI输出（便捷函数）"""
    try:
        oled = get_oled_instance()
        oled.display_ai_output(text)
    except Exception as e:
        logger.error(f"显示AI输出失败: {e}")


def cleanup_oled():
    """清理OLED资源（便捷函数）"""
    global _oled_instance
    if _oled_instance:
        _oled_instance.cleanup()
        _oled_instance = None

def show_shutdown_animation():
    """显示关机动画（便捷函数）"""
    global _oled_instance
    if _oled_instance:
        try:
            _oled_instance.show_shutdown_animation()
        except Exception as e:
            logger.error(f"显示关机动画失败: {e}")
    else:
        logger.warning("OLED实例不存在，无法显示关机动画")


def test_oled():
    """测试OLED显示功能"""
    print("测试OLED显示功能...")
    
    try:
        oled = OLEDDisplay(simulate=True)
        
        # 等待开机动画完成
        time.sleep(2.5)
        
        # 测试用户输入显示
        oled.display_user_input("你好，语音助手！")
        print("✓ 用户输入显示测试")
        time.sleep(2)
        
        # 测试AI输出显示（短文本）
        oled.display_ai_output("你好！我是您的语音助手，有什么可以帮助您的吗？")
        print("✓ AI短文本显示测试")
        time.sleep(2)
        
        # 测试AI输出显示（长文本）
        long_text = "这是一个较长的AI回复文本，用于测试OLED屏幕的文本换行功能。当文本超过显示区域时，应该能够正确地进行换行处理，确保可读性。"
        oled.display_ai_output(long_text)
        print("✓ AI长文本显示测试")
        time.sleep(2)
        
        # 清屏
        oled.clear_screen()
        print("✓ 清屏功能测试")
        time.sleep(1)
        
        oled.cleanup()
        print("OLED测试完成！")
        
    except Exception as e:
        print(f"OLED测试失败: {e}")


if __name__ == "__main__":
    test_oled()