# 婚礼全链路一站式技能（ai-wedding-one-stop）

将求婚定制、AI 婚纱照、婚礼视频、动态电子请柬、蜜月路书五段能力合并为一个可复用技能包。

## 五个阶段（逻辑顺序）

1. **求婚定制** — `stages/01-proposal/`
2. **婚纱照** — `stages/02-wedding-photos/`
3. **婚礼视频** — `stages/03-wedding-video/`
4. **电子请柬** — `stages/04-invitation/`
5. **蜜月路书** — `stages/05-honeymoon/`

## 如何调用

告诉 Agent 要做哪一段（例如「做婚纱照」「做请柬」），或说「全套 / 从求婚做到蜜月」。未指定时从阶段 1 问起；每阶段结束可进入下一阶段或跳过。

主入口与路由规则见根目录 `SKILL.md`。各阶段详细步骤与资源见对应目录下的 `ORIGINAL-SKILL.md` 及同目录 `references/`、`assets/`、`scripts/`。
