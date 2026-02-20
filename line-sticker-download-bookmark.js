// LINE 贴图下载书签工具
// 使用方法：
// 1. 复制下面整段代码
// 2. 在 Chrome 中创建新书签（书签栏右键 → 添加网页）
// 3. 名称：LINE贴图下载
// 4. URL：粘贴这段代码（前面加上 javascript:）
// 5. 访问 LINE Store 贴图页面，点击此书签即可下载

javascript:(function(){
    // 获取当前页面 URL 中的 product ID
    const match = location.href.match(/product\/(\d+)/);
    if (!match) {
        alert('请先访问 LINE Store 贴图页面');
        return;
    }
    
    const productId = match[1];
    const stickerName = document.querySelector('h1, .mdCMN38Item01Ttl')?.textContent?.trim() || 'stickers';
    
    // 创建下载界面
    const div = document.createElement('div');
    div.innerHTML = `
        <div style="position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.8);z-index:99999;display:flex;align-items:center;justify-content:center;font-family:sans-serif;">
            <div style="background:white;padding:30px;border-radius:12px;max-width:500px;width:90%;">
                <h2 style="margin:0 0 20px 0;color:#333;">📦 LINE 贴图下载</h2>
                <p style="color:#666;margin-bottom:20px;">贴图: <strong>${stickerName}</strong><br>ID: ${productId}</p>
                
                <div style="margin-bottom:20px;">
                    <label style="display:block;margin-bottom:8px;color:#333;font-weight:bold;">选择平台:</label>
                    <select id="platform" style="width:100%;padding:10px;border:1px solid #ddd;border-radius:6px;">
                        <option value="iphone">iPhone 2x (推荐)</option>
                        <option value="android">Android</option>
                        <option value="pc">PC</option>
                    </select>
                </div>
                
                <div style="margin-bottom:20px;">
                    <label style="display:block;margin-bottom:8px;color:#333;font-weight:bold;">贴图数量:</label>
                    <input type="number" id="count" value="40" min="1" max="100" style="width:100%;padding:10px;border:1px solid #ddd;border-radius:6px;">
                    <small style="color:#999;">大多数贴图有 24 或 40 张</small>
                </div>
                
                <button id="startBtn" style="width:100%;padding:12px;background:#07C160;color:white;border:none;border-radius:6px;font-size:16px;cursor:pointer;">
                    开始下载
                </button>
                
                <div id="progress" style="margin-top:20px;display:none;">
                    <div style="background:#eee;height:20px;border-radius:10px;overflow:hidden;">
                        <div id="bar" style="background:#07C160;height:100%;width:0%;transition:width 0.3s;"></div>
                    </div>
                    <p id="status" style="text-align:center;color:#666;margin-top:10px;">准备下载...</p>
                </div>
                
                <button id="closeBtn" style="width:100%;padding:10px;margin-top:10px;background:#f5f5f5;color:#666;border:none;border-radius:6px;cursor:pointer;">
                    关闭
                </button>
            </div>
        </div>
    `;
    document.body.appendChild(div);
    
    // 关闭按钮
    div.querySelector('#closeBtn').onclick = () => div.remove();
    
    // 开始下载
    div.querySelector('#startBtn').onclick = async () => {
        const platform = div.querySelector('#platform').value;
        const count = parseInt(div.querySelector('#count').value) || 40;
        const progressDiv = div.querySelector('#progress');
        const bar = div.querySelector('#bar');
        const status = div.querySelector('#status');
        
        progressDiv.style.display = 'block';
        
        const downloaded = [];
        const failed = [];
        
        for (let i = 1; i <= count; i++) {
            const num = i.toString().padStart(2, '0');
            const url = `https://stickershop.line-scdn.net/stickershop/v1/product/${productId}/${platform}/stickers/${num}.png`;
            
            try {
                const response = await fetch(url);
                if (response.ok) {
                    const blob = await response.blob();
                    const a = document.createElement('a');
                    a.href = URL.createObjectURL(blob);
                    a.download = `${stickerName}_${num}.png`;
                    a.click();
                    downloaded.push(num);
                    
                    // 延迟避免触发限制
                    await new Promise(r => setTimeout(r, 200));
                } else {
                    failed.push(num);
                }
            } catch (e) {
                failed.push(num);
            }
            
            // 更新进度
            const percent = (i / count) * 100;
            bar.style.width = `${percent}%`;
            status.textContent = `下载中... ${i}/${count} (${downloaded.length} 成功, ${failed.length} 失败)`;
        }
        
        status.textContent = `完成! ${downloaded.length} 张成功, ${failed.length} 张失败`;
        status.style.color = downloaded.length > 0 ? '#07C160' : '#ff4444';
    };
})();
