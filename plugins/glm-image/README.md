# glm-image — glm-image Codex 插件

图像工作流插件（v2 多技能合并）：生成、编辑、找图、理解四技能构成完整图像工作流，全部本地确定性/本地模型实现，零云服务。四技能互引并与其他域技能跨插件协作（若已安装）。

## 技能目录（4 个）

| 技能 | 触发场景 |
|---|---|
| glm-image-generation | 程序化生成图片 / 徽章 / 排版图 |
| glm-image-edit | 确定性编辑（缩放 / 裁剪 / 合成 / 标注） |
| glm-image-search | 找真实照片素材 / 本地图片检索 |
| glm-image-understand | 静态图片内容理解 |

## 目录结构

```
glm-image/
├── plugin.json                 # Agent Plugins 1.0.0 清单（域级描述 + 关键词并集）
├── .codex-plugin/plugin.json   # Codex 兼容清单（身份字段同步 + skills: ./skills/）
├── README.md
├── LICENSE.txt                 # MIT（版权行按惯例署 Z.ai）
└── skills/                     # 4 个技能目录（原样迁移，仅完成设计冻结的合规修订与措辞审计）
    ├── glm-image-generation/
    ├── glm-image-edit/
    ├── glm-image-search/
    └── glm-image-understand/
```

## 安装到 Codex

方式一（本地插件目录，最直接）：

```bash
tar -xzf glm-image.tar.gz -C ~/.codex/plugins/   # 解出 glm-image/（含 4 个技能）
```

方式二（本地 marketplace，便于浏览/启用/禁用）：

```bash
mkdir -p ~/glm-marketplace/.agents/plugins
cp -r glm-image ~/glm-marketplace/plugins/
# marketplace.json 条目见交付包 marketplace_v2.json
```


> 迁移提示：本插件与 4 个 v1 单技能插件技能名相同。安装本插件前请先卸载
> 对应旧插件，避免同名技能重复注册；卸载旧插件不影响已生成的输出文件。

