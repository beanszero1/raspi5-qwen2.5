#!/usr/bin/env python3
"""
OLED测试程序 - 使用Pillow库显示中文字符
"""

import time
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from luma.core.render import canvas
from PIL import ImageFont, Image, ImageDraw
import os

def get_chinese_font(size=16):
    """
    获取中文字体，如果没有中文系统字体，则使用Pillow的默认字体
    返回一个可用于显示中文字符的字体对象
    """
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
                print(f"已加载中文字体: {font_path} (大小: {size}px)")
                return font
            except Exception as e:
                print(f"字体加载失败 {font_path}: {e}")
                continue
    
    # 如果找不到中文字体，使用Pillow的默认字体
    print(f"警告: 未找到中文字体，使用Pillow默认字体")
    return ImageFont.load_default()

def test_chinese_text(device, chinese_font, default_font):
    """测试中英文混合文本显示"""
    with canvas(device) as draw:
        # 清屏
        draw.rectangle(device.bounding_box, outline="white", fill="black")
        
        # 使用中文字体显示中文
        y_pos = 5
        draw.text((10, y_pos), "OLED中文测试", font=chinese_font, fill="white")
        y_pos += 20
        
        # 显示中英文混合文本
        draw.text((10, y_pos), "Hello 世界!", font=chinese_font, fill="white")
        y_pos += 20
        
        # 使用小字体显示系统信息
        draw.text((10, y_pos), "树莓派5 OLED显示", font=default_font, fill="white")
    
    print("中英文文本显示完成")
    time.sleep(3)

def test_multiline_chinese(device, chinese_font, default_font):
    """测试多行中文文本显示"""
    with canvas(device) as draw:
        # 清屏
        draw.rectangle(device.bounding_box, outline="white", fill="black")
        
        # 显示多行中文文本
        lines = [
            "欢迎使用树莓派",
            "OLED显示测试",
            "支持中英文混合",
            "Hello World!"
        ]
        
        y_pos = 5
        for i, line in enumerate(lines):
            # 交替使用中文字体和默认字体
            font = chinese_font if i % 2 == 0 else default_font
            draw.text((10, y_pos), line, font=font, fill="white")
            y_pos += 15
    
    print("多行文本显示完成")
    time.sleep(3)

def test_scroll_chinese(device, chinese_font):
    """测试中文滚动文本效果"""
    text = "这是一段滚动的中文文本，用于测试OLED显示屏的滚动功能。"
    
    # 创建足够宽的图像来容纳完整文本
    text_width = chinese_font.getlength(text)
    image_width = max(device.width * 2, int(text_width) + 20)
    temp_image = Image.new("1", (image_width, device.height))
    temp_draw = ImageDraw.Draw(temp_image)
    temp_draw.text((0, 20), text, font=chinese_font, fill="white")
    
    # 滚动显示
    for x in range(0, image_width - device.width + 1, 2):
        with canvas(device) as draw:
            # 裁剪并显示当前部分
            cropped = temp_image.crop((x, 0, x + device.width, device.height))
            draw.bitmap((0, 0), cropped, fill="white")
        time.sleep(0.05)
    
    print("中文滚动文本完成")

def test_chinese_shapes(device, chinese_font, default_font):
    """测试图形和中文标签"""
    with canvas(device) as draw:
        # 清屏
        draw.rectangle(device.bounding_box, outline="white", fill="black")
        
        # 绘制图形并添加中文标签
        # 圆形
        draw.ellipse([(10, 5), (40, 35)], outline="white", fill="black")
        draw.text((15, 40), "圆形", font=chinese_font, fill="white")
        
        # 矩形
        draw.rectangle([(50, 5), (80, 35)], outline="white", fill="black")
        draw.text((55, 40), "矩形", font=chinese_font, fill="white")
        
        # 三角形
        draw.polygon([(95, 35), (110, 5), (125, 35)], outline="white", fill="black")
        draw.text((100, 40), "三角", font=chinese_font, fill="white")
        
        # 底部信息
        draw.text((10, 55), "图形测试完成", font=default_font, fill="white")
    
    print("图形和中文标签显示完成")
    time.sleep(3)

def test_chinese_font_sizes(device):
    """测试不同大小的中文字体"""
    with canvas(device) as draw:
        # 清屏
        draw.rectangle(device.bounding_box, outline="white", fill="black")
        
        # 测试不同字体大小
        small_font = get_chinese_font(12)
        medium_font = get_chinese_font(16)
        large_font = get_chinese_font(20)
        
        draw.text((10, 5), "小字体 (12px)", font=small_font, fill="white")
        draw.text((10, 25), "中字体 (16px)", font=medium_font, fill="white")
        draw.text((10, 45), "大字体 (20px)", font=large_font, fill="white")
    
    print("不同字体大小测试完成")
    time.sleep(3)

def main():
    try:
        # 初始化OLED
        serial = i2c(port=1, address=0x3C)
        device = ssd1306(serial, width=128, height=64)
        
        print("OLED初始化成功")
        
        # 获取中文字体和默认字体
        chinese_font = get_chinese_font(16)  # 16px大小的中文字体
        default_font = ImageFont.load_default()  # Pillow默认字体
        
        # 测试1: 中英文混合文本
        test_chinese_text(device, chinese_font, default_font)
        
        # 测试2: 多行中文文本
        test_multiline_chinese(device, chinese_font, default_font)
        
        # 测试3: 图形和中文标签
        test_chinese_shapes(device, chinese_font, default_font)
        
        # 测试4: 不同字体大小
        test_chinese_font_sizes(device)
        
        # 测试5: 中文滚动文本
        test_scroll_chinese(device, chinese_font)
        
        # 显示结束信息
        with canvas(device) as draw:
            draw.rectangle(device.bounding_box, outline="white", fill="black")
            draw.text((10, 10), "测试完成", font=chinese_font, fill="white")
            draw.text((10, 30), "按任意键退出", font=chinese_font, fill="white")
        
        print("所有测试完成！")
        time.sleep(2)
        
        # 清屏
        device.clear()
        print("屏幕已清除")
        
    except Exception as e:
        print(f"错误: {e}")
        print("\n可能的解决方案:")
        print("1. 检查I2C是否启用: sudo raspi-config")
        print("2. 检查OLED地址: sudo i2cdetect -y 1 (地址应为0x3C或0x3D)")
        print("3. 检查接线是否正确:")
        print("   OLED GND → 树莓派 GND (引脚6)")
        print("   OLED VDD → 树莓派 3.3V (引脚1)")
        print("   OLED SCL → 树莓派 SCL (引脚5)")
        print("   OLED SDA → 树莓派 SDA (引脚3)")
        print("4. 确保已安装 luma.oled: pip install luma.oled")
        print("5. 如果需要中文字体: sudo apt install fonts-wqy-microhei")

if __name__ == "__main__":
    main()
