# 平台安装与能力适配

核心目录保持 SKILL.md、scripts/、assets/、references/ 同级，执行路径相对当前技能根目录。平台导出仅生成目录，安装由用户或当前 Agent 在有授权的环境完成，不能因导出成功就称安装成功。

## 安装路径与入口

| 平台 | 安装方式 | 触发与核对 |
| --- | --- | --- |
| Claude Code | 用户 ~/.claude/skills/create-wedding-invitation 或项目 .claude/skills/create-wedding-invitation | /create-wedding-invitation 或自然语言触发，检查实际执行输出 |
| Codex CLI / IDE | 用户 ~/.agents/skills/create-wedding-invitation 或项目 .agents/skills/create-wedding-invitation；Work 内已安装技能由宿主管理 | /skills 或 $create-wedding-invitation，确认脚本运行与产物 |
| Gemini CLI | gemini skills install <技能目录>，或 .gemini/skills、.agents/skills 所认可目录 | /skills list，再提出制作任务，遵循宿主授权 |
| WorkBuddy | 按当前版本的技能导入入口安装完整目录；开放平台包使用专属元数据适配 | 核对识别、触发及 Python 执行，导入失败读取平台报错 |
| Gemini 网页版等受限宿主 | 依当前版本实际导入与文件执行能力处理 | 无执行能力时采集资料和输出移交配置，不声称已经构建或发布 |

导出命令：
python3 scripts/export_platform.py --target portable --out <新父目录/create-wedding-invitation>

target 支持 portable、claude、codex、gemini、workbuddy。WorkBuddy 开放平台适配需加 --author <实际发布方>，导出目录补充 display_name、description_zh、description_en、version、author。核心源文件仍保留通用 name/description。不将当前宿主专有接口写入核心生成脚本。

使用 zip 的平台可由当前环境按其要求打包导出目录；用户未请求时不额外交付压缩包，也不改写主技能目录。

## WorkBuddy 包与 GitHub

WorkBuddy 导出包版本为2.1.0，包含完整 scripts/、assets/、references/ 与二维码海报流程。ZIP 内保留一层 create-wedding-invitation/ 文件夹，不混入原始照片、演示项目、缓存、凭据或检查报告。发布方填写实际作者，导出成功仍不代表 WorkBuddy 客户端端到端安装成功。

用户要从 GitHub 安装时，先解压，再把 create-wedding-invitation 文件夹内的 SKILL.md、scripts/、assets/、references/、agents/、requirements.txt 上传到专用仓库根目录；不要仅把 ZIP 上传到代码目录就声称仓库可识别技能。随后按当前 WorkBuddy 的实际导入入口提供仓库链接或完整本地技能目录；平台只接受 ZIP 时选择完整包，并检查技能名称和执行结果。没有客户端时交付包并标记安装待验证，不编造按钮名称或安装路径。

首次使用运行 scripts/doctor.py。Python 3.10+ 是基础；需要照片处理与海报时，按宿主权限在独立环境执行 python -m pip install -r requirements.txt。可选安装 zxing-cpp 做二维码程序解码。字体使用本机中文字体或 --font 指定合法字体，ffmpeg/ffprobe 仅在截取音乐或重新合成配乐时需要。分享海报与线上发布分别检查能力，安装 Skill 本身不会自动提供托管账号、微信分享权限或字体。

## 能力分支

- 可读文件但无法执行：输出已整理配置、素材顺序与待执行命令。
- Python 可用、Pillow 不可用：基础生成可运行，图片方向、压缩、完整解码、元数据清理未验证；正式照片发布前核对。
- ffmpeg/ffprobe 不可用：使用完整原始音频或内置曲目；指定截取则说明缺少工具并保持旧版，不能忽略用户起点。
- 浏览器不可用：继续代码与静态资源检查，手机视觉待验证。
- 发布能力不可用：交付专用最终目录与所选服务的操作步骤。
- 手机微信不可用：保留真机待验证状态，不用桌面模拟替代。

## 当前兼容性记录

更新日期：2026-10-14。已核对官方安装与格式文档；当前环境完成共享 Python 生成器检查，尚未在四款客户端分别执行端到端安装与触发。每次真实运行更新对应记录。

| 环境 | 格式／安装资料 | 宿主端到端运行 |
| --- | --- | --- |
| WorkBuddy | 官方文档核对，提供元数据导出 | 待验证 |
| Claude Code | 官方文档核对，使用通用目录 | 待验证 |
| Codex | 当前 Work 环境可执行；CLI/IDE 路径核对 | CLI/IDE 待验证 |
| Gemini CLI | 官方文档核对，使用通用目录 | 待验证 |
| Gemini 网页版 | 不假定其可执行脚本或发布 | 按实际能力验证 |

官方资料：
- https://code.claude.com/docs/en/skills
- https://learn.chatgpt.com/docs/build-skills
- https://geminicli.com/docs/cli/skills/
- https://open.workbuddy.cn/en/docs/skill
