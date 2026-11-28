# 本地工具链（定时器 / glm-web 插件技能 CLI / 环境探测）

> SKILL.md「本地形态总纲」的细则。装定时器或调 CLI 前读，读完即用。

## 一、定时器：launchd / crontab + codex exec

Codex CLI 无内置 cron 工具（原宿主 `create_cron_job` 无等效 API）。
定时晨间推送/晚间复盘用 **macOS launchd（首选）或 crontab** 触发
**`codex exec`** 非交互会话实现。

### 通用要点

- **任务名固定**（删除时按名定位）：`StudyBuddy 晨间推送` /
  `StudyBuddy 晚间复盘` / `StudyBuddy 项目生成回查`
- 触发时间必须来自用户明确回复（铁律四），时区按用户所在地
  （Asia/Shanghai）
- `codex exec` 用与用户一致的 profile（如 local）与工作目录（USER.md
  所在目录），模型加载本技能后按 message 指令执行
- **装不上不阻断**：如实告知 + 给手动形态（早/晚对模型说一句"晨间推送"
  / "晚间复盘"即可触发同一流程）；跨会话状态靠 SKILL.md「未完成检查」
  兜底

### launchd 样例（macOS 首选）

`~/Library/LaunchAgents/com.studybuddy.morning.plist`：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
 "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.studybuddy.morning</string>
  <key>Comment</key><string>StudyBuddy 晨间推送</string>
  <key>ProgramArguments</key>
  <array>
    <string>/opt/ollama/0.40.16/../..//usr/bin/env</string>
    <string>codex</string>
    <string>exec</string>
    <string>--profile</string><string>local</string>
    <string>-C</string><string>/data/repo/study</string>
    <string>"现在是晨间推送时间。按 reporting.md 的晨间推送格式，读 USER.md 组装今天 DAY 的待学清单并输出。"</string>
  </array>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key><integer>8</integer>
    <key>Minute</key><integer>0</integer>
  </dict>
</dict>
</plist>
```

装/卸：

```bash
launchctl load   ~/Library/LaunchAgents/com.studybuddy.morning.plist   # 装
launchctl unload ~/Library/LaunchAgents/com.studybuddy.morning.plist   # 删
rm ~/Library/LaunchAgents/com.studybuddy.morning.plist                 # 清理
# 晚间版：Label 改 com.studybuddy.evening、Comment 改 StudyBuddy 晚间复盘、
# Hour 按用户时间、message 改晚间复盘指令
```

> ⚠️ ProgramArguments 第一个串按用户实际 PATH 解析（`command -v codex`），
  上面是占位示意；`-C` 指向 USER.md 所在工作目录。

### crontab 样例（通用兜底）

```cron
# StudyBuddy 晨间推送（任务名，删除按此定位）
0  8 * * * cd /data/repo/study && codex exec --profile local "现在是晨间推送时间。按 reporting.md 的晨间推送格式，读 USER.md 组装今天 DAY 的待学清单并输出。"
# StudyBuddy 晚间复盘（任务名，删除按此定位）
0 22 * * * cd /data/repo/study && codex exec --profile local "现在是晚间复盘时间。读 USER.md，问用户当日答题战绩（非交互模式拿不到回复时如实记录'待结算'），按 reporting.md 晚间复盘格式输出。"
```

### 一次性回查（原"10 分钟回查"的本地等效）

`codex exec` 触发时间不可控精确到分钟时，**降级为会话内等待 + 下次会话
兜底**：步骤2 拆完知识点直接连续走步骤3 排表（本地生成无云端延迟，
原 10 分钟等待是为云端异步生成设计的，本地形态不需要）；若用户中途离
线，靠「未完成检查」①② 在下次会话补齐。**不要为此建长轮询脚本。**

### 删除定时器（用户明确停学时）

```bash
launchctl unload ~/Library/LaunchAgents/com.studybuddy.{morning,evening}.plist
rm ~/Library/LaunchAgents/com.studybuddy.{morning,evening}.plist
crontab -l | grep -v "StudyBuddy" | crontab -   # crontab 形态清理
```

## 二、glm-web 插件技能 CLI（铁律一的执行件）

### glm-web-search（搜索，glmws.py）

```bash
python3 ~/.codex/plugins/glm-web/skills/glm-web-search/scripts/glmws.py \
  search "<关键词>" -n 8
```

- 输出结果列表（标题/URL/摘要）；加 `--json` 机读
- 退出码：0 成功；1 引擎层失败（转述 stderr 的 hint，不要自猜原因）；
  2 网络不可达（沙箱/代理问题 → 建议用户查 Codex 沙箱配置）
- 中文关键词直接可用；引擎链 Bing 主力

### glm-web-reader（读正文，glmwr.py）

```bash
python3 ~/.codex/plugins/glm-web/skills/glm-web-reader/scripts/glmwr.py \
  read "<URL>" --markdown > assets/<slug>.md
```

- 输出带标题层级的正文；`--json` 拿结构化
- 退出码：0 成功；1 页面不可读（4xx/5xx）；2 网络不可达
- 步骤1.5 的资料存档就用这条：`assets/<slug>.md` 每链接一份

### 路径解析顺序

1. setup.sh 探测结果（`~/.codex/plugins/glm-web/...` 标准落位）
2. 探测不到 → 用户自定义安装路径（问一次，记在 USER.md 头部备注区）
3. 都没有 → 降级：请用户直接粘贴资料内容，**绝不编造资料**

## 三、等效映射总表（原宿主工具 → 本地形态）

| 原调用 | 本地等效 | 落点 |
|---|---|---|
| `study_buddy.create_project(资料)` | 模型通读资料拆知识点树（30 分钟~2 小时粒度） | USER.md 项目块 + 叶子列表 |
| `study_buddy.list_leaves(project_id)` | USER.md 该项目的叶子列表就是清单（写入时已含） | USER.md |
| `study_buddy.project_status` | 无云端异步 → 无需轮询（见"一次性回查"节） | — |
| `study_buddy.exam_take(knowledge_ids)` | 模型当场出题写 `quiz/quiz-YYYY-MM-DD.md` + 会话输出 | quiz/ |
| `study_buddy_supervise.study_check` | 晚间问用户战绩（口述）+ 当日练习对答案记录合并 | USER.md 答对字段 |
| `study_buddy.recommend(方向?)` | 模型基于 USER.md 推理；不足走 glmws.py 搜索 | 会话输出 |
| `create_cron_job`（晨/晚/回查） | launchd/crontab + `codex exec`（上文样例） | ~/Library/LaunchAgents 或 crontab |
| `list_cron_jobs` / `delete_cron_job` | `launchctl list | grep studybuddy` / 按任务名删（上文命令） | 同上 |
| `web-search` / `web-reader` 技能 | glmws.py / glmwr.py（上文 CLI） | — |
| `qingyan-research` + `pdf` 技能 | glmwr.py 抓正文存 `assets/<slug>.md`（无需 HTML→PDF 链路，markdown 即学习资料） | assets/ |
| `share_url`（云端项目链接） | 本地产物路径（USER.md/quiz/report 文件） | 铁律三的本地形态 |
| `quiz-mastery` / `cheat-sheet` 分流 | 本技能边界内直接处理（出题/Cheatsheet 本身就是督学流程一部分）；独立测验产品需求时如实说明边界 | — |
