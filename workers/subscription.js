/**
 * Cloudflare Worker: serve the latest top-5 Cloudflare IPs.
 *
 * Data source: top5.json committed to laoxu93/cf-speedtest-bot by the
 * GitHub Actions workflow (router runs daily 05:00, synced to GitHub).
 *
 * Endpoints:
 *   /            - usage note (text)
 *   /top5.json   - the latest top-5 JSON, proxied from GitHub raw
 *   /sub         - plain-text IP list (NOT a usable VLESS/Trojan
 *                  subscription: a real subscription still needs the
 *                  user's own node info, e.g. UUID / domain / path / SNI)
 *   /report.md   - the latest Markdown report
 *
 * Deploy (after the user confirms): npx wrangler deploy
 * or via the Cloudflare API with the xiaoai-api token.
 */

const RAW_BASE =
  "https://raw.githubusercontent.com/laoxu93/cf-speedtest-bot/main";

async function fetchUpstream(path, ctx) {
  const res = await fetch(RAW_BASE + path, {
    cf: { cacheTtl: 300, cacheEverything: true },
  });
  if (!res.ok) {
    return new Response("上游数据暂不可用，请稍后再试。", { status: 502 });
  }
  return res;
}

export default {
  async fetch(request) {
    const url = new URL(request.url);
    const path = url.pathname;

    if (path === "/" || path === "") {
      return new Response(
        [
          "Cloudflare 优选 IP 测速（N60 Pro 路由器定时测速）",
          "",
          "接口：",
          "  /top5.json  最新前 5 名 IP（JSON）",
          "  /sub        最新前 5 名 IP（纯文本列表）",
          "  /report.md  最新测速报告",
          "",
          "注意：这里只是 IP 列表，不是可用的 VLESS/Trojan 订阅；",
          "做可用订阅还需要你自己的节点信息。",
          "测速位置是 N60 Pro 路由器（家里宽带）。",
          "",
        ].join("\n"),
        { headers: { "content-type": "text/plain; charset=utf-8" } }
      );
    }

    if (path === "/top5.json") {
      const res = await fetchUpstream("/top5.json");
      return new Response(res.body, {
        headers: {
          "content-type": "application/json; charset=utf-8",
          "cache-control": "public, max-age=300",
        },
      });
    }

    if (path === "/report.md") {
      const res = await fetchUpstream("/report.md");
      return new Response(res.body, {
        headers: {
          "content-type": "text/markdown; charset=utf-8",
          "cache-control": "public, max-age=300",
        },
      });
    }

    if (path === "/sub" || path === "/subscription") {
      const res = await fetchUpstream("/top5.json");
      if (res.status !== 200) return res;
      const data = await res.json();
      const lines = [
        `# Cloudflare 优选 IP（${data.generated_at || ""}，测速位置：N60 Pro 路由器）`,
        "# 注意：仅为 IP 列表，不是可用的 VLESS/Trojan 订阅",
        "",
      ];
      for (const item of data.top5 || []) {
        lines.push(`${item.ip}:443 # ${item.region} ${item.latency_ms}ms`);
      }
      if (!data.top5 || data.top5.length === 0) {
        lines.push("# 暂无数据");
      }
      return new Response(lines.join("\n") + "\n", {
        headers: {
          "content-type": "text/plain; charset=utf-8",
          "cache-control": "public, max-age=300",
        },
      });
    }

    return new Response("Not found", { status: 404 });
  },
};
