# LINE 贴图自动下载工具

使用 Selenium 自动控制 Chrome 浏览器，自动点击 LineStickerPacker 扩展的下载按钮。

## 🚀 快速开始

### 1. 安装依赖

```bash
cd /Users/cy/workspace/表情包模板
pip3 install selenium webdriver-manager
```

### 2. 确保 Chrome 已登录

- 打开 Chrome
- 访问 https://store.line.me
- **登录你的 LINE 账号**（必须已购买要下载的贴图）
- 确保 LineStickerPacker 扩展已启用

### 3. 运行脚本

```bash
# 下载 Fujiko-Pro（哆啦A梦）的所有贴图
python3 line_sticker_auto_download.py 150

# 下载单个贴图
python3 line_sticker_auto_download.py --id 36844

# 限制下载数量（测试用）
python3 line_sticker_auto_download.py 150 --limit 3

# 查看帮助
python3 line_sticker_auto_download.py --help
```

## 📋 命令参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `author_id` | 作者 ID | 150 (Fujiko-Pro) |
| `-o, --output` | 下载目录 | ./downloads |
| `-l, --limit` | 限制下载数量 | 无限制 |
| `-d, --delay` | 下载间隔（秒） | 3 |
| `--id` | 下载单个贴图 ID | 无 |
| `--headless` | 无头模式（隐藏浏览器） | 关闭 |

## 🔧 工作原理

1. **启动 Chrome** - 使用你的 Profile（保留登录状态）
2. **访问贴图页面** - 自动打开每个贴图详情页
3. **查找下载按钮** - 查找扩展注入的下载按钮（iPhone 2x / Android / PC）
4. **自动点击** - 模拟点击下载按钮
5. **等待下载** - 等待浏览器完成下载
6. **批量处理** - 循环处理下一个贴图

## ⚠️ 注意事项

### 必需条件
- ✅ Chrome 浏览器已安装
- ✅ LineStickerPacker 扩展已安装
- ✅ 已登录 LINE Store
- ✅ **已购买**要下载的贴图（否则无法下载）

### 可能的问题

**问题1: 找不到下载按钮**
- 扩展可能没有正确加载
- 脚本会保存调试截图到 `debug_{sticker_id}.png`
- 检查截图确认扩展按钮位置

**问题2: 下载失败**
- LINE 可能有下载频率限制
- 增加 `--delay` 参数，如 `--delay 5`

**问题3: Chrome 启动失败**
- 确保没有其他 Chrome 实例正在运行
- 尝试关闭所有 Chrome 窗口后再运行

## 📁 输出文件

下载的文件会保存在指定目录（默认 `./downloads`）：
- 贴图 ZIP 文件
- 调试截图（如果失败）

## 🛠️ 高级用法

### 下载不同作者的贴图

```bash
# 查找作者 ID
# 访问 https://store.line.me/stickershop/author/{ID}
# 从 URL 获取 ID

# 示例：下载其他作者
python3 line_sticker_auto_download.py 12345 --limit 10
```

### 无头模式（后台运行）

```bash
python3 line_sticker_auto_download.py 150 --headless --limit 5
```

## 🔍 故障排除

### 检查扩展是否正常工作

1. 手动打开 Chrome
2. 访问 https://store.line.me/stickershop/product/36844/zh-Hant
3. 检查是否显示绿色下载按钮
4. 如果没有，扩展可能需要重新启用

### 查看下载进度

脚本会实时输出：
```
🎨 LINE 贴图批量下载
作者 ID: 150
============================================================

🔍 访问作者页面: https://store.line.me/stickershop/author/150/zh-Hant
✅ 找到 45 个贴图

准备下载 45 个贴图

[1/45] 📦 处理贴图 ID: 36844
   URL: https://store.line.me/stickershop/product/36844/zh-Hant
   ⏳ 等待扩展加载...
   ✅ 找到 3 个可能的下载按钮
   🎯 选择: iPhone 2x
   ✅ 已点击下载按钮
   ⏳ 等待下载完成 (5秒)...
```

## 💡 提示

- **首次运行**建议先用 `--limit 1` 测试单个贴图
- **下载间隔**不要太短，避免被 LINE 限制
- **保持 Chrome 可见**（不用 `--headless`）可以观察进度

## 📞 需要帮助？

如果脚本无法正常工作：
1. 检查 Chrome 版本是否兼容
2. 确保扩展已正确安装
3. 查看调试截图定位问题
4. 告诉我错误信息，我可以帮你调整
