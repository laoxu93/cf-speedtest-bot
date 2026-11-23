# cf-speedtest-bot

定时 Cloudflare 优选 IP 测速机器人（GitHub Actions + Cloudflare Worker）。

## 它做什么

- GitHub Actions 每天北京时间 07:00、12:00、16:00、19:00 自动跑一次测速，也支持手动触发。
- 用 [XIU2/CloudflareSpeedTest](https://github.com/XIU2/CloudflareSpeedTest) 的 HTTPing 模式，只筛 HKG（香港）、SIN（新加坡）、NRT（东京）、KIX（大阪）四个地区，取前 5 名。
- 每次测完把结果写回仓库：`report.md`（报告）、`top5.json`（前 5 名）、`result.csv`（完整结果）。
- Cloudflare Worker（`workers/subscription.js`）把最新的前 5 名 IP 以纯文本 / JSON 形式提供出来。

## 重要说明（先看这个）

- **测速位置是 GitHub Actions**，测的是 GitHub Runner 到 Cloudflare 的延迟，**不是家里宽带的延迟**。家里真实结果以 N60 Pro 路由器每天 05:00 的测速为准。
- **v1 只有测速报告 + IP 列表**。这里给出的只是 IP 列表，**不是可用的 VLESS / Trojan 订阅**——做可用订阅还需要你自己的节点信息（UUID、域名、路径、SNI 等）。
- Telegram 推送目前是占位：工作流里有发送步骤，但没有配置 `TG_BOT_TOKEN` / `TG_CHAT_ID` 时会自动跳过，不会报错。

## 定时

| 北京时间 | Cron（UTC） |
| --- | --- |
| 07:00 | `0 23 * * *` |
| 12:00 | `0 4 * * *` |
| 16:00 | `0 8 * * *` |
| 19:00 | `0 11 * * *` |

手动跑一次：仓库 → Actions → Cloudflare Speed Test → Run workflow。

## 测速命令

```bash
./cfst -httping -cfcolo HKG,SIN,NRT,KIX -n 100 -t 4 -dn 5 -dt 10 -tl 200 -tlr 1 -p 5 -o result.csv
```

`-n 100` 是按 XIU2 的建议调低的并发，HTTPing 本质上算网络扫描，并发太高容易被临时限制。

## Worker 订阅端点

代码在 `workers/subscription.js`，配置在 `wrangler.toml`（脚本名 `cf-speedtest-subscription`）。

部署（需要 Cloudflare API 权限 Workers Scripts Edit，部署前请用户确认）：

```bash
npx wrangler deploy
```

部署后：

- `/` 说明页
- `/top5.json` 最新前 5 名（JSON）
- `/sub` 最新前 5 名（纯文本 IP 列表）
- `/report.md` 最新测速报告

Worker 读的是仓库 main 分支的 `top5.json` / `report.md`（raw.githubusercontent.com），每次工作流更新仓库后最多 5 分钟内生效。

## Telegram（待用户确认）

等用户确认了以下两项再接：

1. 结果发到哪个群 / 频道（群 ID）
2. BotFather 机器人是否已建好（Bot Token）

确认后在仓库 Settings → Secrets and variables → Actions 里加 `TG_BOT_TOKEN` 和 `TG_CHAT_ID` 两个 Secrets 即可，代码不用改。令牌不要写进代码、不要发在聊天里。

## 文件

| 文件 | 说明 |
| --- | --- |
| `.github/workflows/speedtest.yml` | 定时测速工作流 |
| `scripts/report.py` | 读 result.csv，生成 report.md 和 top5.json |
| `scripts/telegram.py` | 发 Telegram 报告，未配置 Secrets 时跳过 |
| `workers/subscription.js` | Worker 订阅端点 |
| `wrangler.toml` | Worker 配置 |
| `report.md` / `top5.json` / `result.csv` | 最新一次测速结果（由工作流更新） |
