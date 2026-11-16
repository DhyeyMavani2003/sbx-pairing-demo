"""Generate hand-laid-out Excalidraw scenes for the two posts.

Usage: python3 gen.py <outdir>
Writes <agent>-<slug>.excalidraw for agent in (claude, codex).
"""
import json
import sys

B62 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

INK = "#1e1e1e"
BLUE, BLUE_BG = "#1971c2", "#e7f5ff"
GREEN, GREEN_BG = "#2f9e44", "#ebfbee"
AMBER, AMBER_BG = "#f08c00", "#fff3bf"
VIOLET, VIOLET_BG = "#6741d9", "#e5dbff"
RED, RED_BG = "#e03131", "#ffe3e3"
GRAY, GRAY_BG = "#495057", "#f1f3f5"
WHITE = "#ffffff"

CHAR_W = 0.56  # average glyph width of Excalifont, as a fraction of font size


class Scene:
    def __init__(self):
        self.els = []
        self.n = 0
        self.g = 0

    def _index(self):
        n = self.n
        if n < 62:
            return "a" + B62[n]
        n -= 62
        return "b" + B62[n // 62] + B62[n % 62]

    def _el(self, kind, x, y, w, h, **kw):
        idx = self._index()
        self.n += 1
        e = {
            "id": f"el-{self.n}", "type": kind, "x": x, "y": y, "width": w, "height": h,
            "angle": 0, "strokeColor": kw.get("stroke", INK),
            "backgroundColor": kw.get("bg", "transparent"), "fillStyle": "solid",
            "strokeWidth": kw.get("sw", 2), "strokeStyle": kw.get("style", "solid"),
            "roughness": kw.get("rough", 1), "opacity": 100,
            "groupIds": list(kw.get("groups", [])), "frameId": None, "index": idx,
            "roundness": kw.get("roundness"), "seed": 1000 + self.n * 7919,
            "version": 1, "versionNonce": 5000 + self.n * 104729, "isDeleted": False,
            "boundElements": None, "updated": 1794816000000, "link": None, "locked": False,
        }
        self.els.append(e)
        return e

    def group(self):
        self.g += 1
        return f"grp-{self.g}"

    def rect(self, x, y, w, h, bg=WHITE, stroke=INK, **kw):
        kw.setdefault("roundness", {"type": 3})
        return self._el("rectangle", x, y, w, h, bg=bg, stroke=stroke, **kw)

    def text(self, cx, cy, s, size=20, color=INK, align="center", groups=()):
        lines = s.split("\n")
        w = max(len(l) for l in lines) * size * CHAR_W + 8
        h = len(lines) * size * 1.25
        x = cx - w / 2 if align == "center" else cx
        e = self._el("text", x, cy - h / 2, w, h, stroke=color, groups=groups, rough=1)
        e.update({
            "text": s, "originalText": s, "fontSize": size, "fontFamily": 5,
            "textAlign": align, "verticalAlign": "top", "containerId": None,
            "autoResize": True, "lineHeight": 1.25,
        })
        return e

    def box(self, x, y, w, h, label, bg=WHITE, stroke=INK, size=20, **kw):
        g = self.group()
        self.rect(x, y, w, h, bg=bg, stroke=stroke, groups=[g], **kw)
        self.text(x + w / 2, y + h / 2, label, size=size, groups=[g])

    def zone(self, x, y, w, h, title, bg, stroke, sw=2, style="solid", title_at="top"):
        self.rect(x, y, w, h, bg=bg, stroke=stroke, sw=sw, style=style)
        ty = y + 26 if title_at == "top" else y + h - 26
        self.text(x + 18, ty, title, size=22, color=stroke, align="left")

    def arrow(self, pts, color=INK, style="solid", start=None, end="arrow", sw=2):
        x0, y0 = pts[0]
        rel = [[px - x0, py - y0] for px, py in pts]
        xs = [p[0] for p in rel]
        ys = [p[1] for p in rel]
        e = self._el("arrow", x0, y0, max(xs) - min(xs), max(ys) - min(ys),
                     stroke=color, style=style, sw=sw,
                     roundness={"type": 2} if len(pts) > 2 else None)
        e.update({
            "points": rel, "lastCommittedPoint": None, "startBinding": None,
            "endBinding": None, "startArrowhead": start, "endArrowhead": end,
            "elbowed": False,
        })
        return e

    def label(self, cx, cy, s, size=16, bg=WHITE, color=INK, pad=16):
        lines = s.split("\n")
        w = max(len(l) for l in lines) * size * CHAR_W + pad
        h = len(lines) * size * 1.25 + 6
        g = self.group()
        self.rect(cx - w / 2, cy - h / 2, w, h, bg=bg, stroke="transparent",
                  roundness=None, rough=0, groups=[g])
        self.text(cx, cy, s, size=size, color=color, groups=[g])

    def dump(self, path):
        doc = {
            "type": "excalidraw", "version": 2, "source": "https://excalidraw.com",
            "elements": self.els,
            "appState": {"viewBackgroundColor": WHITE, "gridSize": None},
            "files": {},
        }
        with open(path, "w") as f:
            json.dump(doc, f, indent=1)


AGENTS = {
    "claude": {
        "name": "Claude Code", "mode": "permission prompts off", "sbx": "pairing-demo",
        "cmd": "claude", "home": "~/.ssh, ~/.claude",
        "hosted": "Context7\nhosted MCP server", "hosted_label": "sign-in handled on the host",
        "cloud_cred": "Anthropic API key", "cred_cmd": "sbx --cloud secret set anthropic",
    },
    "codex": {
        "name": "Codex", "mode": "approvals and its\nsandbox off", "sbx": "codex-demo",
        "cmd": "codex", "home": "~/.ssh, ~/.codex",
        "hosted": "OpenAI Docs MCP and Context7\nhosted MCP servers", "hosted_label": "requests leave from the host",
        "cloud_cred": "OpenAI sign-in (OAuth)", "cred_cmd": "sbx --cloud secret set openai --oauth",
    },
}


def boundary(a):
    """What sits inside the sandbox, what stays on the laptop, and what crosses."""
    s = Scene()
    s.zone(40, 40, 960, 240, "Docker Sandbox: a microVM with its own kernel", GREEN_BG, GREEN, sw=4)
    s.zone(40, 420, 960, 250, "Your laptop", BLUE_BG, BLUE, title_at="bottom")
    y1, y2, bw, bh = 130, 480, 230, 100
    s.box(80, y1, bw, bh, "Private clone\nof your repo")
    s.box(390, y1, 260, bh, f"{a['name']}\n{a['mode']}", bg=AMBER_BG, stroke=AMBER, size=19)
    s.box(730, y1, bw, bh, "Private\nDocker daemon")
    s.box(80, y2, bw, bh, "Project repo")
    s.box(390, y2, 260, bh, "sbx proxy\nholds the real tokens", bg=VIOLET_BG, stroke=VIOLET, size=19)
    s.box(730, y2, bw, bh, f"Your other files\n{a['home']}", bg=RED_BG, stroke=RED, size=19)
    # inside the sandbox
    s.arrow([(390, 180), (310, 180)])
    s.label(350, 146, "edits,\ncommits", size=14, bg=GREEN_BG, pad=0)
    s.arrow([(650, 180), (730, 180)])
    s.label(690, 146, "runs\ncontainers", size=13, bg=GREEN_BG, pad=0)
    # repo <-> clone
    s.arrow([(140, 480), (140, 230)])
    s.label(140, 350, "--clone copies\nyour commits", size=15)
    s.arrow([(250, 230), (250, 480)])
    s.label(292, 350, "git fetch\nsandbox-" + a["sbx"], size=15)
    # agent -> proxy -> internet
    s.arrow([(520, 230), (520, 480)])
    s.label(520, 350, "requests carry\na placeholder token", size=15)
    s.arrow([(520, 580), (520, 790)])
    s.label(520, 728, "real token added,\nallowed hosts only", size=15)
    s.box(330, 790, 380, 80, "Model API, GitHub, package registries", bg=GRAY_BG, stroke=GRAY, size=18)
    # blocked
    s.arrow([(845, 280), (845, 480)], color=RED, style="dashed", end="bar")
    s.label(845, 350, "no access\nfrom the sandbox", size=15, color=RED)
    return s


def pr_flow(a):
    """Sequence: from one command to an open pull request."""
    s = Scene()
    lanes = [("You", 120), ("sbx on your laptop", 400), (f"{a['name']} in the sandbox", 690), ("GitHub", 940)]
    bottom = 760
    for name, x in lanes:
        w = max(120, len(name) * 18 * CHAR_W + 36)
        bg, st = (AMBER_BG, AMBER) if "sandbox" in name else (WHITE, INK)
        s.box(x - w / 2, 40, w, 60, name, bg=bg, stroke=st, size=18)
        s.arrow([(x, 100), (x, bottom)], color=GRAY, style="dashed", end=None, sw=1)
    you, host, agent, gh = (x for _, x in lanes)
    steps = [
        (you, host, f"sbx run --clone {a['cmd']} .", "solid"),
        (host, agent, "start the microVM, clone the repo", "solid"),
        (you, agent, "\"fix the failing test\"", "solid"),
        (agent, agent, "fix, commit on a branch", "solid"),
        (you, host, "git fetch sandbox-" + a["sbx"], "solid"),
        (you, agent, "\"open a pull request\"", "solid"),
        (agent, host, "gh pr create, placeholder token", "solid"),
        (host, gh, "same request, real token", "solid"),
        (gh, you, "pull request link", "dashed"),
    ]
    y = 160
    for src, dst, text, style in steps:
        if src == dst:
            g = s.group()
            w = len(text) * 15 * CHAR_W + 28
            s.rect(src - w / 2, y - 22, w, 44, bg=AMBER_BG, stroke=AMBER, groups=[g])
            s.text(src, y, text, size=15, groups=[g])
        else:
            s.arrow([(src, y), (dst, y)], style=style)
            s.label((src + dst) / 2, y - 16, text, size=15)
        y += 68
    return s


def mcp_gateway(a):
    """How MCP tools reach the agent, and how a host browser reaches the app."""
    s = Scene()
    s.zone(40, 40, 960, 220, "Docker Sandbox", GREEN_BG, GREEN, sw=4)
    s.zone(40, 400, 960, 220, "Your laptop", BLUE_BG, BLUE)
    s.box(90, 120, 360, 100, f"{a['name']}\nsees one server: mcp-gateway", bg=AMBER_BG, stroke=AMBER, size=19)
    s.box(630, 120, 320, 100, "Your dev server\nport 8000")
    s.box(90, 480, 360, 100, "sbx MCP gateway\nservers added with sbx mcp add", bg=VIOLET_BG, stroke=VIOLET, size=19)
    s.box(630, 480, 320, 100, "Playwright MCP\nand its browser")
    s.arrow([(270, 220), (270, 480)])
    s.label(270, 330, "tool calls", size=16)
    s.arrow([(450, 530), (630, 530)])
    s.label(540, 508, "stdio", size=16, bg=BLUE_BG)
    s.arrow([(790, 480), (790, 220)])
    s.label(790, 330, "http://localhost:8080\nthe published port", size=16)
    s.arrow([(270, 580), (270, 730)])
    s.label(270, 676, a["hosted_label"], size=16)
    s.box(90, 730, 360, 90, a["hosted"], bg=GRAY_BG, stroke=GRAY, size=19)
    return s


def local_to_cloud(a):
    """Same CLI, two places to run: what changes in the cloud."""
    s = Scene()
    s.zone(40, 40, 960, 230, "Your laptop", BLUE_BG, BLUE)
    s.zone(40, 450, 960, 250, "Docker Cloud Sandboxes", GREEN_BG, GREEN, sw=4, title_at="bottom")
    s.box(80, 120, 250, 100, "sbx CLI", bg=VIOLET_BG, stroke=VIOLET)
    s.box(690, 120, 270, 100, "Local sandbox\nuses your repo folder")
    s.box(80, 510, 250, 100, "Cloud secret store\n" + a["cloud_cred"], size=18)
    s.box(630, 510, 330, 100, f"Cloud sandbox running {a['name']}\n1 hour by default, 24 at most", bg=AMBER_BG, stroke=AMBER, size=17)
    s.arrow([(330, 170), (690, 170)])
    s.label(510, 148, f"sbx run {a['cmd']} .", size=16, bg=BLUE_BG)
    s.arrow([(160, 220), (160, 510)])
    s.label(160, 360, a["cred_cmd"].replace(" set ", "\nset "), size=15)
    s.arrow([(330, 560), (630, 560)])
    s.label(480, 538, "agent credentials", size=16, bg=GREEN_BG)
    s.arrow([(300, 220), (700, 510)])
    s.label(500, 360, "sbx --cloud create\n--ttl 8h", size=15)
    s.arrow([(880, 220), (880, 510)], start="arrow")
    s.label(880, 360, "sbx move copies\na filesystem\nsnapshot", size=15)
    s.box(630, 800, 330, 80, "GitHub", bg=GRAY_BG, stroke=GRAY)
    s.arrow([(795, 800), (795, 610)])
    s.label(795, 748, "git clone inside, no host folder", size=15)
    return s


DIAGRAMS = {
    "sandbox-boundary": boundary,
    "prompt-to-pull-request": pr_flow,
    "mcp-gateway": mcp_gateway,
    "local-to-cloud": local_to_cloud,
}

if __name__ == "__main__":
    out = sys.argv[1]
    for agent, cfg in AGENTS.items():
        for slug, fn in DIAGRAMS.items():
            fn(cfg).dump(f"{out}/{agent}-{slug}.excalidraw")
            print(f"wrote {agent}-{slug}.excalidraw")
