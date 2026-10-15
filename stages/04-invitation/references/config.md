# 配置与项目维护

## 数据规则

schema_version=2。旧版照片路径列表可以直接读取，归一后每张照片为对象。必填的真实资料为 name1、name2、date、venue、address，以及 ceremony_time 或 banquet_time 至少一个、photos 至少一张。demo=true 允许留空并显式标注。

| 字段 | 规则 |
| --- | --- |
| style | redwhite / floral / gold |
| event_type | 婚礼、订婚宴、答谢宴、归宁宴或用户文字 |
| date | 公历 YYYY-MM-DD；不自动添加农历 |
| welcome_time / ceremony_time / banquet_time | 独立的 HH:MM，空值不显示 |
| message / story / slogan / ending | 邀请语、真实经历、封面短句、收尾语 |
| photos | 至多12项，字符串路径或对象 |
| cover_index | 从0开始的封面索引 |
| sections | invitation / album / address 布尔开关，宴会安排保留 |
| primary_color | 空或 #RRGGBB，修改强调色，页面自动选高对比按钮文字 |
| share_title / share_description | 可选网页分享标题和描述，不保证微信卡片展示；海报优先使用自定义 share_title，正文使用项目资料 |
| public_url | 实际发布页的完整 URL，目录 URL 须带结尾 / |
| map_url | 用户提供或经核实的完整 http/https 地图链接 |

照片对象示例：
{"path":"photos/02.jpg","caption":"我们的这一刻","fit":"contain","position":[50,50]}

contain 完整展示；cover 铺满，position 指定水平和垂直百分比位置，须查看裁切是否影响人脸。默认不进行人脸识别，不宣称自动检测脸部。生成器读取照片尺寸分类为横、竖、近方形。安装 Pillow 时检查解码、矫正方向，短边小于600像素或重复内容会警告；元数据从发布副本中清理，原图不改动。没有 Pillow 时采用复制并报告处理未验证。

单张照片只做封面，省略空相册。多张照片按原顺序排除封面后进入相册。所有图均来自当前用户项目。

## 目录

一个项目可以有：
project.json、originals/、patches/、review/、preview.html、publish/、checks/、sharing/poster.png 与 sharing/sharing.json。

project.json 保存私有源路径、资料、版本和历史；构建摘要只含已发布相对资源与处理状态。发布整个 publish/，勿上传项目根目录。

分享记录保留当前配置摘要、真实链接、封面与海报摘要、验证方法及状态。修改资料后依据 references/sharing.md 更新网页及海报，不能将旧海报默认为当前版本。海报 PNG 可交付宾客，分享报告留在私有项目。

project.json 里的绝对路径便于本机续做。换电脑时复制 originals/ 并更新 photos 和 music 路径；不要声称只复制 project.json 即可恢复素材。

## 操作

初始化：
python3 scripts/project.py init --config <配置.json> --project <project.json>

查看当前版本：
python3 scripts/project.py status --project <project.json>

局部修改：
python3 scripts/project.py update --project <project.json> --patch <patch.json> --expected-revision <当前版本> --note "更换封面"

嵌套对象递归合并；列表整组替换。空文本表示清空可选文案，布尔 false 关闭对应功能。必要字段清空须同时设 demo=true；未知字段、错误日期、错误索引直接报错，不写入项目。音频和照片新路径相对于补丁文件解析，创建项目后归一为绝对路径。

恢复历史：
python3 scripts/project.py restore --project <project.json> --revision <历史版本> --expected-revision <当前版本>

恢复操作会创建新的版本，保留当前版本快照。发布记录在修改后标注 needs_update=true，直到线上当前字节核对成功。

旧版非空输出目录没有 build-manifest.json 时，新生成器拒绝覆盖。选择新的输出目录即可，不需要删除旧版。
