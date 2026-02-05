import socket
import subprocess
import os

def get_network_info():
    """获取网络信息"""
    print("=" * 50)
    print("网络诊断工具")
    print("=" * 50)
    
    # 获取本机IP
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        print(f"本机主机名: {hostname}")
        print(f"本机IP地址: {local_ip}")
    except:
        print("无法获取本机网络信息")
    
    # 获取网关
    try:
        result = subprocess.run(['ip', 'route'], capture_output=True, text=True)
        print("路由信息:")
        print(result.stdout)
    except:
        print("无法获取路由信息")

def test_connectivity(target_ip):
    """测试到目标IP的连接性"""
    print(f"\n测试连接到 {target_ip}")
    
    # 测试ping
    try:
        print("1. 测试ping...")
        response = subprocess.run(['ping', '-c', '3', target_ip], 
                                capture_output=True, text=True, timeout=10)
        if response.returncode == 0:
            print("✅ Ping测试成功")
            print(response.stdout)
        else:
            print("❌ Ping测试失败")
            print(response.stderr)
    except Exception as e:
        print(f"❌ Ping测试错误: {e}")
    
    # 测试端口
    print("2. 测试端口7860...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((target_ip, 7860))
        sock.close()
        
        if result == 0:
            print("✅ 端口7860可以访问")
        else:
            print(f"❌ 端口7860无法访问 (错误代码: {result})")
    except Exception as e:
        print(f"❌ 端口测试错误: {e}")

if __name__ == "__main__":
    get_network_info()
    
    # 请将下面的IP替换为您的Windows主机实际IP
    windows_ip = input("\n请输入Windows主机的IP地址: ").strip()
    
    if windows_ip:
        test_connectivity(windows_ip)
    else:
        print("未输入IP地址，退出")
