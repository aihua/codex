# glm-dev — glm-dev Codex 插件

开发工作流插件（v2 多技能合并）：编码工作流纪律引用全栈开发，合并为「纪律管流程、全栈管实现」的开发插件。

## 技能目录（2 个）

| 技能 | 触发场景 |
|---|---|
| glm-coding-agent | 结构化编码任务（计划 → 实现 → 验证 → 测试） |
| glm-fullstack-dev | Next.js 16 全栈应用（TypeScript / Tailwind / Prisma） |

## 目录结构

```
glm-dev/
├── plugin.json                 # Agent Plugins 1.0.0 清单（域级描述 + 关键词并集）
├── .codex-plugin/plugin.json   # Codex 兼容清单（身份字段同步 + skills: ./skills/）
├── README.md
├── LICENSE.txt                 # MIT（版权行按惯例署 Z.ai）
└── skills/                     # 2 个技能目录（原样迁移，仅完成设计冻结的合规修订与措辞审计）
    ├── glm-coding-agent/
    └── glm-fullstack-dev/
```

## 安装到 Codex

方式一（本地插件目录，最直接）：

```bash
tar -xzf glm-dev.tar.gz -C ~/.codex/plugins/   # 解出 glm-dev/（含 2 个技能）
```

方式二（本地 marketplace，便于浏览/启用/禁用）：

```bash
mkdir -p ~/glm-marketplace/.agents/plugins
cp -r glm-dev ~/glm-marketplace/plugins/
# marketplace.json 条目见交付包 marketplace_v2.json
```


> 迁移提示：本插件与 2 个 v1 单技能插件技能名相同。安装本插件前请先卸载
> 对应旧插件，避免同名技能重复注册；卸载旧插件不影响已生成的输出文件。

