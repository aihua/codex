# glm-design — glm-design Codex 插件

设计与前端资产插件（v2 多技能合并）：设计产物生产与资产管理。路由技能与版本管理互引，版本管理又引用 UI/UX 与视觉基础，五技能合并后跨引用全部内化。体积最大的插件（内含大型参考与示例库）。

## 技能目录（5 个）

| 技能 | 触发场景 |
|---|---|
| glm-design | HTML 设计任务路由（落地页 / 作品集 / 仪表板 / 卡片 / 幻灯片） |
| glm-ui-ux-pro-max | UI/UX 设计智能与实施指导 |
| glm-visual-design-foundations | 字体 / 色彩 / 间距系统 / 图标学 |
| glm-web-shader-extractor | 从真实页面提取 WebGL Shader 效果 |
| glm-version-management | 前端产物版本快照（.html/.jsx/.tsx/.vue） |

## 目录结构

```
glm-design/
├── plugin.json                 # Agent Plugins 1.0.0 清单（域级描述 + 关键词并集）
├── .codex-plugin/plugin.json   # Codex 兼容清单（身份字段同步 + skills: ./skills/）
├── README.md
├── LICENSE.txt                 # MIT（版权行按惯例署 Z.ai）
└── skills/                     # 5 个技能目录（原样迁移，仅完成设计冻结的合规修订与措辞审计）
    ├── glm-design/
    ├── glm-ui-ux-pro-max/
    ├── glm-visual-design-foundations/
    ├── glm-web-shader-extractor/
    └── glm-version-management/
```

## 安装到 Codex

方式一（本地插件目录，最直接）：

```bash
tar -xzf glm-design.tar.gz -C ~/.codex/plugins/   # 解出 glm-design/（含 5 个技能）
```

方式二（本地 marketplace，便于浏览/启用/禁用）：

```bash
mkdir -p ~/glm-marketplace/.agents/plugins
cp -r glm-design ~/glm-marketplace/plugins/
# marketplace.json 条目见交付包 marketplace_v2.json
```


> 迁移提示：本插件与 5 个 v1 单技能插件技能名相同。安装本插件前请先卸载
> 对应旧插件，避免同名技能重复注册；卸载旧插件不影响已生成的输出文件。

