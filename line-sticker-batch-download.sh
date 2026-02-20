#!/bin/bash

# LINE 贴图批量下载工具
# 使用方法: ./line-sticker-batch-download.sh [作者ID] [输出目录]
# 示例: ./line-sticker-batch-download.sh 150 ./downloads

AUTHOR_ID=${1:-150}  # 默认 Fujiko-Pro
OUTPUT_DIR=${2:-"./line_stickers"}
USER_AGENT="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"

# 创建输出目录
mkdir -p "$OUTPUT_DIR"

echo "🚀 开始批量下载 LINE 贴图"
echo "作者 ID: $AUTHOR_ID"
echo "输出目录: $OUTPUT_DIR"
echo "========================================"

# 1. 获取作者所有贴图 ID
echo "📋 正在获取贴图列表..."
STICKER_IDS=$(curl -s -A "$USER_AGENT" \
    "https://store.line.me/stickershop/author/$AUTHOR_ID/zh-Hant" | \
    grep -oE "product/[0-9]+" | \
    sed 's/product\///' | \
    sort -u)

TOTAL=$(echo "$STICKER_IDS" | wc -l)
echo "找到 $TOTAL 个贴图"
echo ""

# 2. 批量下载每个贴图的封面图
count=0
for id in $STICKER_IDS; do
    count=$((count + 1))
    
    # 获取元数据（标题等信息）
    meta=$(curl -s -A "$USER_AGENT" \
        "https://stickershop.line-scdn.net/stickershop/v1/product/$id/LINEStorePC/productInfo.meta" 2>/dev/null)
    
    # 提取标题
    title=$(echo "$meta" | grep -oE '"zh_TW":"[^"]+"' | head -1 | sed 's/"zh_TW":"//;s/"$//')
    if [ -z "$title" ]; then
        title=$(echo "$meta" | grep -oE '"en":"[^"]+"' | head -1 | sed 's/"en":"//;s/"$//')
    fi
    if [ -z "$title" ]; then
        title="sticker_$id"
    fi
    
    # 清理标题中的特殊字符
    safe_title=$(echo "$title" | sed 's/[\/:*?"<>|]/_/g')
    
    echo "[$count/$TOTAL] 下载: $safe_title (ID: $id)"
    
    # 下载封面图
    curl -s -A "$USER_AGENT" \
        -o "$OUTPUT_DIR/${id}_${safe_title}.png" \
        "https://stickershop.line-scdn.net/stickershop/v1/product/$id/LINEStorePC/main.png"
    
    # 检查是否下载成功
    if [ -s "$OUTPUT_DIR/${id}_${safe_title}.png" ]; then
        echo "  ✓ 成功"
    else
        echo "  ✗ 失败"
        rm -f "$OUTPUT_DIR/${id}_${safe_title}.png"
    fi
    
    # 添加延迟避免触发限制
    sleep 0.5
done

echo ""
echo "========================================"
echo "✅ 下载完成！"
echo "共下载 $count 个贴图到: $OUTPUT_DIR"
ls -la "$OUTPUT_DIR" | tail -5
