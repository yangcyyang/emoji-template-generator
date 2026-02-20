#!/usr/bin/env python3
"""
LINE 贴图批量自动下载工具
使用 Selenium 控制 Chrome 自动点击 LineStickerPacker 扩展下载按钮

使用方法:
1. 确保 Chrome 已安装 LineStickerPacker 扩展
2. 确保已登录 LINE Store
3. 运行: python3 line_sticker_auto_download.py

作者: Assistant
日期: 2024
"""

import os
import sys
import time
import json
import argparse
from pathlib import Path
from urllib.parse import urljoin

# Selenium 导入
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager


class LineStickerAutoDownloader:
    def __init__(self, output_dir="./downloads"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # 扩展相关信息
        self.extension_id = "bngfikljchleddkelnfgohdfcobkggin"
        self.extension_path = Path.home() / "Library/Application Support/Google/Chrome/Profile 7/Extensions/bngfikljchleddkelnfgohdfcobkggin/1.6.5_0"
        
        self.driver = None
        self.wait = None
        
    def setup_driver(self, headless=False):
        """初始化 Chrome 浏览器"""
        chrome_options = Options()
        
        # 基本设置
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # 加载本地扩展（如果存在）
        if self.extension_path.exists():
            print(f"✅ 找到扩展: {self.extension_path}")
            # 注意：加载未打包扩展需要特殊处理
            # chrome_options.add_argument(f"--load-extension={self.extension_path}")
        else:
            print(f"⚠️ 扩展路径不存在: {self.extension_path}")
            print("请确保扩展已安装，脚本将尝试通过已安装的 Chrome 使用扩展")
        
        # 使用用户数据目录（保留登录状态）
        user_data_dir = Path.home() / "Library/Application Support/Google/Chrome"
        if user_data_dir.exists():
            # 使用 Profile 7（根据用户提供的路径）
            profile_path = user_data_dir / "Profile 7"
            if profile_path.exists():
                chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
                chrome_options.add_argument("--profile-directory=Profile 7")
                print(f"✅ 使用 Chrome Profile: Profile 7")
        
        # 设置下载目录
        prefs = {
            "download.default_directory": str(self.output_dir.absolute()),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        # 无头模式（可选）
        if headless:
            chrome_options.add_argument("--headless=new")
        
        # 启动浏览器
        print("🚀 正在启动 Chrome...")
        try:
            # 尝试使用 ChromeDriverManager 自动管理驱动
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
        except Exception as e:
            print(f"⚠️ 自动安装驱动失败: {e}")
            print("尝试使用系统 ChromeDriver...")
            self.driver = webdriver.Chrome(options=chrome_options)
        
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        self.wait = WebDriverWait(self.driver, 10)
        print("✅ Chrome 启动成功")
        
    def get_author_stickers(self, author_id):
        """获取作者所有贴图 ID"""
        url = f"https://store.line.me/stickershop/author/{author_id}/zh-Hant"
        print(f"🔍 访问作者页面: {url}")
        
        self.driver.get(url)
        time.sleep(3)  # 等待页面加载
        
        # 提取所有贴图链接
        sticker_links = []
        try:
            # 寻找贴图链接
            links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/stickershop/product/']")
            for link in links:
                href = link.get_attribute("href")
                if "/product/" in href:
                    sticker_id = href.split("/product/")[-1].split("/")[0]
                    if sticker_id.isdigit():
                        sticker_links.append(sticker_id)
            
            # 去重
            sticker_links = list(dict.fromkeys(sticker_links))
            print(f"✅ 找到 {len(sticker_links)} 个贴图")
            
        except Exception as e:
            print(f"⚠️ 获取贴图列表失败: {e}")
        
        return sticker_links
    
    def download_sticker(self, sticker_id, wait_time=5):
        """
        下载单个贴图
        通过找到扩展注入的下载按钮并点击
        """
        url = f"https://store.line.me/stickershop/product/{sticker_id}/zh-Hant"
        print(f"\n📦 处理贴图 ID: {sticker_id}")
        print(f"   URL: {url}")
        
        try:
            self.driver.get(url)
            time.sleep(2)  # 等待页面加载
            
            # 等待扩展加载（通过查找扩展注入的按钮）
            # 扩展通常会在页面顶部或贴图信息区域插入下载按钮
            print("   ⏳ 等待扩展加载...")
            time.sleep(2)
            
            # 方法1: 尝试通过 CSS 选择器查找扩展按钮
            # 扩展按钮通常有特定的类名或包含特定文字
            download_buttons = []
            
            # 查找包含 "iPhone 2x" 或 "Android" 等文字的按钮
            try:
                buttons = self.driver.find_elements(By.XPATH, 
                    "//button[contains(text(), 'iPhone') or contains(text(), 'Android') or contains(text(), 'PC')] | " +
                    "//a[contains(text(), 'iPhone') or contains(text(), 'Android') or contains(text(), 'PC')] | " +
                    "//div[contains(text(), 'iPhone') or contains(text(), 'Android') or contains(text(), 'PC')]"
                )
                download_buttons.extend(buttons)
            except:
                pass
            
            # 方法2: 查找扩展可能使用的特定类名
            try:
                buttons = self.driver.find_elements(By.CSS_SELECTOR, 
                    ".lsp-download-btn, .line-sticker-packer, [data-lsp], .mdCMN38Body button"
                )
                download_buttons.extend(buttons)
            except:
                pass
            
            # 方法3: 查找所有按钮并筛选
            if not download_buttons:
                all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
                for btn in all_buttons:
                    try:
                        text = btn.text.lower()
                        if any(keyword in text for keyword in ['download', '下載', '下载', 'iphone', 'android']):
                            download_buttons.append(btn)
                    except:
                        pass
            
            if not download_buttons:
                print("   ⚠️ 未找到下载按钮，扩展可能未加载或需要手动点击")
                # 截图保存供调试
                screenshot_path = self.output_dir / f"debug_{sticker_id}.png"
                self.driver.save_screenshot(str(screenshot_path))
                print(f"   📸 已保存调试截图: {screenshot_path}")
                return False
            
            print(f"   ✅ 找到 {len(download_buttons)} 个可能的下载按钮")
            
            # 点击第一个 iPhone 2x 或 Android 按钮（通常是高清版本）
            target_button = None
            for btn in download_buttons:
                try:
                    text = btn.text
                    if '2x' in text or 'iPhone' in text:
                        target_button = btn
                        print(f"   🎯 选择: {text}")
                        break
                except:
                    continue
            
            if not target_button and download_buttons:
                target_button = download_buttons[0]
                print(f"   🎯 选择第一个按钮")
            
            if target_button:
                # 滚动到按钮位置
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target_button)
                time.sleep(0.5)
                
                # 点击按钮
                target_button.click()
                print("   ✅ 已点击下载按钮")
                
                # 等待下载完成
                print(f"   ⏳ 等待下载完成 ({wait_time}秒)...")
                time.sleep(wait_time)
                
                return True
            
        except Exception as e:
            print(f"   ❌ 错误: {e}")
            return False
        
        return False
    
    def batch_download(self, author_id, limit=None, delay=3):
        """批量下载作者的所有贴图"""
        print(f"\n{'='*60}")
        print(f"🎨 LINE 贴图批量下载")
        print(f"作者 ID: {author_id}")
        print(f"{'='*60}\n")
        
        # 获取贴图列表
        sticker_ids = self.get_author_stickers(author_id)
        
        if not sticker_ids:
            print("❌ 未找到贴图")
            return
        
        if limit:
            sticker_ids = sticker_ids[:limit]
        
        total = len(sticker_ids)
        success_count = 0
        failed_count = 0
        
        print(f"\n准备下载 {total} 个贴图\n")
        
        for i, sticker_id in enumerate(sticker_ids, 1):
            print(f"[{i}/{total}] ", end="")
            
            if self.download_sticker(sticker_id):
                success_count += 1
            else:
                failed_count += 1
            
            if i < total:  # 不是最后一个
                print(f"   ⏳ 等待 {delay} 秒...")
                time.sleep(delay)
        
        print(f"\n{'='*60}")
        print(f"✅ 完成!")
        print(f"成功: {success_count}, 失败: {failed_count}")
        print(f"下载目录: {self.output_dir}")
        print(f"{'='*60}\n")
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            print("🚪 关闭 Chrome...")
            self.driver.quit()


def main():
    parser = argparse.ArgumentParser(description='LINE 贴图自动下载工具')
    parser.add_argument('author_id', nargs='?', default='150',
                        help='作者 ID (默认: 150 Fujiko-Pro)')
    parser.add_argument('-o', '--output', default='./downloads',
                        help='下载目录 (默认: ./downloads)')
    parser.add_argument('-l', '--limit', type=int, default=None,
                        help='限制下载数量')
    parser.add_argument('-d', '--delay', type=int, default=3,
                        help='下载间隔秒数 (默认: 3)')
    parser.add_argument('--headless', action='store_true',
                        help='无头模式（不显示浏览器窗口）')
    parser.add_argument('--id', type=int, default=None,
                        help='下载单个贴图 ID')
    
    args = parser.parse_args()
    
    downloader = None
    try:
        downloader = LineStickerAutoDownloader(args.output)
        downloader.setup_driver(headless=args.headless)
        
        if args.id:
            # 下载单个
            print(f"🎯 下载单个贴图: {args.id}")
            downloader.download_sticker(args.id, wait_time=10)
        else:
            # 批量下载
            downloader.batch_download(args.author_id, args.limit, args.delay)
            
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if downloader:
            downloader.close()


if __name__ == '__main__':
    main()
