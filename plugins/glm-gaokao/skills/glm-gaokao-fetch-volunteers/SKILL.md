---
name: glm-gaokao-fetch-volunteers
description: "调用高考智能推荐志愿表公网无鉴权接口（纯标准库 urllib，非 SDK 依赖），根据考生基本信息及专业/城市/院校倾向（映射为 API 选填参数）获取冲稳保志愿列表，解析为 parsed.json；内置两阶段调用（batch/list 批次解析 → intelligenceVolunteer 志愿推荐）与 31 省选科模式校验。适用于获取推荐院校、冲稳保志愿表、志愿接口调用。触发场景：获取推荐志愿表 / 拉一份冲稳保志愿 / 调志愿接口 / 志愿推荐列表 / 高考志愿数据。"
metadata:
  version: "1.0.0"
---

# 获取推荐志愿表

本 Skill 是流水线的**第二步**：读取 `student.json`，**提取并映射考生倾向到 API 选填参数**，调用志愿接口，输出 `parsed.json`。

## Codex Deployment Notes

本技能以 Codex 插件形态部署，路径约定：

- 插件安装根目录：`~/.codex/plugins/glm-gaokao-fetch-volunteers/`
- 本技能目录：`~/.codex/plugins/glm-gaokao-fetch-volunteers/skills/glm-gaokao-fetch-volunteers/`
- 下文 `references/`、`examples/`、`scripts/` 均指该技能目录内的子目录；`api_request.json`、`parsed.json` 等运行产物落在**用户工作目录** `output/`，插件目录只读。
- **零 pip 依赖**：三个脚本均为 Python 标准库（urllib/json/argparse）。源 skill 的 `python3 -m venv` + `pip install -r requirements.txt` 环境准备**整段移除**——requirements.txt 中的 requests/jinja2 实际未被脚本使用，勿再建 venv。
- **API 为公网无鉴权 HTTP 接口，非任何 SDK 依赖**（无需部署厂商 web-dev SDK）：`https://publicapi.chatglm.cn/chatglm_public/skill`（POST /zp/volunteer/intelligenceVolunteer、GET /zp/volunteer/batch/list），无认证、无 key、纯 urllib 直调；用户本地**不需要部署任何 SDK**。默认 BASE_URL 写在脚本内，可用 `--base-url` 参数或 `ZP_API_BASE_URL` 环境变量覆盖/切换镜像。这是本技能唯一的网络出口，且仅经用户显式发起的调用。
- **流水线上下游为同门姊妹插件**（各自独立安装，未装齐时本步仍可独立跑，只要有 student.json）：
  - 上游 Step1：glm-gaokao-collect-student-info 插件产出 `output/student.json`（未装时手工按其 `examples/student_template.json` 结构准备亦可）。
  - 下游 Step3/4/5：glm-gaokao-recommend-majors、glm-gaokao-recommend-schools、glm-gaokao-generate-report 消费 `parsed.json`。

## 上下游

- **上游**：glm-gaokao-collect-student-info 插件（Step1）→ `student.json`
- **下游**：glm-gaokao-recommend-majors（Step3）、glm-gaokao-recommend-schools（Step4）、glm-gaokao-generate-report（Step5）插件

## 执行步骤

### 1. 从辅助信息提取倾向（Agent 必做）

读取 `student.json`，根据 `references/preference-mapping.md` 将考生倾向补全/写入以下字段：

| 字段 | 映射到 API |
|------|-----------|
| `preferred_universities` | `universitys` |
| `preferred_provinces` / `preferred_cities` | `provinces` |
| `preferred_tags` | `tags` |
| `preferred_major_classes` | `majorClass` |

提取来源：`interests`、`career_direction`、`preferred_cities`、`notes` 及对话中的院校/专业/层次偏好。

若 Step1 已结构化写入，本步核对并补全；**调用 API 前倾向字段不得为空数组**（考生无偏好时除外）。

### 2. 构建 API 请求

```bash
python3 ~/.codex/plugins/glm-gaokao-fetch-volunteers/skills/glm-gaokao-fetch-volunteers/scripts/build_api_request.py \
  -i output/student.json \
  -o output/api_request.json \
  --summary output/preference_summary.json
```

脚本将 `preferred_*` 转为 API 选填参数；`preferred_cities` 会自动推导 `provinces`（见 `references/preference-mapping.md`）。

`build_api_request.py` 会调用 `province_config.validate_classify` 校验 `classify` 是否与省份模式匹配。

### 2.5 调用前参数核对（必做）

在调用 API 前，对照 `references/api-reference.md` 核对 `student.json` / `api_request.json`：

