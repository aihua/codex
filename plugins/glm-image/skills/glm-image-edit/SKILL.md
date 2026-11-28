---
name: glm-image-edit
description: "Local deterministic image editing for Codex agents: the source image-edit skill's z-ai-web-dev-sdk images.generations.edit() (AI prompt-driven editing) is honestly and equivalently replaced by glmimgedit.py - a Pillow pipeline CLI (in-process PIL or provisioned on the fly via uv run --with pillow) covering crop/center-crop, resize incl. the source 7-size whitelist, rotate, flip, grayscale, blur/sharpen, brightness/contrast/saturation, trim, pad, border, watermark, annotation, compositing, format conversion and base64 output parity; semantic AI edits (object replacement) are explicitly out of local scope with routing guidance. 触发场景：图片裁剪缩放 / 批量规格化 / 水印 / 格式转换 / 拼图合成 / 配图后处理。配合本地 Ollama 模型编排。"
metadata:
  version: "1.0.0"
---

# Image Edit Skill（本地 Codex 插件形态）

## Codex Deployment Notes

- 插件安装根目录：`~/.codex/plugins/glm-image/`；本技能目录：
  `~/.codex/plugins/glm-image/skills/glm-image-edit/`。下文 `scripts/`
  指 `scripts/glmimgedit.py`。
- **z-ai-web-dev-sdk 等效替换审计结论**：源 skill 依赖云端
  `zai.images.generations.edit({prompt, images, size})`（语义级 AI 编辑，
  云端扩散模型）——本地不部署该 SDK，且 Ollama 文本模型无图像编辑能力。
  等效分两层：

| 源 SDK / CLI 用法 | 本地等效（glmimgedit.py） | 说明 |
|---|---|---|
| 尺寸调整（size: '1024x1024' 等 7 尺寸） | `edit -i in -o out --resize 1024x1024` | 白名单沿源 skill（另有 --fit 保比缩放、--pad 衬底） |
| 图片变体（variations） | 确定性变换组合：`--rotate/--flip/--grayscale/--blur/--sharpen` | 管线组合可复现（源「变体」的本地可确定性子集） |
| 本地图片输入（base64 data URL） | `-i 本地路径`（CLI 内部处理） | URL 亦可（自动下载） |
| 响应 `data[0].base64` | `--print-base64` | 输出后打印 base64（对齐源响应形状） |
| 多图输入（images 数组） | `--composite overlay.png --x --y --opacity` | 两图合成（本地链的多图语义） |
| **语义级 AI 编辑（prompt：「把猫换成狗」）** | **不在本地能力范围** | 本地无扩散模型；此类需求路由 ComfyUI / SD WebUI / 云端服务（用户自选），本插件不冒充支持 |

- 后端解析：系统 python3 已装 PIL → 进程内直跑；否则 `uv run --with
  pillow` 即用即建临时环境（用户 uv 管理 Python 依赖，零预装、零污染）。
- 退出码：`0` 成功 / `1` 用法错误 / `2` 后端缺失或编辑失败。
- 输出落**用户工作目录**；插件目录只读。
- **同插件技能路由**：分析图片内容 → glm-image-understand；找图 →
  glm-image-search；程序化生图 → glm-image-generation。

---

## Core Capabilities（沿源 skill 的本地可确定性子集）

- 几何：裁剪（像素/居中百分比）、缩放（精确/保比）、旋转、翻转、白边裁剪
- 色彩：灰度、模糊、锐化、亮度/对比度/饱和度
- 版式：衬底留白、加边框、文字水印（5 角落+字号+透明度）、任意位置标注
- 合成：两图叠加（坐标+不透明度）
- 输出：格式由扩展名决定（png/jpg/webp/bmp…）、JPEG 质量、base64 打印

## 操作管线次序（固定）

`trim → crop/crop-center → rotate → flip → resize/fit → 灰度与增强
→ pad/border → watermark/annotate → composite`，再落盘。需要不同次序时
分多次调用串接（每次 -o 的输出作为下次 -i 的输入）。

## 常用工作流

1. **规格化到源 skill 尺寸**：
   `python3 scripts/glmimgedit.py edit -i in.png -o out.png --resize 1344x768`
2. **头像/封面居中裁剪**：`edit -i photo.jpg -o square.jpg --crop-center 80 --resize 1024x1024`
3. **版权水印**：`edit -i art.png -o wm.png --watermark "© 2026 Z.ai" --corner br --font-size 28`
4. **批量规格化**（源批量变体等效）：
   `for f in *.jpg; do glmimgedit.py edit -i "$f" -o "n_$f" --fit 1440x720 --quality 85; done`
5. **两图合成**：`edit -i bg.png -o composed.png --composite logo.png --x 20 --y 20 --opacity 80`
6. **base64 输出对齐**：`… --print-base64`（源响应 `data[0].base64` 的等效）。

## 尺寸白名单（沿源 skill）

`1024x1024`（方）· `768x1344`（竖）· `864x1152`（竖）· `1344x768`
（横）· `1152x864`（横）· `1440x720`（宽横）· `720x1440`（长竖）
——`--resize/--fit` 支持任意 `宽x高`，以上为与源对齐的常用档。

## 故障排查

| 症状 | 处置 |
|---|---|
| exit 2 + 无 Pillow 亦无 uv | `brew install uv`（即用即建临时环境） |
| 中文水印变方块 | 系统缺中文字体：装 PingFang/思源黑体，或检查 /System/Library/Fonts |
| 想要「把猫换成狗」 | 本地链不支持语义编辑（诚实降级）：路由 ComfyUI/SD WebUI/云端服务 |
| rotate 后背景白边 | 默认白底填充；要透明背景先转 PNG 且输入带 alpha |
| 编辑次序不合预期 | 管线次序固定；特殊次序分多次调用串接 |
| exit 2 + 打开失败 | 文件非图片或损坏；`info` 子命令先探 |
