# 定稿与发布

## 生成最终目录

用户选定 style、核对真实内容，使用 project.json：
python3 scripts/build.py --config <project.json> --out <publish> --mode final

最终目录只含 index.html、media/ 和不含私人源路径的 build-manifest.json。内置音乐只复制当前风格，评审预览留在外部。demo=true 的普通最终生成会拒绝；演示网站明确使用 --allow-demo 并保留标记。

本地检查：
python3 scripts/check_publish.py --out <publish> --report <checks/local.json>

演示检查同样显式添加 --allow-demo。公开范围、显示的照片、时间和地址由用户核对。用户已授权的发布步骤继续执行，勿重复要求批准。

## 托管选择

优先用户指定的服务及当前 Agent 已有的发布能力。已有站点更新原站点，保留站点标识、访问权限和资源路径。没有指定服务时说明当前可用方案，再使用符合已授权分享范围的路径。没有任何发布能力时交付最终目录和必要配置，不生成假的访问地址。

- 当前 Agent 提供 Sites：遵循宿主的 Sites 发布技能，将最终目录复制到站点静态输出目录，使用其源码同步和部署流程。分享给无需账号的宾客需要对应公开访问设置，不能把私人预览地址称为亲友可直接打开。
- 用户已有静态网站：将最终目录上传到所选目录，保留 media/ 相对路径及 HTTPS；首次上传后检查页面与媒体。
- GitHub Pages、Cloudflare Pages 等：仅在用户选择且当前环境可用时采用官方发布流程。不要内置密钥、不将私人原图和 project.json 提交到公开仓库。
- 无发布能力：标注“已生成，待发布”，列出需要用户选择的托管服务与部署目录。

## 分享元数据与二维码

发布工具返回预计地址时可先填写 public_url；实际部署成功后再确认。页面 URL 如 https://example.com/invite/ 须带结尾 /，如为 index.html 则直接使用完整页地址。重建会将 share_title、share_description 和分享封面的绝对 URL 写入页面。安装 Pillow 时生成1200×630封面，照片完整放入画布；分享标题仍是可编辑文字。

安装 qrcode 时使用本地库为 public_url 生成 media/link-qr.png，不使用外部二维码服务。URL 尚未验证时该二维码只能算候选，线上检查成功后才交付为可用二维码。未安装可选库时如实标明未生成，勿伪造。

线上检查：
python3 scripts/check_publish.py --out <publish> --url <实际地址> --report <checks/online.json>

检查比较入口及照片、音乐与当前本地版本的字节，能识别登录页、旧版和资源缺失。代理改写或图片压缩会产生差异，此时核对实际服务行为，不删掉检查来声称成功。微信分享缩略图受实际域名及平台能力影响，通用网页元数据不构成展示保证。继续按 references/sharing.md 判断标题卡片或二维码海报路径；海报须绑定选定风格的最终页，不能误用三款评审首页。

记录当前发布结果：
python3 scripts/project.py record-publication --project <project.json> --out <publish> --report <checks/online.json> --expected-revision <当前版本>

## 真机验收

在微信 iOS、微信 Android 及手机浏览器检查：进入、跳过、静音、有声、重播、返回前台、照片完整性、文字换行、复制地址、地图跳转、链接转发和分享卡片。若无真机条件，保留待验证记录，交付实际已完成的链接和检查结果。地图需真实地点与用户核实过的链接，不用演示地址假装验证。