| 检查项 | 规则 |
|--------|------|
| `classify` | 新疆→文科/理科；3+1+2 省→物理/历史；3+3 省→综合。**传错会导致批次列表为空** |
| `subjects` | 3+1+2：**完整三科**（首选+两门再选，如 `物理,化学,生物`）；3+3：完整三科；新疆不传；京沪津专科由脚本处理 |
| `gradeType` | **仅北京/上海/天津**填本科或专科；其他省必须为 `null` 或不传 |
| `score` | 新疆**必传**（无一分一段表，仅 rank 无效） |
| `batch` | 可填泛称「本科批」/「专科批」，由 batch/list 解析为各省具体批次名 |
| 西藏 | 测试环境不支持，应退回采集环节说明 |

**批次 batch**：用户侧可填泛称 `本科批` / `专科批`，脚本通过 batch/list 解析为各省具体批次名（如山东 → `普通类一段`）。接口失败时使用 `references/api-reference.md` 中的静态兜底表。

### 3. 调用志愿 API（两阶段：批次 → 志愿列表）

```bash
python3 ~/.codex/plugins/glm-gaokao-fetch-volunteers/skills/glm-gaokao-fetch-volunteers/scripts/fetch_volunteers.py \
  --config output/api_request.json \
  -o output/parsed.json
```

或一步完成（内置构建逻辑）：

```bash
python3 ~/.codex/plugins/glm-gaokao-fetch-volunteers/skills/glm-gaokao-fetch-volunteers/scripts/fetch_volunteers.py \
  --student output/student.json \
  -o output/parsed.json
```

脚本会先调用 `batch/list` 根据分数与选科解析具体 `batch` 和 `volunteerType`，再请求志愿推荐接口。参数规范化由 `scripts/province_config.py` 自动完成。可用 `--no-auto-batch` 关闭自动解析。

**两阶段 SOP**：

```
1. GET  batch/list  →  得到各省可选批次 + volunteerType
2. POST intelligenceVolunteer  →  用选中批次的 batch / volunteerType 拉志愿
```

京沪津在步骤 1 还需传 `gradeType`（脚本按 score / batch 自动推断）。

### 4. 向用户说明

结合 `preference_summary.json` 与 `parsed.json` 的 `stats`，说明：

- 传入了哪些倾向参数（院校/省份/层次/专业类）
- 冲/稳/保各多少所

## API 选填参数说明

| API 字段 | 含义 | 来源 |
|----------|------|------|
| `universitys` | 心仪高校 | `preferred_universities` |
| `provinces` | 省份意向 | `preferred_provinces` 或由城市推导 |
| `tags` | 院校属性 | `preferred_tags`（985/211 等） |
| `majorClass` | 专业类意向 | `preferred_major_classes` |

完整 API 文档见 `references/api-reference.md`。

## 输出结构（parsed.json）

| 字段 | 说明 |
|------|------|
| `profile` | 含传入的选填参数回显 |
| `stats` | 冲/稳/保数量 |
| `schools_by_type` | 分组院校列表 |
| `request` | 实际 API 请求体（含倾向参数） |
| `batch_resolution` | 批次解析来源、选中项与可选项 |

## 故障排查

| 现象 | 处理 |
|------|------|
| 推荐结果与倾向不符 | 检查 `api_request.json` 中选填参数是否正确 |
| 没有可填报的批次 | 查 `references/api-reference.md`；确认 classify 与省份模式一致 |
| 批次列表为空 | classify 错误（如 3+3 省传了物理）— 脚本会明确报错 |
| 西藏考生 | 测试环境不支持，需换省份或等待平台接入 |
| 志愿接口 500 | 查 reference：gradeType/subjects 是否按省传对 |
| 缺少 subjects | 3+3/3+1+2 必填选科；新疆/京沪津专科除外 |
| subjects 只有两门 | 3+1+2 须传**完整三科**（含物理/历史），不能只传化学,生物 |
| 倾向未传入 | 确认 Step1/本步已填写 `preferred_*` 字段 |
| 网络不可达 / 连接被拒 | 公网接口域名不可达——重试一次；仍失败则用 `--base-url` 指向可用镜像或稍后再试；本技能无离线数据源 |

## 附加资源

- `references/preference-mapping.md` — 倾向 → API 参数映射规则
- `references/api-reference.md` — API、选科模式、批次接口踩坑速查
- `scripts/province_config.py` — 各省 classify/subjects/gradeType 校验与规范化
- `examples/api_request_shandong.json` — 含选填参数示例
- 源 skill 另有 31 省批次接口回归脚本（test_batch_api.py，需连续调用公网接口），插件形态不随包分发以免误触发批量调用；省份规则校验已由 `province_config.py` 在本地覆盖
