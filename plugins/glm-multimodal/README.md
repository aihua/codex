# glm-multimodal — glm-multimodal Codex 插件

本地模型多模态能力插件（v2 多技能合并）：四个模型能力适配技能（对话 / 视觉 / 语音识别 / 语音合成），原 z-ai-web-dev-sdk 调用全部替换为本地 Ollama 等效实现。需本地运行 Ollama；四个技能互引成链并在 SKILL.md 内按场景路由。

## 技能目录（4 个）

| 技能 | 触发场景 | 备注 |
|---|---|---|
| glm-llm | 本地模型文本生成 / 对话 | Ollama chat |
| glm-vlm | 看图对话 / 视觉问答 | Ollama vision |
| glm-asr | 语音转文字 / 转写 | 本地音频 |
| glm-tts | 文字转语音 | macOS say 语音 |

## 目录结构

```
glm-multimodal/
├── plugin.json                 # Agent Plugins 1.0.0 清单（域级描述 + 关键词并集）
├── .codex-plugin/plugin.json   # Codex 兼容清单（身份字段同步 + skills: ./skills/）
├── README.md
├── LICENSE.txt                 # MIT（版权行按惯例署 Z.ai）
└── skills/                     # 4 个技能目录（原样迁移，仅完成设计冻结的合规修订与措辞审计）
    ├── glm-llm/
    ├── glm-vlm/
    ├── glm-asr/
    └── glm-tts/
```

## 安装到 Codex

方式一（本地插件目录，最直接）：

```bash
tar -xzf glm-multimodal.tar.gz -C ~/.codex/plugins/   # 解出 glm-multimodal/（含 4 个技能）
```

方式二（本地 marketplace，便于浏览/启用/禁用）：

```bash
mkdir -p ~/glm-marketplace/.agents/plugins
cp -r glm-multimodal ~/glm-marketplace/plugins/
# marketplace.json 条目见交付包 marketplace_v2.json
```


> 迁移提示：本插件与 4 个 v1 单技能插件技能名相同。安装本插件前请先卸载
> 对应旧插件，避免同名技能重复注册；卸载旧插件不影响已生成的输出文件。

