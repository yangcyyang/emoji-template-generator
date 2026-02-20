#!/bin/bash
# browser-use CLI 安装和测试脚本
# 用于自动下载 LINE 贴图

set -e

echo "🚀 browser-use CLI 安装和测试脚本"
echo "======================================"
echo ""

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查 Python 3.11+
echo "1️⃣ 检查 Python 版本..."
if command -v python3.11 &> /dev/null; then
    PYTHON="python3.11"
elif command -v python3.12 &> /dev/null; then
    PYTHON="python3.12"
else
    echo -e "${RED}❌ 需要 Python 3.11 或更高版本${NC}"
    echo "请安装: brew install python@3.11"
    exit 1
fi

echo -e "${GREEN}✅ 使用 Python: $($PYTHON --version)${NC}"

# 安装 browser-use
echo ""
echo "2️⃣ 安装 browser-use CLI..."
echo "   这可能需要几分钟..."
$PYTHON -m pip install "browser-use[cli]" --quiet

# 验证安装
echo ""
echo "3️⃣ 验证安装..."
if command -v browser-use &> /dev/null; then
    echo -e "${GREEN}✅ browser-use 安装成功${NC}"
    browser-use --version
else
    echo -e "${YELLOW}⚠️ browser-use 命令未找到，尝试使用 Python 模块方式${NC}"
    $PYTHON -m browser_use --version || true
fi

# 安装浏览器依赖
echo ""
echo "4️⃣ 安装浏览器依赖..."
browser-use install || echo -e "${YELLOW}⚠️ 浏览器安装可能需要手动完成${NC}"

# 运行测试
echo ""
echo "5️⃣ 运行 LINE 贴图下载测试..."
echo "   将打开 Chrome 浏览器访问 LINE Store..."
echo ""

# 创建测试脚本
cat > /tmp/test_line_sticker.py << 'PYEOF'
import subprocess
import time
import sys

def run_cmd(cmd, wait=2):
    """运行命令并等待"""
    print(f"\n📝 执行: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    time.sleep(wait)
    return result

# 测试配置
STICKER_ID = "36844"
URL = f"https://store.line.me/stickershop/product/{STICKER_ID}/zh-Hant"

print("🎯 LINE 贴图自动下载测试")
print(f"贴图 ID: {STICKER_ID}")
print("=" * 60)

# 1. 打开浏览器
run_cmd(f'browser-use --browser real --headed open "{URL}"', wait=5)

# 2. 获取页面状态
print("\n📄 页面元素列表:")
result = run_cmd('browser-use state', wait=3)

# 保存状态到文件
run_cmd('browser-use state > /tmp/browser_state.txt', wait=1)

# 3. 截图
run_cmd('browser-use screenshot /tmp/line_page.png', wait=2)

# 4. 尝试查找并点击下载按钮
# 注意：这里需要根据实际 state 输出调整索引
print("\n🖱️ 尝试点击可能的下载按钮...")
print("请查看上面的元素列表，找到 iPhone/Android/PC 按钮的索引")

# 5. 保持浏览器打开，让用户手动操作
print("\n⏳ 浏览器将保持打开 30 秒...")
print("请手动查看页面，确认扩展按钮是否可见")
time.sleep(30)

# 6. 关闭浏览器
run_cmd('browser-use close')

print("\n✅ 测试完成!")
print("请检查:")
print("  - /tmp/browser_state.txt (页面元素列表)")
print("  - /tmp/line_page.png (页面截图)")
PYEOF

# 运行测试
$PYTHON /tmp/test_line_sticker.py

echo ""
echo "======================================"
echo -e "${GREEN}✅ 安装和测试完成!${NC}"
echo ""
echo "如果测试成功，可以使用以下命令手动控制:"
echo "  browser-use --browser real --headed open <URL>"
echo "  browser-use state"
echo "  browser-use click <索引>"
echo ""
echo "或者使用 Python 脚本批量处理。"
