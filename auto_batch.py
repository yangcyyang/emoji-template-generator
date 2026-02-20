#!/usr/bin/env python3
"""
表情包批量处理主控脚本
协调服务器和浏览器完成全自动处理

使用方法:
    python auto_batch.py <集合文件夹路径>
"""

import os
import sys
import time
import shutil
import zipfile
from pathlib import Path
from datetime import datetime

# Selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# 导入服务器模块
from server import start_server, set_collection_folder, set_current_folder, state

def log(message, level="INFO"):
    """打印日志"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    icons = {"INFO": "ℹ️", "SUCCESS": "✅", "WARNING": "⚠️", "ERROR": "❌", "PROCESS": "⚙️"}
    print(f"[{timestamp}] {icons.get(level, 'ℹ️')} {message}")

def setup_chrome():
    """配置Chrome浏览器"""
    chrome_options = Options()
    
    # 基础配置
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # 下载配置 - 设置下载目录
    download_dir = str(Path.home() / "Downloads")
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    # 可选：无头模式（不显示浏览器窗口）
    # chrome_options.add_argument("--headless=new")
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_window_size(1400, 900)
    return driver

def wait_for_download(download_dir, folder_name, timeout=30):
    """等待ZIP文件下载完成"""
    expected_file = f"{folder_name}_表情包.zip"
    download_path = Path(download_dir) / expected_file
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        # 检查文件是否存在且完整（没有.crdownload后缀）
        if download_path.exists():
            # 检查是否还在下载中
            temp_file = Path(str(download_path) + ".crdownload")
            if not temp_file.exists():
                return download_path
        time.sleep(0.5)
    
    return None

def process_collection(collection_path):
    """处理整个集合文件夹"""
    collection_path = Path(collection_path)
    
    if not collection_path.exists():
        log(f"文件夹不存在: {collection_path}", "ERROR")
        return False
    
    print("\n" + "=" * 60)
    print("🎨 表情包批量处理器")
    print("=" * 60 + "\n")
    
    # 1. 启动服务器
    log("启动HTTP服务器...")
    server = start_server(port=8765)
    time.sleep(1)
    
    # 2. 扫描文件夹
    log(f"扫描集合文件夹: {collection_path}")
    folders = set_collection_folder(collection_path)
    
    if not folders:
        log("未找到有效的子文件夹", "ERROR")
        return False
    
    log(f"找到 {len(folders)} 个待处理文件夹", "SUCCESS")
    for i, f in enumerate(folders, 1):
        print(f"  {i}. {f['name']}")
    
    # 3. 启动浏览器
    log("启动Chrome浏览器...")
    driver = setup_chrome()
    
    # 打开批量处理器页面
    driver.get("http://localhost:8765/batch-processor.html")
    time.sleep(2)
    
    # 4. 逐个处理文件夹
    download_dir = Path.home() / "Downloads"
    output_dir = state.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    
    try:
        for index, folder_info in enumerate(folders):
            folder_name = folder_info['name']
            
            print("\n" + "-" * 50)
            log(f"[{index+1}/{len(folders)}] 处理: {folder_name}", "PROCESS")
            
            # 设置当前文件夹
            if not set_current_folder(index):
                log(f"设置文件夹失败: {folder_name}", "ERROR")
                continue
            
            # 刷新页面以获取新文件夹数据
            driver.refresh()
            time.sleep(2)
            
            # 调用JS处理函数
            log("开始渲染和截图...")
            driver.execute_script("window.BatchProcessor.process()")
            
            # 等待处理完成
            time.sleep(8)  # 给足够时间渲染和下载
            
            # 等待下载完成
            log("等待ZIP下载...")
            downloaded_file = wait_for_download(download_dir, folder_name)
            
            if downloaded_file and downloaded_file.exists():
                # 移动并重命名到输出目录
                final_path = output_dir / f"{folder_name}_表情包.zip"
                shutil.move(str(downloaded_file), str(final_path))
                log(f"✓ 已保存: {final_path.name}", "SUCCESS")
                results.append({"folder": folder_name, "success": True, "file": str(final_path)})
            else:
                log(f"✗ 下载失败或超时", "ERROR")
                results.append({"folder": folder_name, "success": False, "error": "Download timeout"})
            
            # 间隔一下
            time.sleep(1)
    
    except KeyboardInterrupt:
        log("用户中断", "WARNING")
    except Exception as e:
        log(f"处理出错: {e}", "ERROR")
        import traceback
        traceback.print_exc()
    
    finally:
        # 5. 清理
        print("\n" + "-" * 50)
        log("关闭浏览器...")
        driver.quit()
        
        log("停止服务器...")
        server.shutdown()
    
    # 6. 创建总包
    if results:
        print("\n" + "=" * 50)
        log("创建总包...", "PROCESS")
        
        success_count = sum(1 for r in results if r.get("success"))
        timestamp = datetime.now().strftime("%m%d_%H%M")
        master_zip = output_dir / f"表情包合集_{timestamp}.zip"
        
        with zipfile.ZipFile(master_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
            for result in results:
                if result.get("success") and Path(result["file"]).exists():
                    zf.write(result["file"], Path(result["file"]).name)
        
        log(f"总包已创建: {master_zip.name}", "SUCCESS")
        
        # 汇总
        print(f"\n📊 处理结果:")
        print(f"   成功: {success_count}/{len(results)}")
        print(f"   输出: {output_dir}")
        print(f"   总包: {master_zip}")
    
    print("=" * 50 + "\n")
    return True

def main():
    if len(sys.argv) < 2:
        print("用法: python auto_batch.py <集合文件夹路径>")
        print("示例: python auto_batch.py '/Users/cy/Desktop/表情包素材'")
        return
    
    collection_path = sys.argv[1]
    process_collection(collection_path)

if __name__ == "__main__":
    main()
