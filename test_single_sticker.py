#!/usr/bin/env python3
"""
测试脚本 - 下载单个贴图
用法: python3 test_single_sticker.py
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# 配置
STICKER_ID = "36844"
OUTPUT_DIR = "/Users/cy/workspace/表情包模板/downloads"

print("🚀 LINE 贴图自动下载测试")
print(f"贴图 ID: {STICKER_ID}")
print("=" * 60)

# 设置 Chrome 选项
chrome_options = Options()
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])

# 使用你的 Chrome Profile（保留登录状态）
chrome_options.add_argument("--user-data-dir=/Users/cy/Library/Application Support/Google/Chrome")
chrome_options.add_argument("--profile-directory=Profile 7")

# 设置下载目录
import os
os.makedirs(OUTPUT_DIR, exist_ok=True)
prefs = {
    "download.default_directory": OUTPUT_DIR,
    "download.prompt_for_download": False,
}
chrome_options.add_experimental_option("prefs", prefs)

# 启动浏览器
print("\n1️⃣ 启动 Chrome...")
try:
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
except:
    driver = webdriver.Chrome(options=chrome_options)

print("✅ Chrome 已启动")

# 访问贴图页面
url = f"https://store.line.me/stickershop/product/{STICKER_ID}/zh-Hant"
print(f"\n2️⃣ 访问贴图页面...")
print(f"   URL: {url}")
driver.get(url)
time.sleep(3)

print("✅ 页面加载完成")

# 查找下载按钮
print("\n3️⃣ 查找扩展注入的下载按钮...")
buttons = driver.find_elements(By.XPATH, 
    "//button[contains(text(), 'iPhone') or contains(text(), 'Android') or contains(text(), 'PC')] | " +
    "//a[contains(text(), 'iPhone') or contains(text(), 'Android')] | " +
    "//div[contains(@class, 'lsp')] | " +
    "//*[contains(@data-track, 'download')]"
)

print(f"   找到 {len(buttons)} 个可能的按钮")

# 显示所有按钮信息
for i, btn in enumerate(buttons[:5], 1):
    try:
        text = btn.text[:50] if btn.text else "(无文字)"
        print(f"   按钮 {i}: {text}")
    except:
        print(f"   按钮 {i}: (无法读取)")

# 截图保存
screenshot_path = f"{OUTPUT_DIR}/test_screenshot.png"
driver.save_screenshot(screenshot_path)
print(f"\n4️⃣ 已保存截图: {screenshot_path}")

# 尝试点击第一个 iPhone 2x 按钮
print("\n5️⃣ 尝试点击下载按钮...")
clicked = False
for btn in buttons:
    try:
        text = btn.text
        if '2x' in text or 'iPhone' in text:
            btn.click()
            print(f"   ✅ 已点击: {text}")
            clicked = True
            time.sleep(5)  # 等待下载
            break
    except:
        continue

if not clicked and buttons:
    try:
        buttons[0].click()
        print(f"   ✅ 已点击第一个按钮")
        time.sleep(5)
    except Exception as e:
        print(f"   ❌ 点击失败: {e}")

print("\n6️⃣ 检查下载结果...")
import glob
downloaded = glob.glob(f"{OUTPUT_DIR}/*.zip")
if downloaded:
    print(f"   ✅ 下载成功: {len(downloaded)} 个文件")
    for f in downloaded[-3:]:
        print(f"      - {os.path.basename(f)}")
else:
    print("   ⚠️ 未找到下载的 ZIP 文件")
    print("   可能原因:")
    print("   - 扩展未正确加载")
    print("   - 按钮未被正确识别")
    print("   - 需要手动点击一次扩展初始化")

print("\n" + "=" * 60)
print("测试完成，5秒后关闭浏览器...")
time.sleep(5)
driver.quit()
print("✅ 浏览器已关闭")
