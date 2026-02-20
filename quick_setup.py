#!/usr/bin/env python3
"""
快速配置向导
引导用户完成初次配置
"""

import os
import sys
from pathlib import Path
import json

def log(message, level="INFO"):
    icons = {"INFO": "ℹ️", "SUCCESS": "✅", "WARNING": "⚠️", "ERROR": "❌"}
    print(f"{icons.get(level, 'ℹ️')} {message}")

def main():
    print("\n" + "=" * 50)
    print("🎨 表情包批量处理器 - 快速配置")
    print("=" * 50 + "\n")
    
    # 检查字体
    font_path = Path(__file__).parent / "刘欢卡通手书.ttf"
    if font_path.exists():
        log(f"字体文件已找到: {font_path}", "SUCCESS")
    else:
        log(f"字体文件未找到，请确保字体在: {font_path}", "WARNING")
    
    # 询问素材文件夹
    print("\n请输入表情包素材文件夹路径:")
    print("（该文件夹应包含多个子文件夹，每个子文件夹是一个表情包集合）")
    print("示例: /Users/cy/Desktop/表情包素材")
    
    while True:
        folder = input("\n📁 素材文件夹: ").strip()
        if not folder:
            log("路径不能为空", "WARNING")
            continue
        
        path = Path(folder).expanduser()
        if not path.exists():
            log(f"路径不存在: {path}", "ERROR")
            create = input("是否创建该文件夹? (y/n): ").strip().lower()
            if create == 'y':
                path.mkdir(parents=True)
                log(f"已创建: {path}", "SUCCESS")
            else:
                continue
        
        # 检查子文件夹
        subdirs = [d for d in path.iterdir() if d.is_dir() and not d.name.startswith('.')]
        log(f"找到 {len(subdirs)} 个子文件夹")
        
        if subdirs:
            print("\n子文件夹列表:")
            for i, d in enumerate(subdirs[:10], 1):
                # 统计图片
                imgs = list(d.glob("*.png")) + list(d.glob("*.jpg")) + list(d.glob("*.gif"))
                print(f"  {i}. {d.name} ({len(imgs)} 张图片)")
            if len(subdirs) > 10:
                print(f"  ... 还有 {len(subdirs) - 10} 个")
        
        confirm = input("\n使用此文件夹? (y/n): ").strip().lower()
        if confirm == 'y':
            break
    
    # 询问输出文件夹
    print("\n请输入输出文件夹路径（留空使用默认）:")
    print("默认: ./output")
    output_input = input("📁 输出文件夹: ").strip()
    
    if output_input:
        output_folder = str(Path(output_input).expanduser().absolute())
    else:
        output_folder = str(Path(__file__).parent / "output")
    
    # 创建配置
    config = {
        "collection_folder": str(path.absolute()),
        "output_folder": output_folder,
        "min_images": 15,
        "templates": {
            "template1": True,
            "template2": True,
            "template3": True,
            "template4": True
        },
        "font_path": "刘欢卡通手书.ttf",
        "image_quality": 95,
        "canvas_size": [1200, 1600],
        "auto_start": False
    }
    
    config_path = Path(__file__).parent / "config.json"
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    log(f"\n配置已保存: {config_path}", "SUCCESS")
    
    print("\n" + "=" * 50)
    print("配置完成！")
    print("=" * 50)
    print(f"素材文件夹: {config['collection_folder']}")
    print(f"输出文件夹: {config['output_folder']}")
    print("\n运行以下命令开始处理:")
    print("  python auto_processor.py")
    print("=" * 50 + "\n")

if __name__ == "__main__":
    main()
