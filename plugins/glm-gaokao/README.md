# glm-gaokao — GLM Gaokao Advisor Codex 插件

高考志愿推荐流水线插件（v2 多技能合并，阶段 1 试点）：一次安装获得端到端志愿填报
能力——考生信息采集 → 志愿表获取 → 专业推荐 → 院校推荐 → HTML 报告生成。纯
Skills 型 Codex 插件（Agent Plugins 1.0.0 + `.codex-plugin` 兼容清单，身份字段同
步），供本地模型调用。五个技能自五个 v1 单技能插件**原样迁移**（零措辞改动，技能
名与触发行为与分别安装旧插件时完全一致）；五技能两两互引构成完整流水线，合并后
全部技能间引用都在本插件内部，无跨插件依赖。

## 技能目录

| 技能 | 步 | 触发场景 | 入口脚本 |
|---|---|---|---|
| glm-gaokao-collect-student-info | 1 | 高考志愿咨询开场 / 考生信息登记（省份、分数、选科等） | `scripts/student_check.py`（输出体检） |
| glm-gaokao-fetch-volunteers | 2 | 获取推荐志愿表 / 拉一份冲稳保志愿 | `scripts/fetch_volunteers.py` + `build_api_request.py`（`province_config.py` 提供分省参数） |
| glm-gaokao-recommend-majors | 3 | 推荐专业 / 选什么专业 / 就业方向分析 | `scripts/check_recommendation.py`（一致性体检） |
| glm-gaokao-recommend-schools | 4 | 推荐院校 / 冲稳保院校布局 | `scripts/check_recommendation.py`（一致性体检） |
| glm-gaokao-generate-report | 5 | 生成志愿填报报告 / 出一份 HTML 志愿报告 | `scripts/merge_analysis.py` + `generate_html.py`（模板 `templates/volunteer_report.html`） |

数据在五步间以 `output/student.json` → `output/parsed.json` → 推荐 JSON → HTML 报告
串联（详见各技能 SKILL.md）。零 SDK、零 API key；仅第二步调用宿主平台公网志愿 API
（免 key），其余各步零网络出口。

## 目录结构

```
glm-gaokao/
├── plugin.json                 # Agent Plugins 1.0.0 清单（域级描述 + 关键词并集）
├── .codex-plugin/plugin.json   # Codex 兼容清单（身份字段同步 + skills: ./skills/）
├── README.md
├── LICENSE.txt                 # MIT（版权行按惯例署 Z.ai）
└── skills/                     # 五个技能目录原样迁移（SKILL.md/scripts/references/examples/templates）
    ├── glm-gaokao-collect-student-info/
    ├── glm-gaokao-fetch-volunteers/
    ├── glm-gaokao-recommend-majors/
    ├── glm-gaokao-recommend-schools/
    └── glm-gaokao-generate-report/
```

## 安装到 Codex

方式一（本地插件目录，最直接）：

```bash
tar -xzf glm-gaokao.tar.gz -C ~/.codex/plugins/   # 解出 glm-gaokao/（含 5 个技能）
# 按需运行各技能的 scripts/setup.sh（离线环境体检；第五步报告渲染涉及 uv 依赖时运行）
```

方式二（本地 marketplace，便于浏览/启用/禁用）：

```bash
mkdir -p ~/glm-marketplace/.agents/plugins
cp -r glm-gaokao ~/glm-marketplace/plugins/
# marketplace.json 条目见交付包 marketplace_phase1_fragment.json
```

> 迁移提示：本插件与五个 v1 单技能插件（glm-gaokao-*）技能名相同。安装本插件前请
> 先卸载对应旧插件，避免同名技能重复注册；卸载旧插件不影响已生成的输出文件。
