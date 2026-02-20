#!/usr/bin/env python3
"""
单文件夹测试工具
快速测试单个表情包文件夹的处理效果
"""

import sys
from pathlib import Path
import json
from datetime import datetime

# 导入主程序模块
from auto_processor import FolderScanner, ImageProcessor, log

def test_single_folder(folder_path: str):
    """测试单文件夹"""
    print("\n" + "=" * 50)
    print("🧪 单文件夹测试模式")
    print("=" * 50 + "\n")
    
    path = Path(folder_path).expanduser()
    
    if not path.exists():
        log(f"文件夹不存在: {path}", "ERROR")
        return
    
    # 扫描单文件夹
    scanner = FolderScanner(min_images=1)
    folder_info = scanner._process_subfolder(path)
    
    if not folder_info:
        log("文件夹处理失败，可能没有有效图片", "ERROR")
        return
    
    # 显示信息
    log(f"文件夹: {folder_info.name}", "INFO")
    log(f"标题: {folder_info.title}")
    log(f"副标题: {folder_info.subtitle}")
    log(f"图片数: {folder_info.image_count}")
    log(f"主图: {folder_info.main_image.name if folder_info.main_image else 'None'}")
    
    # 加载配置或创建默认
    config_path = Path(__file__).parent / "config.json"
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    else:
        config = {
            "output_folder": str(Path(__file__).parent / "test_output"),
            "font_path": "刘欢卡通手书.ttf",
            "image_quality": 95,
            "canvas_size": [1200, 1600],
            "templates": {
                "template1": True,
                "template2": True,
                "template3": True,
                "template4": True
            }
        }
    
    # 创建处理器
    processor = ImageProcessor(config)
    
    # 确认处理
    print("\n将生成以下模板:")
    for t, enabled in config.get("templates", {}).items():
        status = "✅" if enabled else "❌"
        print(f"  {status} {t}")
    
    response = input("\n开始测试处理? (y/n): ").strip().lower()
    if response != 'y':
        log("已取消")
        return
    
    # 处理
    log("\n开始处理...")
    try:
        generated = processor.process_folder(folder_info)
        
        log("\n" + "=" * 50)
        log("测试完成！", "SUCCESS")
        log(f"输出目录: {processor.output_dir / folder_info.name}")
        log("生成的文件:")
        for f in generated:
            print(f"  📄 {f.name}")
        log("=" * 50 + "\n")
        
    except Exception as e:
        log(f"处理失败: {e}", "ERROR")
        import traceback
        traceback.print_exc()

def main():
    if len(sys.argv) < 2:
        print("使用方法: python test_single.py <文件夹路径>")
        print("示例: python test_single.py ~/Desktop/表情包素材/01春意慵懒kitty")
        return
    
    folder_path = sys.argv[1]
    test_single_folder(folder_path)

if __name__ == "__main__":
    main()
