# glm-agent-ops — GLM Agent Ops Codex 插件

Agent 元技能插件（v2 多技能合并，阶段 1 试点）：Agent 的自我管理能力——任务后复
盘沉淀与目标进度追踪。纯 Skills 型 Codex 插件（Agent Plugins 1.0.0 +
`.codex-plugin` 兼容清单，身份字段同步），供本地模型调用。两个技能自两个 v1 单技
能插件**原样迁移**（零措辞改动，技能名与触发行为不变）；定位类比官方 superpowers
插件的元技能类（meta-skills），服务 Agent 自身而非终端用户的业务域。

## 技能目录

| 技能 | 触发场景 | 入口脚本 |
|---|---|---|
| glm-task-review | 复盘刚才的任务 / 沉淀经验 / 记录踩坑（高复杂度任务完成后） | 无脚本（纯 SKILL.md 工作流） |
| glm-auto-target-tracker | 目标打卡追踪（学习/健身/工作/创作/习惯图片 → 结构化打卡 → 本地目标日记） | `scripts/track.py`（图片识别 + 打卡解析；`setup.sh` 环境体检） |

两个技能相互独立：task-review 把可复用任务路径沉淀为用户级技能（落盘
`~/.codex/skills/`，属于用户）；auto-target-tracker 以本地视觉模型识别打卡图片，
预览确认后 `--apply` 落盘本地目标日记。零网关凭据、零云调用。

## 目录结构

```
glm-agent-ops/
├── plugin.json                 # Agent Plugins 1.0.0 清单（域级描述 + 关键词并集）
├── .codex-plugin/plugin.json   # Codex 兼容清单（身份字段同步 + skills: ./skills/）
├── README.md
├── LICENSE.txt                 # MIT（版权行按惯例署 Z.ai）
└── skills/                     # 两个技能目录原样迁移
    ├── glm-task-review/            # SKILL.md（复盘沉淀工作流）
    └── glm-auto-target-tracker/    # SKILL.md + scripts/（track.py, setup.sh）
```

## 安装到 Codex

方式一（本地插件目录，最直接）：

```bash
tar -xzf glm-agent-ops.tar.gz -C ~/.codex/plugins/   # 解出 glm-agent-ops/（含 2 个技能）
bash ~/.codex/plugins/glm-agent-ops/skills/glm-auto-target-tracker/scripts/setup.sh
```

方式二（本地 marketplace，便于浏览/启用/禁用）：

```bash
mkdir -p ~/glm-marketplace/.agents/plugins
cp -r glm-agent-ops ~/glm-marketplace/plugins/
# marketplace.json 条目见交付包 marketplace_phase1_fragment.json
```

> 迁移提示：本插件与两个 v1 单技能插件（glm-task-review、glm-auto-target-tracker）
> 技能名相同。安装本插件前请先卸载对应旧插件，避免同名技能重复注册。
