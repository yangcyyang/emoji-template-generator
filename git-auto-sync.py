#!/usr/bin/env python3
"""
🔄 Git 自动同步脚本
功能：监控文件变化 → 自动 commit → 可选自动 push

使用方法:
    python3 git-auto-sync.py           # 启动监控
    python3 git-auto-sync.py --setup   # 配置 GitHub 远程仓库
    python3 git-auto-sync.py --once    # 手动同步一次
    python3 git-auto-sync.py --push    # 立即 push
"""

import os
import sys
import json
import time
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Set, Dict, Optional


class GitAutoSync:
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path).resolve()
        self.config_file = self.repo_path / ".git-auto-sync.json"
        self.config = self._load_config()
        self.file_hashes: Dict[str, str] = {}
        
    def _load_config(self) -> dict:
        """加载配置文件"""
        default_config = {
            "auto_commit": True,
            "auto_push": False,
            "commit_message_template": "auto: 更新于 {time}",
            "ignore_patterns": ["*.tmp", "*.log", ".DS_Store", "__pycache__", ".git", 
                              "node_modules", "*.pyc", ".pytest_cache", "output"],
            "debounce_seconds": 3,
            "file_extensions": [".py", ".html", ".js", ".css", ".md", ".json", ".txt"]
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                    default_config.update(saved_config)
            except Exception as e:
                print(f"⚠️  配置加载失败: {e}, 使用默认配置")
        
        return default_config
    
    def _save_config(self):
        """保存配置文件"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def _run_git(self, *args, check=True) -> subprocess.CompletedProcess:
        """执行 git 命令"""
        result = subprocess.run(
            ["git", "-C", str(self.repo_path)] + list(args),
            capture_output=True,
            text=True
        )
        if check and result.returncode != 0:
            raise RuntimeError(f"Git 命令失败: {' '.join(args)}\n{result.stderr}")
        return result
    
    def _should_ignore(self, file_path: Path) -> bool:
        """检查文件是否应该被忽略"""
        import fnmatch
        
        path_str = str(file_path)
        name = file_path.name
        
        # 检查忽略模式
        for pattern in self.config["ignore_patterns"]:
            if fnmatch.fnmatch(name, pattern) or fnmatch.fnmatch(path_str, pattern):
                return True
        
        # 检查扩展名
        if self.config.get("file_extensions"):
            if file_path.suffix not in self.config["file_extensions"]:
                return True
        
        return False
    
    def _get_file_hash(self, file_path: Path) -> str:
        """计算文件哈希"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return ""
    
    def _scan_files(self) -> Dict[str, str]:
        """扫描所有文件并计算哈希"""
        files_hash = {}
        for root, dirs, files in os.walk(self.repo_path):
            # 过滤忽略的目录
            dirs[:] = [d for d in dirs if not self._should_ignore(Path(d))]
            
            for filename in files:
                file_path = Path(root) / filename
                if not self._should_ignore(file_path):
                    rel_path = str(file_path.relative_to(self.repo_path))
                    files_hash[rel_path] = self._get_file_hash(file_path)
        
        return files_hash
    
    def _has_changes(self) -> bool:
        """检查是否有未提交的更改"""
        result = self._run_git("status", "--porcelain", check=False)
        return bool(result.stdout.strip())
    
    def _get_changed_files(self) -> list:
        """获取变更的文件列表"""
        result = self._run_git("status", "--porcelain", check=False)
        files = []
        for line in result.stdout.strip().split('\n'):
            if line:
                status = line[:2]
                filename = line[3:]
                files.append(f"{status}:{filename}")
        return files
    
    def commit(self, message: Optional[str] = None) -> bool:
        """执行提交"""
        if not self._has_changes():
            return False
        
        # 添加所有更改
        self._run_git("add", ".")
        
        # 生成提交信息
        if message is None:
            template = self.config["commit_message_template"]
            message = template.format(
                time=datetime.now().strftime("%m-%d %H:%M"),
                date=datetime.now().strftime("%Y-%m-%d")
            )
        
        # 提交
        self._run_git("commit", "-m", message)
        print(f"✅ 已提交: {message}")
        
        # 自动推送
        if self.config.get("auto_push", False):
            self.push()
        
        return True
    
    def push(self) -> bool:
        """推送到远程"""
        try:
            # 检查是否有远程仓库
            result = self._run_git("remote", "-v", check=False)
            if not result.stdout.strip():
                print("⚠️  没有配置远程仓库，跳过 push")
                return False
            
            self._run_git("push")
            print("🚀 已推送到远程")
            return True
        except Exception as e:
            print(f"❌ Push 失败: {e}")
            return False
    
    def setup_remote(self, username: str, repo_name: str):
        """配置 GitHub 远程仓库"""
        remote_url = f"https://github.com/{username}/{repo_name}.git"
        
        # 检查是否已有远程仓库
        result = self._run_git("remote", "-v", check=False)
        if "origin" in result.stdout:
            print("📝 更新远程仓库地址...")
            self._run_git("remote", "set-url", "origin", remote_url)
        else:
            print("📝 添加远程仓库...")
            self._run_git("remote", "add", "origin", remote_url)
        
        # 保存配置
        self.config["github_username"] = username
        self.config["github_repo"] = repo_name
        self._save_config()
        
        print(f"✅ 远程仓库配置完成: {remote_url}")
        print("💡 首次推送需要手动执行: git push -u origin master")
    
    def watch(self):
        """监控文件变化"""
        print("👀 开始监控文件变化...")
        print(f"   仓库路径: {self.repo_path}")
        print(f"   自动提交: {'✅' if self.config['auto_commit'] else '❌'}")
        print(f"   自动推送: {'✅' if self.config['auto_push'] else '❌'}")
        print(f"   防抖时间: {self.config['debounce_seconds']}秒")
        print("   按 Ctrl+C 停止\n")
        
        last_check = time.time()
        pending_changes = False
        
        try:
            while True:
                time.sleep(1)
                
                # 检查是否有更改
                if self._has_changes():
                    if not pending_changes:
                        pending_changes = True
                        last_check = time.time()
                        print(f"📝 检测到文件变化，等待 {self.config['debounce_seconds']} 秒后提交...")
                    
                    # 防抖：等待指定时间无新更改后再提交
                    elapsed = time.time() - last_check
                    if elapsed >= self.config["debounce_seconds"]:
                        if self.config["auto_commit"]:
                            changed = self._get_changed_files()
                            self.commit()
                            print(f"   变更文件: {', '.join(changed[:3])}{'...' if len(changed) > 3 else ''}\n")
                        pending_changes = False
                else:
                    pending_changes = False
                    
        except KeyboardInterrupt:
            print("\n👋 停止监控")
            # 停止前如果有待提交更改，询问是否提交
            if self._has_changes():
                response = input("有未提交的更改，是否提交? [y/N]: ").strip().lower()
                if response in ('y', 'yes'):
                    self.commit()
                    if input("是否推送到远程? [y/N]: ").strip().lower() in ('y', 'yes'):
                        self.push()


def main():
    if len(sys.argv) < 2:
        # 默认启动监控
        sync = GitAutoSync()
        sync.watch()
        
    elif sys.argv[1] == "--setup":
        # 配置远程仓库
        username = input("GitHub 用户名: ").strip()
        repo_name = input("仓库名称 (默认: emoji-template-generator): ").strip() or "emoji-template-generator"
        
        sync = GitAutoSync()
        sync.setup_remote(username, repo_name)
        
    elif sys.argv[1] == "--once":
        # 手动同步一次
        sync = GitAutoSync()
        if sync.commit():
            print("✅ 同步完成")
        else:
            print("ℹ️  没有需要提交的更改")
            
    elif sys.argv[1] == "--push":
        # 立即推送
        sync = GitAutoSync()
        sync.push()
        
    elif sys.argv[1] == "--config":
        # 编辑配置
        config_file = Path(".git-auto-sync.json")
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print("当前配置:")
            print(json.dumps(config, indent=2, ensure_ascii=False))
        
        print("\n修改配置:")
        auto_push = input("是否开启自动推送? [y/N]: ").strip().lower() == 'y'
        
        sync = GitAutoSync()
        sync.config["auto_push"] = auto_push
        sync._save_config()
        print(f"✅ 配置已保存: auto_push={auto_push}")
        
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
