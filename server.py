#!/usr/bin/env python3
"""
表情包处理服务器
提供静态文件服务 + API接口供浏览器调用
"""

import os
import json
import base64
import zipfile
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import threading
import shutil

# 全局状态
class ServerState:
    collection_folder = None  # 集合文件夹路径
    current_folder = None     # 当前处理的子文件夹
    all_folders = []         # 所有待处理文件夹列表
    current_index = 0        # 当前处理索引
    output_dir = None        # 输出目录

state = ServerState()

class APIHandler(SimpleHTTPRequestHandler):
    """处理API请求和静态文件"""
    
    def end_headers(self):
        # 添加CORS头
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()
    
    def log_message(self, format, *args):
        # 简化日志
        try:
            msg = args[0] if args else ""
            if isinstance(msg, str) and '/api/' in msg:
                print(f"[API] {msg}")
        except:
            pass
    
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        
        # API: 获取当前文件夹信息
        if path == '/api/folder':
            self.send_json(self.get_folder_info())
            return
        
        # API: 获取文件夹列表
        if path == '/api/folders':
            self.send_json({
                "folders": state.all_folders,
                "current_index": state.current_index,
                "total": len(state.all_folders)
            })
            return
        
        # API: 获取图片文件（用于浏览器加载）
        if path.startswith('/api/image/'):
            image_path = path[len('/api/image/'):]
            self.serve_image(image_path)
            return
        
        # 静态文件服务
        return super().do_GET()
    
    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        
        # API: 接收生成的图片数据
        if path == '/api/upload':
            self.handle_upload()
            return
        
        # API: 标记当前文件夹完成
        if path == '/api/complete':
            self.handle_complete()
            return
        
        self.send_error(404)
    
    def send_json(self, data):
        """发送JSON响应"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def get_folder_info(self):
        """获取当前文件夹信息"""
        if not state.current_folder:
            return {"error": "No folder selected"}
        
        folder_path = Path(state.current_folder)
        
        # 扫描图片文件
        images = []
        for f in folder_path.iterdir():
            if f.is_file() and f.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
                if '_key' not in f.name and '_s' not in f.name:
                    images.append({
                        "name": f.name,
                        "path": str(f.absolute()),
                        "url": f"/api/image/{base64.b64encode(str(f.absolute()).encode()).decode()}"
                    })
        
        images.sort(key=lambda x: x["name"])
        
        # 解析标题
        title = folder_path.name
        subtitle = "表情包合集"
        if '·' in title:
            parts = title.split('·')
            title = parts[0].strip()
            subtitle = parts[1].strip()
        
        # 检测动态/静态
        gif_count = sum(1 for img in images if img["name"].endswith('.gif'))
        anim_type = "动态表情包" if gif_count > len(images) * 0.3 else "静态表情包"
        
        return {
            "name": folder_path.name,
            "title": title,
            "subtitle": subtitle,
            "images": images,
            "image_count": len(images),
            "anim_type": anim_type,
            "main_image": images[0] if images else None
        }
    
    def serve_image(self, encoded_path):
        """提供图片文件"""
        try:
            image_path = base64.b64decode(encoded_path).decode()
            path = Path(image_path)
            if path.exists():
                self.send_response(200)
                content_type = {
                    '.png': 'image/png',
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.gif': 'image/gif',
                    '.webp': 'image/webp'
                }.get(path.suffix.lower(), 'application/octet-stream')
                self.send_header('Content-Type', content_type)
                self.end_headers()
                with open(path, 'rb') as f:
                    self.wfile.write(f.read())
                return
        except Exception as e:
            print(f"Error serving image: {e}")
        
        self.send_error(404)
    
    def handle_upload(self):
        """处理上传的图片数据（Base64）"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            
            folder_name = data.get('folder_name')
            images = data.get('images', [])  # [{name, data: base64}]
            
            if not folder_name or not images:
                self.send_json({"error": "Missing data"})
                return
            
            # 保存到输出目录
            folder_output = state.output_dir / folder_name
            folder_output.mkdir(parents=True, exist_ok=True)
            
            saved_files = []
            for img_data in images:
                name = img_data['name']
                data = img_data['data'].split(',')[1] if ',' in img_data['data'] else img_data['data']
                img_bytes = base64.b64decode(data)
                
                output_path = folder_output / name
                with open(output_path, 'wb') as f:
                    f.write(img_bytes)
                saved_files.append(str(output_path))
            
            # 创建ZIP包
            zip_path = state.output_dir / "_downloads" / f"{folder_name}_表情包.zip"
            zip_path.parent.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for file_path in saved_files:
                    zf.write(file_path, Path(file_path).name)
            
            self.send_json({
                "success": True,
                "saved_files": saved_files,
                "zip": str(zip_path)
            })
            
        except Exception as e:
            print(f"Upload error: {e}")
            self.send_json({"error": str(e)})
    
    def handle_complete(self):
        """标记当前文件夹处理完成"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            
            print(f"✅ 文件夹完成: {state.current_folder.name if state.current_folder else 'unknown'}")
            
            self.send_json({"success": True})
        except Exception as e:
            self.send_json({"error": str(e)})


def start_server(port=8765, directory="/Users/cy/workspace/表情包模板"):
    """启动服务器"""
    os.chdir(directory)
    server = HTTPServer(('localhost', port), APIHandler)
    print(f"🚀 服务器启动: http://localhost:{port}")
    
    # 在后台线程运行
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    
    return server


def set_collection_folder(folder_path):
    """设置要处理的集合文件夹"""
    state.collection_folder = Path(folder_path)
    state.output_dir = state.collection_folder.parent / (state.collection_folder.name + "_output")
    state.output_dir.mkdir(parents=True, exist_ok=True)
    
    # 扫描所有子文件夹
    state.all_folders = []
    for item in sorted(state.collection_folder.iterdir()):
        if item.is_dir() and not item.name.startswith('.'):
            state.all_folders.append({
                "name": item.name,
                "path": str(item.absolute())
            })
    
    print(f"📁 找到 {len(state.all_folders)} 个待处理文件夹")
    return state.all_folders


def set_current_folder(index):
    """设置当前处理的文件夹"""
    if 0 <= index < len(state.all_folders):
        state.current_index = index
        state.current_folder = Path(state.all_folders[index]["path"])
        print(f"🎯 当前处理: {state.current_folder.name}")
        return True
    return False


if __name__ == "__main__":
    # 测试模式
    start_server()
    input("按回车停止服务器...\n")
