#!/bin/bash
# GitHub 部署配置脚本

echo "=========================================="
echo "🚀 GitHub 自动部署配置"
echo "=========================================="
echo ""

# 检查 git
if ! command -v git &> /dev/null; then
    echo "❌ 请先安装 git"
    exit 1
fi

# 获取 GitHub 用户名
read -p "你的 GitHub 用户名: " USERNAME
if [ -z "$USERNAME" ]; then
    echo "❌ 用户名不能为空"
    exit 1
fi

# 获取仓库名
read -p "仓库名称 (默认: emoji-template-generator): " REPO
REPO=${REPO:-"emoji-template-generator"}

echo ""
echo "📋 配置信息:"
echo "   用户名: $USERNAME"
echo "   仓库名: $REPO"
echo "   远程地址: https://github.com/$USERNAME/$REPO.git"
echo ""

# 配置 git 远程仓库
cd "$(dirname "$0")"

# 检查是否已有远程仓库
if git remote get-url origin &> /dev/null; then
    echo "📝 更新远程仓库..."
    git remote set-url origin "https://github.com/$USERNAME/$REPO.git"
else
    echo "📝 添加远程仓库..."
    git remote add origin "https://github.com/$USERNAME/$REPO.git"
fi

# 保存到配置文件
python3 -c "
import json
try:
    with open('.git-auto-sync.json', 'r') as f:
        config = json.load(f)
except:
    config = {}
config['github_username'] = '$USERNAME'
config['github_repo'] = '$REPO'
with open('.git-auto-sync.json', 'w') as f:
    json.dump(config, f, indent=2)
print('✅ 配置已保存到 .git-auto-sync.json')
"

echo ""
echo "=========================================="
echo "✅ GitHub 配置完成!"
echo "=========================================="
echo ""
echo "下一步操作:"
echo ""
echo "1️⃣  在 GitHub 上创建仓库:"
echo "   https://github.com/new"
echo "   仓库名: $REPO"
echo "   选择 Public 或 Private"
echo ""
echo "2️⃣  首次推送代码:"
echo "   git push -u origin master"
echo ""
echo "   或使用自动脚本:"
echo "   python3 git-auto-sync.py --push"
echo ""
echo "3️⃣  启动自动同步 (监控文件变化):"
echo "   python3 git-auto-sync.py"
echo ""
echo "📖 其他命令:"
echo "   python3 git-auto-sync.py --once    # 手动同步一次"
echo "   python3 git-auto-sync.py --config  # 修改配置"
echo ""
