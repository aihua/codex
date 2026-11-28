---
name: glm-image-search
description: "Local image search for Codex agents: the source image-search skill's ZAI in-house service CLI (`z-ai image-search`, with OSS re-hosting and guaranteed-reachable links) is equivalently replaced by glmimgsearch.py - a zero-key, pure-stdlib Bing Images HTML scraper that parses iusc result cards and emits the source response schema (original_url / caption / source / original_width / original_height, gl cn/us/jp/kr, count 1-20, --no-rank). Honest difference: no OSS re-hosting - results are direct original-site links, so save important assets locally. 触发场景：找图 / 配图 / 插图 / 封面素材 / moodboard / 参考照片。配合本地 Ollama 模型编排。"
metadata:
  version: "1.0.0"
---

# image-search Skill（本地 Codex 插件形态）

## Codex Deployment Notes

- 插件安装根目录：`~/.codex/plugins/glm-image/`；本技能目录：
  `~/.codex/plugins/glm-image/skills/glm-image-search/`。下文
  `scripts/` 指 `scripts/glmimgsearch.py`。
- **z-ai-web-dev-sdk 等效替换审计结论**：源 skill 的检索走 ZAI 自家图片
  搜索服务（`z-ai image-search` CLI：检索 + OSS 转存 + 生成 caption）——
  本地不部署该 SDK 与服务。等效替换为 **Bing Images HTML 检索**（零
  key、纯标准库、大陆网络可达）：

| 源 CLI 用法 | 本地等效（glmimgsearch.py） | 说明 |
|---|---|---|
| `z-ai image-search -q "…" --count 5` | `glmimgsearch.py -q "…" --count 5` | Bing Images 结果卡 iusc 的 m 属性里取原图直链 |
| `--gl cn/us/jp/kr` | 同名 `--gl`（映射 mkt/setlang） | caption 语言随区域 |
| `--no-rank`（免 caption 提速） | `--no-rank`（caption 置空） | 源旗标保留 |
| `-o results.json` | `-o results.json` | JSON 落盘 |
| 响应字段 original_url/caption/source/original_width/original_height | 同名同义 | schema 逐字段对齐 |
| OSS 转存保证直链可达 | **无 OSS（诚实差异）** | 返回源站原图直链；重要素材随即保存本地 |
| 计费/鉴权（网关注入） | 零 key 公共页面 | 无任何凭证 |

- 结果质量提示：查询用**描述句**而非关键词堆砌；区域影响结果池
  （`--gl us` 偏英文素材）；Bing 按出口 IP 定位市场，同一 `--gl` 在
  不同网络下结果可能漂移。
- 退出码：`0` 成功 / `1` 用法错误 / `2` 网络失败或零结果。
- 输出落**用户工作目录**；插件目录只读。
- **同插件技能路由**：保存/加工素材 → glm-image-edit；理解图片内容 →
  glm-image-understand；程序化生图 → glm-image-generation。

---

## Core Capabilities（沿源 skill）

- 自然语言查询检索网络图片（中英）
- 结果含原图直链、caption、来源域、宽高（可用时）
- 区域化（cn/us/jp/kr）
- 数量控制（1–20，源约束沿用）
- JSON 输出与源 schema 字段级对齐

## 常用工作流

1. **文章配图**：`python3 scripts/glmimgsearch.py -q "a cute orange tabby kitten playing with yarn" --count 5`
2. **中文素材**：`glmimgsearch.py -q "中国传统水墨山水画" --gl cn -o art.json`
3. **英文区 moodboard**：`glmimgsearch.py -q "vintage red sports car on a mountain road" --gl us --count 10 --no-rank`
4. **选图入库**：从 JSON 挑 `original_url` → 素材随即下载保存（重要，
   源站直链可能失效）→ 需要加工用 glm-image-edit。
5. **一次一个概念**：两个不相关主体分两次调用（源 skill 操作纪律沿用）。

## 参数选择（沿源 skill）

- `--query`：描述句；匹配受众语言（中文查询偏中文素材）。
- `--count`：日常 5；定稿 1–3；moodboard 10–20。
- `--no-rank`：不需要 caption 时加速。

## 故障排查

| 症状 | 处置 |
|---|---|
| exit 2 + 无法访问 Bing | 检查网络/代理；大陆网络通常可达（沙箱实测通过） |
| exit 2 + HTTP 403/风控 | 稍后重试；降低频率；换 `--gl` |
| 零结果 | 放宽查询 / 换语言重写 / 调大 --count / 换 --gl |
| 结果相关度低 | 描述句更具体；加风格/场景限定词 |
| original_width/height 为空 | 该结果卡未带尺寸元数据（字段可选，源 schema 同样可空） |
| 直链 404 | 无 OSS 转存的预期差异：改用其他结果，重要素材尽早保存 |
