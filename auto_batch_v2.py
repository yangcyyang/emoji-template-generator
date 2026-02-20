#!/usr/bin/env python3
"""
表情包批量处理主控脚本 V2
通过API直接接收图片数据，避免浏览器下载问题
"""

import os
import sys
import time
import json
import base64
import zipfile
from pathlib import Path
from datetime import datetime

# Selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# 导入服务器
from server import start_server, set_collection_folder, set_current_folder, state

def log(message, level="INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    icons = {"INFO": "ℹ️", "SUCCESS": "✅", "WARNING": "⚠️", "ERROR": "❌", "PROCESS": "⚙️"}
    print(f"[{timestamp}] {icons.get(level, 'ℹ️')} {message}")

def setup_chrome():
    """配置Chrome浏览器"""
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_window_size(1400, 900)
    return driver

def process_collection(collection_path):
    """处理整个集合文件夹"""
    collection_path = Path(collection_path)
    
    if not collection_path.exists():
        log(f"文件夹不存在: {collection_path}", "ERROR")
        return False
    
    print("\n" + "=" * 60)
    print("🎨 表情包批量处理器 V2")
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
    driver.get("http://localhost:8765/batch-processor.html")
    time.sleep(2)
    
    output_dir = state.output_dir
    results = []
    
    try:
        for index, folder_info in enumerate(folders):
            folder_name = folder_info['name']
            
            print("\n" + "-" * 50)
            log(f"[{index+1}/{len(folders)}] 处理: {folder_name}", "PROCESS")
            
            # 设置当前文件夹
            if not set_current_folder(index):
                log(f"设置文件夹失败", "ERROR")
                continue
            
            # 刷新页面
            driver.refresh()
            time.sleep(2)
            
            # 等待页面加载完成
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "log-panel"))
            )
            
            # 执行处理
            log("浏览器渲染中...")
            driver.execute_script("window.BatchProcessor.process()")
            
            # 等待处理完成（最多60秒）
            log("等待截图和打包...")
            time.sleep(10)  # 给足够时间渲染和截图
            
            # 检查是否完成
            max_wait = 60
            waited = 10
            while waited < max_wait:
                status = driver.execute_script("return document.getElementById('status-text').textContent")
                if status == "完成":
                    break
                time.sleep(1)
                waited += 1
            
            # 检查输出目录是否生成文件
            folder_output = output_dir / folder_name
            if folder_output.exists() and list(folder_output.glob("*.jpg")):
                files = list(folder_output.glob("*.jpg"))
                log(f"✓ 生成 {len(files)} 张图片", "SUCCESS")
                
                # 创建ZIP
                zip_path = output_dir / f"{folder_name}_表情包.zip"
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for f in files:
                        zf.write(f, f.name)
                
                log(f"✓ ZIP已创建: {zip_path.name}", "SUCCESS")
                results.append({"folder": folder_name, "success": True, "files": len(files)})
            else:
                log(f"✗ 未找到生成的文件", "ERROR")
                results.append({"folder": folder_name, "success": False})
            
            time.sleep(2)
    
    except KeyboardInterrupt:
        log("用户中断", "WARNING")
    except Exception as e:
        log(f"处理出错: {e}", "ERROR")
        import traceback
        traceback.print_exc()
    
    finally:
        print("\n" + "-" * 50)
        log("关闭浏览器...")
        driver.quit()
        log("停止服务器...")
        server.shutdown()
    
    # 创建总包
    if results:
        print("\n" + "=" * 50)
        success_count = sum(1 for r in results if r.get("success"))
        timestamp = datetime.now().strftime("%m%d_%H%M")
        master_zip = output_dir / f"表情包合集_{timestamp}.zip"
        
        with zipfile.ZipFile(master_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
            for folder_info in folders:
                zip_file = output_dir / f"{folder_info['name']}_表情包.zip"
                if zip_file.exists():
                    zf.write(zip_file, zip_file.name)
        
        log(f"总包已创建: {master_zip.name}", "SUCCESS")
        print(f"\n📊 处理结果: {success_count}/{len(results)} 成功")
        print(f"📁 输出目录: {output_dir}")
    
    print("=" * 50 + "\n")
    return True

def main():
    if len(sys.argv) < 2:
        print("用法: python auto_batch_v2.py <集合文件夹路径>")
        return
    
    process_collection(sys.argv[1])

if __name__ == "__main__":
    main()
