#!/usr/bin/env python3
"""
表情包批量处理器
自动处理表情包集合文件夹，生成四模板并打包

使用流程：
1. 配置 config.json
2. 运行: python auto_processor.py
"""

import os
import sys
import json
import time
import shutil
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple
from dataclasses import dataclass
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import webbrowser

# 图像处理
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

# SVG处理
try:
    from svglib.svglib import svg2rlg
    from reportlab.graphics import renderPM
    HAS_SVGLIB = True
except ImportError:
    HAS_SVGLIB = False

# Selenium 自动化
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# 配置文件路径
CONFIG_FILE = Path(__file__).parent / "config.json"
DEFAULT_OUTPUT_DIR = Path(__file__).parent / "output"


@dataclass
class FolderInfo:
    """表情包文件夹信息"""
    path: Path
    name: str
    image_count: int
    images: List[Path]
    title: str = ""
    subtitle: str = ""
    main_image: Path = None


def log(message: str, level: str = "INFO"):
    """打印带时间戳的日志"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    prefix = {
        "INFO": "ℹ️",
        "SUCCESS": "✅",
        "WARNING": "⚠️",
        "ERROR": "❌",
        "PROCESS": "⚙️",
        "DOWNLOAD": "⬇️",
        "COMPLETE": "🎉"
    }.get(level, "ℹ️")
    print(f"[{timestamp}] {prefix} {message}")


def load_config() -> dict:
    """加载配置文件"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_config(config: dict):
    """保存配置文件"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def init_config():
    """初始化默认配置"""
    default_config = {
        "collection_folder": "",
        "output_folder": str(DEFAULT_OUTPUT_DIR),
        "min_images": 15,
        "templates": {
            "template1": True,
            "template2": True,
            "template3": True,
            "template4": True
        },
        "chrome_profile": "Profile 7",
        "headless": False,
        "auto_start": False,
        "font_path": "刘欢卡通手书.ttf",
        "image_quality": 95,
        "canvas_size": [1200, 1600]
    }
    
    if not CONFIG_FILE.exists():
        save_config(default_config)
        log(f"已创建默认配置文件: {CONFIG_FILE}", "SUCCESS")
        return default_config
    
    return load_config()


class ImageProcessor:
    """图像处理器 - 使用 PIL 替代浏览器"""
    
    def __init__(self, config: dict):
        self.config = config
        self.canvas_width, self.canvas_height = config.get("canvas_size", [1200, 1600])
        self.font_path = Path(__file__).parent / config.get("font_path", "刘欢卡通手书.ttf")
        self.output_dir = Path(config.get("output_folder", DEFAULT_OUTPUT_DIR))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 加载字体
        self._load_fonts()
    
    def _load_fonts(self):
        """加载字体"""
        try:
            self.font_title = ImageFont.truetype(str(self.font_path), 72)
            self.font_subtitle = ImageFont.truetype(str(self.font_path), 42)
            self.font_small = ImageFont.truetype(str(self.font_path), 24)
        except Exception as e:
            log(f"字体加载失败: {e}，使用默认字体", "WARNING")
            self.font_title = ImageFont.load_default()
            self.font_subtitle = self.font_title
            self.font_small = self.font_title
    
    def load_icon(self, icon_path: Path, size: Tuple[int, int]) -> Image.Image:
        """加载图标（支持PNG和SVG）"""
        try:
            # 优先尝试PNG
            png_path = icon_path.with_suffix('.png')
            if png_path.exists():
                icon = Image.open(png_path).convert('RGBA')
                icon = icon.resize(size, Image.Resampling.LANCZOS)
                return icon
            
            # 尝试SVG
            if HAS_SVGLIB and icon_path.exists():
                from svglib.svglib import svg2rlg
                from reportlab.graphics import renderPM
                drawing = svg2rlg(str(icon_path))
                if drawing:
                    scale_x = size[0] / drawing.width
                    scale_y = size[1] / drawing.height
                    drawing.scale(scale_x, scale_y)
                    icon = renderPM.drawToPIL(drawing)
                    return icon
        except Exception as e:
            log(f"图标加载失败 {icon_path}: {e}", "WARNING")
        
        # 创建占位图标
        placeholder = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(placeholder)
        draw.ellipse([0, 0, size[0], size[1]], fill=(200, 200, 200, 128))
        return placeholder
    
    def extract_dominant_color(self, image_path: Path) -> Tuple[int, int, int]:
        """提取图片主色调 - 使用K-means聚类找到最突出的颜色"""
        try:
            with Image.open(image_path) as img:
                # 转换为RGBA处理透明背景
                img = img.convert('RGBA')
                # 创建白色背景
                background = Image.new('RGBA', img.size, (255, 255, 255, 255))
                img = Image.alpha_composite(background, img)
                img = img.convert('RGB')
                
                # 缩小图片加速处理
                img = img.resize((100, 100))
                pixels = list(img.getdata())
                
                # 过滤掉接近白色的背景色
                filtered = []
                for r, g, b in pixels:
                    # 计算与白色的距离
                    dist_to_white = ((255-r)**2 + (255-g)**2 + (255-b)**2) ** 0.5
                    if dist_to_white > 30:  # 不是白色/浅色
                        filtered.append((r, g, b))
                
                if not filtered:
                    return (254, 207, 120)  # 默认金黄色
                
                # 使用K-means简化版：找到颜色聚类中心
                # 将颜色量化到较少的区间
                quantized = {}
                for r, g, b in filtered:
                    # 量化到32的倍数，减少颜色数量
                    qr, qg, qb = (r//32)*32, (g//32)*32, (b//32)*32
                    key = (qr, qg, qb)
                    quantized[key] = quantized.get(key, 0) + 1
                
                # 找到最常见的颜色
                most_common = max(quantized.items(), key=lambda x: x[1])[0]
                
                # 返回该颜色的实际平均值（而非量化值）
                matching = [(r, g, b) for r, g, b in filtered 
                           if (r//32)*32 == most_common[0] 
                           and (g//32)*32 == most_common[1] 
                           and (b//32)*32 == most_common[2]]
                
                if matching:
                    avg_r = sum(c[0] for c in matching) // len(matching)
                    avg_g = sum(c[1] for c in matching) // len(matching)
                    avg_b = sum(c[2] for c in matching) // len(matching)
                    return (avg_r, avg_g, avg_b)
                
                return most_common
                
        except Exception as e:
            log(f"颜色提取失败: {e}", "WARNING")
            return (254, 207, 120)
    
    def create_gradient_background(self, color: Tuple[int, int, int], width: int, height: int) -> Image.Image:
        """创建渐变背景"""
        base = Image.new('RGB', (width, height), color)
        
        # 创建渐变层
        gradient = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(gradient)
        
        # 简单的水平渐变
        r, g, b = color
        for y in range(height):
            factor = 1 - (y / height) * 0.3  # 顶部亮，底部暗
            new_color = (int(r * factor), int(g * factor), int(b * factor))
            draw.line([(0, y), (width, y)], fill=new_color)
        
        # 混合
        result = Image.blend(base, gradient, 0.5)
        return result
    
    def load_and_resize_image(self, image_path: Path, size: Tuple[int, int]) -> Image.Image:
        """加载并调整图片大小"""
        try:
            with Image.open(image_path) as img:
                img = img.convert('RGBA')
                # 保持比例缩放到指定尺寸内
                img.thumbnail(size, Image.Resampling.LANCZOS)
                # 创建透明背景
                background = Image.new('RGBA', size, (255, 255, 255, 0))
                # 居中粘贴
                x = (size[0] - img.width) // 2
                y = (size[1] - img.height) // 2
                background.paste(img, (x, y), img)
                return background
        except Exception as e:
            log(f"图片加载失败 {image_path}: {e}", "WARNING")
            # 返回占位图
            placeholder = Image.new('RGBA', size, (240, 240, 240, 255))
            draw = ImageDraw.Draw(placeholder)
            draw.text((size[0]//2, size[1]//2), "Error", fill=(200, 200, 200), anchor="mm")
            return placeholder
    
    def generate_template1(self, folder: FolderInfo) -> Image.Image:
        """生成模板1：头图+9宫格"""
        log(f"  生成模板1: {folder.name}", "PROCESS")
        
        # 创建画布
        canvas = Image.new('RGB', (self.canvas_width, self.canvas_height), (255, 255, 255))
        
        # 头图区域高度
        header_height = int(self.canvas_height * 0.4)
        
        # 获取主图
        if folder.main_image and folder.main_image.exists():
            main_image_path = folder.main_image
        else:
            main_image_path = folder.images[0] if folder.images else None
        
        # 提取主色调创建背景
        if main_image_path:
            dominant_color = self.extract_dominant_color(main_image_path)
            header_bg = self.create_gradient_background(dominant_color, self.canvas_width, header_height)
        else:
            header_bg = Image.new('RGB', (self.canvas_width, header_height), (254, 207, 120))
        
        # 粘贴头图背景
        canvas.paste(header_bg, (0, 0))
        
        # 左侧主图
        if main_image_path:
            main_img = self.load_and_resize_image(main_image_path, (400, 400))
            # 转换为RGB
            main_img_rgb = Image.new('RGB', main_img.size, (255, 255, 255))
            main_img_rgb.paste(main_img, mask=main_img.split()[3] if main_img.mode == 'RGBA' else None)
            canvas.paste(main_img_rgb, (60, (header_height - 400) // 2))
        
        # 绘制右侧文字区域
        draw = ImageDraw.Draw(canvas)
        
        # 获取标题
        title = folder.title or folder.name
        subtitle = folder.subtitle or "表情包合集"
        count_text = f"共 {folder.image_count} 张"
        
        # 计算文字位置（右侧居中）
        text_x = 520
        text_y = header_height // 2
        
        # 绘制标题
        draw.text((text_x, text_y - 50), title, fill=(255, 255, 255), font=self.font_title)
        draw.text((text_x, text_y + 30), subtitle, fill=(255, 255, 255), font=self.font_subtitle)
        
        # 绘制右上角图标和数量
        # 加载图标
        icon_size = 48
        wechat_icon = self.load_icon(Path(__file__).parent / "wechat-icon.svg", (icon_size, icon_size))
        qq_icon = self.load_icon(Path(__file__).parent / "qq-icon.svg", (icon_size, icon_size))
        
        # 计算位置（右上角）
        icon_y = 30
        right_margin = 40
        
        # 粘贴微信图标
        if wechat_icon:
            icon_x = self.canvas_width - right_margin - icon_size * 2 - 10
            canvas.paste(wechat_icon, (icon_x, icon_y), wechat_icon if wechat_icon.mode == 'RGBA' else None)
        
        # 粘贴QQ图标
        if qq_icon:
            icon_x = self.canvas_width - right_margin - icon_size
            canvas.paste(qq_icon, (icon_x, icon_y), qq_icon if qq_icon.mode == 'RGBA' else None)
        
        # 绘制数量文字（在图标左侧）
        count_x = self.canvas_width - right_margin - icon_size * 2 - 20
        draw.text((count_x, icon_y + 12), count_text, fill=(255, 255, 255), font=self.font_small, anchor="rm")
        
        # 绘制3x3网格（剩余9张图）- 匹配原index.html尺寸 200x160（2倍=400x320）
        grid_images = folder.images[1:10] if len(folder.images) > 1 else folder.images[:9]
        cell_width = 400   # 200 * 2
        cell_height = 320  # 160 * 2
        gap = 0  # 无间距，像浏览器版一样紧密排列
        start_x = 0  # 从左边开始
        start_y = header_height  # 紧接头图下方
        
        for idx, img_path in enumerate(grid_images[:9]):
            if idx >= 9:
                break
            row = idx // 3
            col = idx % 3
            x = start_x + col * cell_width
            y = start_y + row * cell_height
            
            img = self.load_and_resize_image(img_path, (cell_width, cell_height))
            # 转换为RGB并粘贴
            img_rgb = Image.new('RGB', img.size, (255, 255, 255))
            img_rgb.paste(img, mask=img.split()[3] if img.mode == 'RGBA' else None)
            canvas.paste(img_rgb, (x, y))
        
        return canvas
    
    def generate_template_grid(self, folder: FolderInfo, start_idx: int, template_num: int) -> Image.Image:
        """生成模板2/3/4：3x5网格"""
        log(f"  生成模板{template_num}: {folder.name} (起始{start_idx})", "PROCESS")
        
        # 创建白色画布
        canvas = Image.new('RGB', (self.canvas_width, self.canvas_height), (255, 255, 255))
        
        # 3x5 网格布局 - 匹配原index.html尺寸 200x160（2倍=400x320）
        cols, rows = 3, 5
        cell_width = 400   # 200 * 2
        cell_height = 320  # 160 * 2
        
        # 获取15张图片
        end_idx = start_idx + 15
        grid_images = folder.images[start_idx:end_idx]
        
        # 如果图片不足，循环使用
        while len(grid_images) < 15:
            remaining = 15 - len(grid_images)
            grid_images.extend(folder.images[:remaining])
        
        for idx, img_path in enumerate(grid_images[:15]):
            row = idx // cols
            col = idx % cols
            x = col * cell_width
            y = row * cell_height
            
            # 加载并粘贴图片
            img = self.load_and_resize_image(img_path, (cell_width, cell_height))
            img_rgb = Image.new('RGB', img.size, (255, 255, 255))
            img_rgb.paste(img, mask=img.split()[3] if img.mode == 'RGBA' else None)
            canvas.paste(img_rgb, (x, y))
        
        return canvas
    
    def process_folder(self, folder: FolderInfo) -> List[Path]:
        """处理单个文件夹，生成所有模板"""
        generated_files = []
        
        # 创建输出子文件夹
        folder_output = self.output_dir / folder.name
        folder_output.mkdir(parents=True, exist_ok=True)
        
        templates_config = self.config.get("templates", {})
        quality = self.config.get("image_quality", 95)
        
        # 模板1
        if templates_config.get("template1", True):
            img = self.generate_template1(folder)
            output_path = folder_output / f"01_头图_{folder.name}.jpg"
            img.save(output_path, "JPEG", quality=quality)
            generated_files.append(output_path)
            log(f"    ✓ 模板1已保存: {output_path.name}", "SUCCESS")
        
        # 模板2、3、4
        for i, template_key in enumerate(["template2", "template3", "template4"], start=2):
            if templates_config.get(template_key, True):
                start_idx = (i - 2) * 15
                img = self.generate_template_grid(folder, start_idx, i)
                output_path = folder_output / f"0{i}_网格{i-1}_{folder.name}.jpg"
                img.save(output_path, "JPEG", quality=quality)
                generated_files.append(output_path)
                log(f"    ✓ 模板{i}已保存: {output_path.name}", "SUCCESS")
        
        return generated_files


class FolderScanner:
    """文件夹扫描器"""
    
    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
    
    def __init__(self, min_images: int = 15):
        self.min_images = min_images
    
    def scan(self, collection_path: Path) -> List[FolderInfo]:
        """扫描表情包集合文件夹"""
        log(f"扫描文件夹: {collection_path}")
        
        if not collection_path.exists():
            raise FileNotFoundError(f"文件夹不存在: {collection_path}")
        
        folders = []
        
        # 遍历所有子文件夹
        for item in sorted(collection_path.iterdir()):
            if item.is_dir() and not item.name.startswith('.'):
                folder_info = self._process_subfolder(item)
                if folder_info:
                    folders.append(folder_info)
        
        log(f"找到 {len(folders)} 个有效表情包文件夹", "SUCCESS")
        return folders
    
    def _process_subfolder(self, folder_path: Path) -> FolderInfo:
        """处理单个子文件夹"""
        # 收集图片
        images = []
        for f in folder_path.iterdir():
            if f.is_file() and f.suffix.lower() in self.SUPPORTED_FORMATS:
                # 排除缩略图和UI元素（如包含 _key、tab_off、tab_on 的文件）
                exclude_names = ['_key', '_s.', 'tab_off', 'tab_on']
                if not any(exclude in f.stem for exclude in exclude_names):
                    images.append(f)
        
        # 按文件名排序
        images.sort(key=lambda x: x.name)
        
        if len(images) < self.min_images:
            log(f"跳过 {folder_path.name}: 仅 {len(images)} 张图片（需要≥{self.min_images}）", "WARNING")
            return None
        
        # 解析文件夹名获取标题
        name = folder_path.name
        title, subtitle = self._parse_folder_name(name)
        
        # 选择主图（第一张或包含特定关键词的）
        main_image = images[0] if images else None
        for img in images[:5]:
            if any(kw in img.stem.lower() for kw in ['main', 'cover', '01', '1_']):
                main_image = img
                break
        
        return FolderInfo(
            path=folder_path,
            name=name,
            image_count=len(images),
            images=images,
            title=title,
            subtitle=subtitle,
            main_image=main_image
        )
    
    def _parse_folder_name(self, name: str) -> Tuple[str, str]:
        """解析文件夹名获取标题和副标题"""
        # 移除常见分隔符后的编号
        import re
        
        # 尝试提取序号和名称
        match = re.match(r'^(\d+)[\.\-_\s]*(.+)$', name)
        if match:
            title = match.group(2).strip()
        else:
            title = name
        
        # 清理标题
        title = title.replace('_', ' ').replace('-', ' ').strip()
        
        # 尝试提取副标题（如果有特定分隔符）
        subtitle = "表情包合集"
        if '·' in title:
            parts = title.split('·')
            title = parts[0].strip()
            subtitle = parts[1].strip() if len(parts) > 1 else subtitle
        elif '|' in title:
            parts = title.split('|')
            title = parts[0].strip()
            subtitle = parts[1].strip() if len(parts) > 1 else subtitle
        
        return title, subtitle


class PackageManager:
    """打包管理器"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.zip_dir = output_dir / "_zip_packages"
        self.zip_dir.mkdir(parents=True, exist_ok=True)
    
    def package_folder(self, folder_name: str, files: List[Path]) -> Path:
        """将文件夹的输出打包为 zip"""
        import zipfile
        
        zip_path = self.zip_dir / f"{folder_name}_表情包.zip"
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path in files:
                if file_path.exists():
                    zf.write(file_path, file_path.name)
        
        log(f"  打包完成: {zip_path.name}", "SUCCESS")
        return zip_path
    
    def create_master_package(self, all_packages: List[Path]) -> Path:
        """创建总包"""
        import zipfile
        
        timestamp = datetime.now().strftime("%m%d_%H%M")
        master_zip = self.zip_dir / f"表情包合集_{timestamp}.zip"
        
        with zipfile.ZipFile(master_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
            for pkg in all_packages:
                if pkg.exists():
                    zf.write(pkg, pkg.name)
        
        log(f"总包已创建: {master_zip}", "COMPLETE")
        return master_zip


def setup_chrome_driver(config: dict) -> webdriver.Chrome:
    """配置并启动 Chrome 浏览器"""
    log("配置 Chrome 浏览器...")
    
    chrome_options = Options()
    
    # 基础配置
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # 下载配置
    download_dir = str(Path(config.get("output_folder", DEFAULT_OUTPUT_DIR)).absolute())
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    # 配置文件
    profile = config.get("chrome_profile", "Profile 7")
    user_data_dir = f"/Users/{os.environ.get('USER', 'cy')}/Library/Application Support/Google/Chrome"
    
    if os.path.exists(user_data_dir):
        chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
        chrome_options.add_argument(f"--profile-directory={profile}")
    
    # 无头模式
    if config.get("headless", False):
        chrome_options.add_argument("--headless=new")
    
    # 启动浏览器
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_window_size(1400, 900)
        log("Chrome 浏览器已启动", "SUCCESS")
        return driver
    except Exception as e:
        log(f"Chrome 启动失败: {e}", "ERROR")
        raise


class AutoProcessor:
    """主处理器"""
    
    def __init__(self):
        self.config = init_config()
        self.scanner = FolderScanner(self.config.get("min_images", 15))
        self.processor = None  # 延迟初始化
        self.packager = None
        self.driver = None
        self.folders: List[FolderInfo] = []
        self.results = []
    
    def validate_config(self) -> bool:
        """验证配置"""
        collection_folder = self.config.get("collection_folder", "")
        
        if not collection_folder:
            log("错误: 未配置 collection_folder", "ERROR")
            log(f"请编辑配置文件: {CONFIG_FILE}", "WARNING")
            return False
        
        path = Path(collection_folder)
        if not path.exists():
            log(f"错误: 文件夹不存在: {path}", "ERROR")
            return False
        
        return True
    
    def scan_folders(self):
        """扫描文件夹"""
        collection_path = Path(self.config["collection_folder"])
        self.folders = self.scanner.scan(collection_path)
        
        if not self.folders:
            log("未找到有效的表情包文件夹", "ERROR")
            return False
        
        # 打印汇总
        log("\n📁 扫描结果汇总:")
        for i, folder in enumerate(self.folders, 1):
            log(f"  {i}. {folder.name}")
            log(f"     图片数: {folder.image_count} | 标题: {folder.title}")
        
        return True
    
    def process_with_pil(self):
        """使用 PIL 纯 Python 处理"""
        log("\n" + "=" * 50)
        log("开始批量处理 (PIL模式)")
        log("=" * 50)
        
        self.processor = ImageProcessor(self.config)
        self.packager = PackageManager(self.processor.output_dir)
        
        all_packages = []
        
        for idx, folder in enumerate(self.folders, 1):
            log(f"\n[{idx}/{len(self.folders)}] 处理: {folder.name}")
            
            try:
                # 生成模板
                generated_files = self.processor.process_folder(folder)
                
                # 打包
                if generated_files:
                    pkg = self.packager.package_folder(folder.name, generated_files)
                    all_packages.append(pkg)
                
                self.results.append({
                    "folder": folder.name,
                    "success": True,
                    "files": [str(f) for f in generated_files]
                })
                
            except Exception as e:
                log(f"处理失败: {e}", "ERROR")
                self.results.append({
                    "folder": folder.name,
                    "success": False,
                    "error": str(e)
                })
        
        # 创建总包
        if all_packages:
            master = self.packager.create_master_package(all_packages)
            log(f"\n✨ 所有表情包已打包: {master}", "COMPLETE")
        
        # 保存处理报告
        self._save_report()
    
    def _save_report(self):
        """保存处理报告"""
        report_path = Path(self.config.get("output_folder", DEFAULT_OUTPUT_DIR)) / "_processing_report.json"
        report = {
            "timestamp": datetime.now().isoformat(),
            "config": self.config,
            "results": self.results,
            "summary": {
                "total": len(self.results),
                "success": sum(1 for r in self.results if r.get("success")),
                "failed": sum(1 for r in self.results if not r.get("success"))
            }
        }
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        log(f"处理报告已保存: {report_path}")
    
    def run(self):
        """主运行流程"""
        print("\n" + "=" * 60)
        print("🎨 表情包批量处理器")
        print("=" * 60 + "\n")
        
        # 验证配置
        if not self.validate_config():
            return False
        
        # 扫描文件夹
        if not self.scan_folders():
            return False
        
        # 确认开始
        if not self.config.get("auto_start", False):
            response = input("\n确认开始处理? (y/n): ").strip().lower()
            if response != 'y':
                log("已取消")
                return False
        
        # 处理（使用 PIL 模式）
        self.process_with_pil()
        
        # 完成
        log("\n" + "=" * 50)
        log("处理完成！")
        log(f"输出目录: {self.config.get('output_folder', DEFAULT_OUTPUT_DIR)}")
        log("=" * 50)
        
        return True


def main():
    """主入口"""
    processor = AutoProcessor()
    processor.run()


if __name__ == "__main__":
    main()
