# GLM Codex 插件

全部为本地 Ollama 可用的纯 Skills 型 Codex 插件（Agent Plugins 1.0.0 + `.codex-plugin` 兼容清单，身份字段同步），供本地模型调用，单机直连 localhost 或跨机/内网部署均可（见各插件内 README「远程 Ollama」节）。协议口径：Codex ≥ 0.162 只支持 `wire_api = "responses"`；`ollama` 为保留内置 provider id，自定义 base_url 需换自定义 id（单机 `ollama-local`、跨机 `ollama-remote`）。

## 插件总览

| 插件 | 定位 | 技能数 | 
|---|---|---|---|
| glm-academic | 学术研究 |
| glm-agent-ops | Agent 元技能 | 2 |
| glm-career | 求职全流程 | 5 |
| glm-chart | 数据可视化 | 1 |
| glm-content | 内容生产与写作 | 4 |
| glm-design | 设计与前端资产 | 5 |
| glm-dev | 开发工作流 | 2 | [
| glm-finance | 金融投资 | 2 | 
| glm-gaokao | 高考志愿流水线 | 5 |
| glm-image | 图像工作流 | 4 |
| glm-market | 营销与市场研究 | 3 |
| glm-multimodal | 本地模型多模态 | 4 |
| glm-study | 学习与测验 | 4 |
| glm-web | 网页检索与内容获取 | 5 |

## glm-academic — 学术研究（6 技能，115KB）

AMiner 四技能（付费检索 / 日报 / 深度收集 / 免费检索） + 文献综述 + 研究选题；四 AMiner 技能需 AMINER_API_KEY。

技能目录：

| 技能 |
|---|
| aminer-academic-search |
| aminer-daily-paper |
| aminer-deep-search |
| aminer-free-academic |
| glm-literature-survey |
| glm-research-explorer |

## glm-agent-ops — Agent 元技能（2 技能，12KB）

任务复盘沉淀 + 目标打卡追踪。

技能目录：

| 技能 |
|---|
| glm-task-review |
| glm-auto-target-tracker |

## glm-career — 求职全流程（5 技能，80KB）

简历 / JD 改写 / 面试准备 / 结构化面试设计 / 投递追踪。

技能目录：

| 技能 |
|---|
| glm-resume-builder |
| glm-jd-resume-tailor |
| glm-interview-prep |
| glm-interview-designer |
| glm-job-intent-tracker |

## glm-chart — 数据可视化（1 技能，61KB）

matplotlib / ECharts / D3 / Mermaid 场景化路由（已实测基线）。

技能目录：

| 技能 |
|---|
| glmcharts |


## glm-content — 内容生产与写作（4 技能，74KB）

博客长文 / SEO 文 / 小说分镜 / AI 新闻聚合。

技能目录：

| 技能 |
|---|
| glm-blog-writer |
| glm-seo-content-writer |
| glm-storyboard-manager |
| glm-ai-news-collectors |

## glm-design — 设计与前端资产（5 技能，1362KB）

设计路由 / UI/UX / 视觉基础 / Shader 提取 / 版本快照；体积最大。

技能目录：

| 技能 |
|---|
| glm-design |
| glm-ui-ux-pro-max |
| glm-visual-design-foundations |
| glm-web-shader-extractor |
| glm-version-management |

## glm-dev — 开发工作流（2 技能，13KB）

编码纪律 + Next.js 全栈开发。

技能目录：

| 技能 |
|---|
| glm-coding-agent |
| glm-fullstack-dev |


## glm-finance — 金融投资（2 技能，32KB）

行情综合分析 + 个股决策看板。

技能目录：

| 技能 |
|---|
| glm-finance |
| glm-stock-analysis-skill |


## glm-gaokao — 高考志愿流水线（5 技能，67KB）

信息采集 → 志愿表 → 专业 → 院校 → HTML 报告五步流水线。

技能目录：

| 技能 |
|---|
| glm-gaokao-collect-student-info |
| glm-gaokao-fetch-volunteers |
| glm-gaokao-recommend-majors |
| glm-gaokao-recommend-schools |
| glm-gaokao-generate-report |

## glm-image — 图像工作流（4 技能，25KB）

生成 / 编辑 / 找图 / 理解，零云服务。

技能目录：

| 技能 |
|---|
| glm-image-generation |
| glm-image-edit |
| glm-image-search |
| glm-image-understand |

## glm-market — 营销与市场研究（3 技能，70KB）

八步内容营销 / 23 域知识库 / 50+ 页市场报告。

技能目录：

| 技能 |
|---|
| glm-content-strategy |
| glm-marketing-mode |
| glm-market-research-reports |

## glm-multimodal — 本地模型多模态（4 技能，23KB）

对话 / 视觉 / 语音识别 / 语音合成四适配器，需本地 Ollama。

技能目录：

| 技能 |
|---|
| glm-llm |
| glm-vlm |
| glm-asr |
| glm-tts |

## glm-study — 学习与测验（4 技能，73KB）

督学 / 出题 / 网页练习页 / 速查卡，学习闭环。

技能目录：

| 技能 |
|---|
| glm-study-buddy |
| glm-quiz-mastery |
| glm-quiz-html |
| glm-cheat-sheet |

## glm-web — 网页检索与内容获取（5 技能，63KB）

通用底座：20+ 其他技能的文档引用本插件 CLI，建议优先安装。

技能目录：

| 技能 |
|---|
| glm-web-search |
| glm-web-reader |
| glm-multi-search-engine |
| glm-agent-browser |
| glm-contentanalysis |
