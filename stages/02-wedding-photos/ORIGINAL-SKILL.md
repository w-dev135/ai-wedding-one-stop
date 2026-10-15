---
name: ai-wedding-photo-skill
description: 专用于生成多风格、高保真双人AI婚纱照的智能体技能（适配 WorkBuddy / Claude Code / Trae / Cursor）。当用户上传双人合照或两张单人照，并要求生成AI婚纱照、情侣写真或多风格婚纱摄影成片画廊时触发此技能。
version: 2.0.0
license: MIT
---

# AI 婚纱照生成与沉浸式选片画廊专家 (AI Wedding Photo Studio Skill v2.0)

将用户上传的双人照片转化为多款高审美、电影级、拒绝“影楼塑料感”的 AI 婚纱照成片，并交付**纯视觉、全屏左右滑动的沉浸式选片画廊（Horizontal Swipe Photo Gallery）**。

---

## 核心铁律 (CRITICAL RULES - 严禁违反)

1. **必须先真实生图，再渲染画廊**：
   - 严禁在未生成真实图片文件的情况下直接生成 HTML 画廊！
   - 严禁在 HTML 中使用不存在的虚假占位路径（导致出现破损裂图图标 `<img>`）。
   - 如果环境支持生图工具（MCP / 内置生图 API / 脚本生图），必须先将所有风格的婚纱照**真实生成并保存到本地目录（或转为 Base64 / 真实有效 URL）**，再注入画廊。
2. **画廊必须是「纯图片左右滑动选片台」，禁止堆砌大段文字卡片**：
   - 选片画廊（`wedding_lookbook.html`）的首要且唯一核心是**展示生成的婚纱照大图**，供用户左右滑动（Swipe / Carousel / 键盘方向键切换）沉浸式看片与选片（加星收藏 ♥）。
   - **禁止**在画廊首屏放置冗长的「双人特征锚点大文本框」，**禁止**在图片下方直接铺开大段英文 Prompt 代码块喧宾夺主（参数与 Prompt 仅允许收纳在右上角极简的 `ⓘ 机位信息` 悬浮气泡或可折叠抽屉中）。

---

## 核心工作流 (4-Step Workflow)

### Step 1：原图视觉审计与双人特征建模 (Facial & Bone Structure Modeling)

收到用户上传的照片后，调用多模态视觉能力执行「双人特征审计」：

1. **参照规范**：读取 `references/face-consistency-guide.md`，提取新郎（Subject A）与新娘（Subject B）的骨相与标志性特征（脸型、眉眼、发型、是否戴眼镜等）。
2. **风格确认**：若用户未指定具体风格，默认一次性生成 4–6 款经典反差风格（或由用户从 `S1-S8` 中指定）：
   - `S1` **森系纪实松弛感**（轻婚纱 / 逆光丁达尔 / 抓拍大笑）
   - `S2` **王家卫复古港风**（丝绒礼服 / 霓虹光影 / 胶片抽帧感）
   - `S3` **新中式东方雅韵**（宋锦霞帔 / 红墙竹影 / 工笔留白）
   - `S4` **极简韩式光影主纱**（重工缎面主纱 / 几何光影 / 高级灰阶）
   - `S5` **冰岛旷野公路旅拍**（飘逸长头纱 / 黑沙滩蓝调时刻 / 史诗广角）
   - `S6` **赫本黑金复古画报**（黑色丝绒礼服 / 珍珠礼帽 / 经典蝴蝶光）
   - `S7` **南法庄园莫奈油画**（蕾丝鱼尾纱 / 绣球花海 / 柔焦暖阳）
   - `S8` **街头夜景机顶直闪**（短款蓬蓬纱 / 皮衣墨镜混搭 / 富士胶片颗粒）

### Step 2：防串脸提示词组装 (Prompt Assembly)

读取 `references/style-library.md` 中对应风格的完整配方，按空间分区公式组装生图指令：

```text
[Spatial Split & Composition] + [Subject A (Groom): Left/Foreground + Facial Anchor + Attire] + [Subject B (Bride): Right/Background + Facial Anchor + Attire] + [Candid Interaction] + [Lighting & Film Stock] + [Anti-Blending Constraints]
```

### Step 3：批量真实生图执行 (Actual Image Generation)

1. **调用生图工具**：使用当前 Agent 环境的图像生成能力（传入原图作为人物面部参考 + 组装好的 Prompt），为每个选定风格生成 **3:4 竖幅高清婚纱照**（建议每个风格生成 1-2 张）。
2. **校验文件落盘**：确认每张图片均已成功生成并保存为本地文件（如 `./photos/S1_forest.jpg`）或已转为 Base64 Data URI，确保在浏览器中 100% 可正常加载显示，绝对不出现裂图！

### Step 4：生成「全屏左右滑动」沉浸式选片画廊 (Swipeable Photo Gallery Delivery)

严格按照 `references/lookbook-gallery-template.md` 中的 HTML 代码模板（或调用 `scripts/generate_wedding_photos.py`），将生成的真实婚纱照打包为 `wedding_lookbook.html`：

- **交互体验**：
  - **主舞台横向滑块（3D Coverflow / CSS Scroll-Snap 轮播）**：全屏聚焦婚纱照成片本身，支持**鼠标拖拽滑动、触控板左右横滑、左右箭头按钮、键盘 `←` `→` 方向键丝滑切图**。
  - **底部缩略图胶片条（Filmstrip）**：底部一排小图预览，点击任意缩略图瞬间平滑滚动至对应大图。
  - **选片心愿单（♥ 入选标记）**：每张照片右下角提供「♥ 选入相册」按钮，支持一键筛选「仅看已选成片」并导出选片结果。
  - **全屏灯箱放大（Lightbox Zoom）**：双击或点击放大镜可全屏检视面部与婚纱细节。
