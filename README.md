# 表情包批量处理器

自动化处理表情包集合文件夹，生成四种模板并打包下载。

## 功能特点

- ✅ **批量处理**：自动扫描文件夹内所有子文件夹
- ✅ **四模板输出**：
  - 模板1：头图+9宫格（带头像和标题）
  - 模板2-4：3x5网格（每页15张，支持循环）
- ✅ **智能解析**：自动从文件夹名提取标题和副标题
- ✅ **自动打包**：每个文件夹独立 ZIP + 总包
- ✅ **纯 Python**：无需浏览器，使用 PIL 直接生成图片

## 目录结构

```
表情包模板/
├── auto_processor.py      # 主程序
├── index.html             # 单文件预览版
├── batch-mode.html        # 浏览器批量版
├── config.example.json    # 配置示例
├── 刘欢卡通手书.ttf        # 字体文件
├── wechat-icon.svg        # 微信图标
├── qq-icon.svg           # QQ图标
└── output/               # 输出目录
    ├── 文件夹A/
    │   ├── 01_头图_文件夹A.jpg
    │   ├── 02_网格1_文件夹A.jpg
    │   ├── 03_网格2_文件夹A.jpg
    │   └── 04_网格3_文件夹A.jpg
    ├── 文件夹B/
    │   └── ...
    └── _zip_packages/
        ├── 文件夹A_表情包.zip
        ├── 文件夹B_表情包.zip
        └── 表情包合集_0123_1430.zip  # 总包
```

## 使用方法

### 1. 准备表情包素材

将表情包按文件夹组织：

```
表情包素材/
├── 01 春意慵懒kitty/          # 文件夹名会解析为标题
│   ├── 01.png
│   ├── 02.png
│   └── ... (≥15张)
├── 02 可爱小狗/
│   └── ...
└── 03 搞笑表情包/
    └── ...
```

文件夹命名格式：
- `序号 标题` → 如 `01 春意慵懒kitty`
- `标题·副标题` → 如 `春意慵懒kitty·精选合集`

### 2. 配置

复制配置示例并修改：

```bash
cp config.example.json config.json
```

编辑 `config.json`：

```json
{
  "collection_folder": "/Users/cy/Desktop/表情包素材",  // 素材文件夹路径
  "output_folder": "/Users/cy/workspace/表情包模板/output",  // 输出路径
  "min_images": 15,  // 每文件夹最少图片数
  "templates": {
    "template1": true,   // 是否生成模板1
    "template2": true,   // 是否生成模板2
    "template3": true,   // 是否生成模板3
    "template4": true    // 是否生成模板4
  },
  "font_path": "刘欢卡通手书.ttf",
  "image_quality": 95,
  "canvas_size": [1200, 1600],
  "auto_start": false   // true = 跳过确认直接开始
}
```

### 3. 运行

```bash
# 进入项目目录
cd /Users/cy/workspace/表情包模板

# 运行
python auto_processor.py
```

程序会：
1. 扫描所有子文件夹
2. 显示统计信息
3. 确认后开始处理
4. 生成图片并打包
5. 输出到指定目录

### 4. 获取结果

处理完成后，在 `output/_zip_packages/` 中找到：
- 每个文件夹独立的 ZIP 包
- 总包（包含所有表情包）

## 模板说明

| 模板 | 布局 | 内容 | 用途 |
|-----|------|------|------|
| 模板1 | 头图+3x3网格 | 主图+标题+9张图 | 封面/头图 |
| 模板2 | 3x5网格 | 第1-15张图 | 详情页1 |
| 模板3 | 3x5网格 | 第16-30张图 | 详情页2 |
| 模板4 | 3x5网格 | 第31-45张图 | 详情页3 |

> 注意：图片不足时会循环使用

## 依赖安装

如果缺少依赖，安装以下包：

```bash
pip install pillow selenium
```

或完整环境：

```bash
pip install -r requirements.txt
```

## 浏览器模式（可选）

如需使用浏览器模式预览（非批量处理）：

```bash
python auto_processor.py --browser
```

这会启动 Chrome 并打开 `batch-mode.html` 进行可视化预览。

## 文件夹命名技巧

| 命名方式 | 解析结果 |
|---------|---------|
| `01 春意慵懒kitty` | 标题：春意慵懒kitty |
| `春意慵懒kitty·精选合集` | 标题：春意慵懒kitty，副标题：精选合集 |
| `03_可爱小狗` | 标题：可爱小狗 |

## 常见问题

**Q: 图片数量不足15张怎么办？**  
A: 程序会自动跳过该文件夹（可在配置中修改 `min_images`）

**Q: 可以修改模板样式吗？**  
A: 可以，编辑 `auto_processor.py` 中的 `ImageProcessor` 类

**Q: 支持哪些图片格式？**  
A: jpg, jpeg, png, gif, webp, bmp

**Q: 如何处理大量表情包？**  
A: 程序会自动处理所有符合条件的文件夹，支持数百个文件夹批量处理

## 更新日志

- 2024-01-16: 初始版本，支持 PIL 纯 Python 处理
