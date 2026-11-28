# glm-career — glm-career Codex 插件

求职全流程插件（v2 多技能合并）：求职者侧与面试官侧能力兼备——简历生成、JD 定向改写、面试准备、结构化面试设计、投递追踪五个技能两两互引构成完全图，合并后全部互引都在本插件内部。技能自五个 v1 单技能插件迁移（11 项 frontmatter 按 D 类完成 YAML 加固，解析值不变）。

## 技能目录（5 个）

| 技能 | 触发场景 |
|---|---|
| glm-resume-builder | 写简历 / 优化简历 / ATS 关键词 / 多格式导出 |
| glm-jd-resume-tailor | 按 JD 改简历 / 差距分析 |
| glm-interview-prep | 准备面试 / 题库 / 面试备战手册 |
| glm-interview-designer | 设计结构化面试 / 评分量表（面试官侧） |
| glm-job-intent-tracker | 求职意向梳理 / 投递追踪 |

## 目录结构

```
glm-career/
├── plugin.json                 # Agent Plugins 1.0.0 清单（域级描述 + 关键词并集）
├── .codex-plugin/plugin.json   # Codex 兼容清单（身份字段同步 + skills: ./skills/）
├── README.md
├── LICENSE.txt                 # MIT（版权行按惯例署 Z.ai）
└── skills/                     # 5 个技能目录（原样迁移，仅完成设计冻结的合规修订与措辞审计）
    ├── glm-resume-builder/
    ├── glm-jd-resume-tailor/
    ├── glm-interview-prep/
    ├── glm-interview-designer/
    └── glm-job-intent-tracker/
```

## 安装到 Codex

方式一（本地插件目录，最直接）：

```bash
tar -xzf glm-career.tar.gz -C ~/.codex/plugins/   # 解出 glm-career/（含 5 个技能）
```

方式二（本地 marketplace，便于浏览/启用/禁用）：

```bash
mkdir -p ~/glm-marketplace/.agents/plugins
cp -r glm-career ~/glm-marketplace/plugins/
# marketplace.json 条目见交付包 marketplace_v2.json
```


> 迁移提示：本插件与 5 个 v1 单技能插件技能名相同。安装本插件前请先卸载
> 对应旧插件，避免同名技能重复注册；卸载旧插件不影响已生成的输出文件。

