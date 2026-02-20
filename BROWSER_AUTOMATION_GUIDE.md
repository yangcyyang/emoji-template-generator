# LINE 贴图批量下载 - 浏览器自动化方案

两种技术方案对比，选择适合你的方式：

---

## 方案对比

| 特性 | 方案 A: Selenium | 方案 B: browser-use CLI |
|------|------------------|-------------------------|
| **技术栈** | Python + Selenium | browser-use CLI |
| **复杂度** | 中等 | 简单 |
| **安装难度** | 已准备好 | 需要安装（5-10分钟）|
| **浏览器控制** | 代码控制 | 命令行控制 |
| **扩展支持** | ✅ 完全支持 | ✅ 应该支持 |
| **批量处理** | ✅ 已实现 | 需编写脚本 |
| **立即可用** | ✅ 是 | 需先安装 |

---

## 快速选择

### 如果你想立即开始测试 → 选方案 A (Selenium)

```bash
cd /Users/cy/workspace/表情包模板
python3 test_single_sticker.py
```

**优点：**
- 环境已配置好
- 脚本已写好
- 立即可运行

---

### 如果你想要更简洁的控制 → 选方案 B (browser-use)

```bash
# 安装（5-10分钟）
bash /Users/cy/workspace/表情包模板/install_and_test_browser_use.sh

# 然后使用命令行控制
browser-use --browser real --headed open https://store.line.me/stickershop/product/36844/zh-Hant
browser-use state
browser-use click 5
```

**优点：**
- 命令行操作更简单
- 跨步骤保持会话
- 不需要写 Python 代码

---

## 详细说明

### 方案 A: Selenium (推荐立即测试)

**文件位置：**
- `/Users/cy/workspace/表情包模板/test_single_sticker.py` - 测试脚本
- `/Users/cy/workspace/表情包模板/line_sticker_auto_download.py` - 批量脚本

**使用方法：**

```bash
# 1. 测试单个贴图
python3 test_single_sticker.py

# 2. 批量下载（测试成功后）
python3 line_sticker_auto_download.py 150
```

**原理：**
- 启动 Chrome（使用你的 Profile，保留登录态）
- 访问 LINE Store 贴图页面
- 自动查找扩展注入的下载按钮
- 点击按钮触发下载

---

### 方案 B: browser-use CLI

**安装脚本：**
- `/Users/cy/workspace/表情包模板/install_and_test_browser_use.sh`

**安装方法：**

```bash
bash /Users/cy/workspace/表情包模板/install_and_test_browser_use.sh
```

**手动使用：**

```bash
# 打开贴图页面
browser-use --browser real --headed \
  open https://store.line.me/stickershop/product/36844/zh-Hant

# 查看页面元素（找到下载按钮索引）
browser-use state

# 点击按钮（假设索引是 5）
browser-use click 5

# 等待下载完成后关闭
sleep 5
browser-use close
```

---

## 关键问题：扩展按钮能否被识别？

无论哪种方案，都需要验证：**能否找到 LineStickerPacker 扩展注入的下载按钮**

### 测试步骤：

1. **手动确认**
   - 打开 Chrome
   - 访问 https://store.line.me/stickershop/product/36844/zh-Hant
   - 确认页面顶部有绿色下载按钮（Android/iPhone 2x/PC）

2. **运行自动化测试**
   - 使用 Selenium 或 browser-use 打开同一页面
   - 查看是否能识别到这些按钮
   - 截图确认

3. **如果找不到按钮**
   - 可能需要等待扩展加载
   - 或调整元素选择器
   - 告诉我具体情况，我来调整

---

## 推荐工作流程

### 第一次测试（建议）

```bash
# 使用 Selenium 脚本快速验证
python3 /Users/cy/workspace/表情包模板/test_single_sticker.py
```

脚本会：
1. 打开 Chrome
2. 访问贴图页面
3. 查找所有按钮并显示
4. 尝试点击 iPhone 2x 按钮
5. 保存截图供你查看

### 根据结果决定

**如果成功：**
- 可以直接使用 Selenium 批量下载
- 或继续使用 browser-use（如果你喜欢命令行）

**如果失败：**
- 查看截图确认扩展是否加载
- 调整按钮选择器
- 尝试 browser-use 作为替代

---

## 我的建议

**现在立即执行：**

```bash
# 方案 A：快速验证（推荐先做这个）
python3 /Users/cy/workspace/表情包模板/test_single_sticker.py
```

运行后告诉我：
1. 是否成功打开了 Chrome？
2. 是否看到了贴图页面？
3. 是否找到了下载按钮？
4. 是否点击成功？
5. 是否下载了 ZIP 文件？

根据结果，我可以帮你：
- 调整脚本参数
- 优化按钮识别
- 或者转向 browser-use 方案

**你想先尝试哪个？**