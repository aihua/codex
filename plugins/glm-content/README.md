# glm-content — glm-content Codex 插件

内容生产与写作插件（v2 多技能合并）：博客长文、SEO 优化文、小说分镜管理、AI 新闻聚合。新闻聚合技能的搜索执行路由到 glm-web 插件技能（若未安装则如实告知，不得编造新闻）。

## 技能目录（4 个）

| 技能 | 触发场景 |
|---|---|
| glm-blog-writer | 博客长文 / 风格档案写作 |
| glm-seo-content-writer | SEO 文章 / 关键词优化 / 本地审计（seocheck.py） |
| glm-storyboard-manager | 小说/剧本分镜 / 角色管理 / 一致性检查 |
| glm-ai-news-collectors | AI 新闻聚合 / 热度分级周报 |

## 目录结构

```
glm-content/
├── plugin.json                 # Agent Plugins 1.0.0 清单（域级描述 + 关键词并集）
├── .codex-plugin/plugin.json   # Codex 兼容清单（身份字段同步 + skills: ./skills/）
├── README.md
├── LICENSE.txt                 # MIT（版权行按惯例署 Z.ai）
└── skills/                     # 4 个技能目录（原样迁移，仅完成设计冻结的合规修订与措辞审计）
    ├── glm-blog-writer/
    ├── glm-seo-content-writer/
    ├── glm-storyboard-manager/
    └── glm-ai-news-collectors/
```

## 安装到 Codex

方式一（本地插件目录，最直接）：

```bash
tar -xzf glm-content.tar.gz -C ~/.codex/plugins/   # 解出 glm-content/（含 4 个技能）
```

方式二（本地 marketplace，便于浏览/启用/禁用）：

```bash
mkdir -p ~/glm-marketplace/.agents/plugins
cp -r glm-content ~/glm-marketplace/plugins/
# marketplace.json 条目见交付包 marketplace_v2.json
```


> 迁移提示：本插件与 4 个 v1 单技能插件技能名相同。安装本插件前请先卸载
> 对应旧插件，避免同名技能重复注册；卸载旧插件不影响已生成的输出文件。

