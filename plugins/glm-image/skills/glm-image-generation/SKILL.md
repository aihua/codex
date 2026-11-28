---
name: glm-image-generation
description: "Local procedural image generation for Codex agents: the source image-generation skill's z-ai-web-dev-sdk images.generations.create() and `z-ai image` CLI (cloud diffusion text-to-image) is honestly and equivalently replaced by glmgenimg.py - a Pillow procedural generator (in-process PIL or uv-provisioned) with five style templates (gradient / poster / banner / avatar / card), the source skill's seven-size whitelist, eight palettes, reproducible seeds, Chinese-capable font fallback chain and base64 output parity; semantic text-to-image is explicitly out of local scope with routing guidance to ComfyUI/SD/云服务. 触发场景：封面底图 / 海报 / 横幅 hero / 头像 / 卡片封面 / 占位图。配合本地 Ollama 模型编排。"
metadata:
  version: "1.0.0"
---

# Image Generation Skill（本地 Codex 插件形态）

## Codex Deployment Notes

- 插件安装根目录：`~/.codex/plugins/glm-image/`；本技能目录：
  `~/.codex/plugins/glm-image/skills/glm-image-generation/`。下文
  `scripts/` 指 `scripts/glmgenimg.py`。
- **z-ai-web-dev-sdk 等效替换审计结论**：源 skill 依赖云端
  `zai.images.generations.create({prompt, size})`（扩散模型文生图）——
  本地不部署该 SDK，且 Ollama 文本模型无文生图能力。等效分两层：

| 源 SDK / CLI 用法 | 本地等效（glmgenimg.py） | 说明 |
|---|---|---|
| `z-ai image -p "…" -o ./cat.png -s 1024x1024` | `glmgenimg.py <风格> -o out.png --size 1024x1024` | 程序化模板生图（非语义文生图） |
| 7 尺寸白名单（1024x1024 等） | `--size` 同白名单（任意宽高亦可） | 1024x1024 / 768x1344 / 864x1152 / 1344x768 / 1152x864 / 1440x720 / 720x1440 |
| prompt 文字内容进画面 | `--title / --subtitle / --text` | 标题、副题、头像字母（poster/banner/card/avatar） |
| 造型控制 | `--palette warm/sunset/cool/ocean/forest/mono/dark/purple` + `--seed` | 8 调色板 + 种子可复现 |
| 响应 `data[0].base64` | `--print-base64` | 输出后打印 base64（对齐源响应形状） |
| Node SDK import | 纯 Python 标准库编排（Pillow 经 uv 或进程内） | 零 pip 预装 |
| **语义级文生图（「花园里的猫」）** | **不在本地能力范围（诚实降级）** | 本地无扩散模型；路由 ComfyUI / SD WebUI / 云端服务，本插件不冒充支持 |

- 风格模板：`gradient`（渐变背景+几何+噪点）/ `poster`（标题海报）/
  `banner`（斜纹横幅 hero）/ `avatar`（字母圆形头像）/
  `card`（卡片封面）。
- 后端解析：系统 python3 已装 PIL → 进程内直跑；否则 `uv run --with
  pillow` 即用即建（用户 uv 管理 Python 依赖）。
- 退出码：`0` 成功 / `1` 用法错误 / `2` 后端缺失或生成失败。
- 输出落**用户工作目录**；插件目录只读。
- **同插件技能路由**：找真实照片素材 → glm-image-search；改已有图 →
  glm-image-edit；理解图片 → glm-image-understand。

---

## Core Capabilities（沿源 skill 的本地程序化子集）

- 封面/底图渐变（多色插值 + 噪点 + 几何描边）
- 标题海报（主/副标题 + 装饰条，中文字体回退链）
- 斜纹横幅 hero（适合 1440x720 网页头图）
- 字母头像（圆形裁剪 + 渐变底，社交默认头像场景）
- 卡片封面（顶部渐变条 + 标题 + 彩色圆弧装饰）
- 7 尺寸白名单 + 8 调色板 + `--seed` 复现 + base64 输出

## 常用工作流

1. **网页 hero 底图**：
   `python3 scripts/glmgenimg.py gradient -o hero.png --size 1440x720 --palette sunset --seed 7`
2. **活动海报**：`glmgenimg.py poster -o poster.png --title "产品发布会" --subtitle "2026.11.30 · 上海" --palette dark --size 864x1152`
3. **默认头像**：`glmgenimg.py avatar -o me.png --text "Z" --palette cool`
4. **文档卡片封面**：`glmgenimg.py card -o cover.png --title "季度报告" --subtitle "Q3 · 2026" --palette mono`
5. **占位图批量**（mock/开发用）：
   `for i in 1 2 3; do glmgenimg.py gradient -o p$i.png --seed $i; done`
6. **base64 输出对齐**：`… --print-base64`（源响应 `data[0].base64`）。

## 尺寸白名单（沿源 skill）

`1024x1024`（方）· `768x1344`（竖）· `864x1152`（竖）· `1344x768`
（横）· `1152x864`（横）· `1440x720`（宽横 banner 首选）· `720x1440`
（长竖）。

## 中文字体说明

标题/副标题使用系统字体回退链（PingFang → Hiragino → Songti → Arial
Unicode → DejaVu）。macOS 中文开箱可用；Linux 服务器装 Noto Sans CJK
或思源黑体后可用。

## 故障排查

| 症状 | 处置 |
|---|---|
| exit 2 + 无 Pillow 亦无 uv | `brew install uv`（即用即建临时环境） |
| 中文标题变方块 | 系统缺中文字体（见上节） |
| 想要「一只在花园里玩的猫」 | 本地链不支持语义文生图：路由 ComfyUI/SD WebUI/云端服务（诚实降级） |
| 每次结果不同想复现 | 传 `--seed` 固定 |
| 需要更精细排版 | 生成底图后用 glm-image-edit 加水印/标注二次加工 |
