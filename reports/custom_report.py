import json
import time
import shutil
from datetime import datetime
from pathlib import Path

# CMD NAME MAPPING
from utils.ws_commands import XOCDIA_LIVE_CMD, TAIXIU_MINI_CMD, WS_CMD, TAIXIU_MD5_MINI_CMD, TREN_DUOI_CMD, MINI_POKER_CMD

ALL_WS_CMDS = {}
ALL_WS_CMDS.update({str(v): k for k, v in XOCDIA_LIVE_CMD.items()})
ALL_WS_CMDS.update({str(v): k for k, v in TAIXIU_MINI_CMD.items()})
ALL_WS_CMDS.update({str(v): k for k, v in WS_CMD.items()})
ALL_WS_CMDS.update({str(v): k for k, v in TAIXIU_MD5_MINI_CMD.items()})
ALL_WS_CMDS.update({str(v): k for k, v in TREN_DUOI_CMD.items()})
ALL_WS_CMDS.update({str(v): k for k, v in MINI_POKER_CMD.items()})


def get_cmd_name(cmd):
    return ALL_WS_CMDS.get(str(cmd), f"WS CMD {cmd}")


class ReportStep:
    def __init__(self, name, status, message="", screenshot=None, extra=None):
        self.name = name
        self.status = status
        self.message = message
        self.screenshot = screenshot
        self.timestamp = datetime.now().strftime("%H:%M:%S")
        self.extra = extra or {}


class ExecutionReport:
    def __init__(self):
        self.title = "HitClub Automation Report"
        self.base_url = ""
        self.username = ""
        self.browser_name = "Chrome"
        self.captcha_mode = ""

        self.game_name = ""
        self.video_path = None

        # Create a unique temporary folder for THIS specific run
        self.run_dir = Path(f"reports/temp_run_{int(time.time())}")
        self.run_dir.mkdir(parents=True, exist_ok=True)

        self.started_at = datetime.now()
        self.finished_at = None
        self.status = "RUNNING"

        self.steps = []

    def add_step(self, name, status, message="", screenshot=None, extra=None):
        step = ReportStep(name, status, message, screenshot, extra)
        self.steps.append(step)

        short_message = (message or "").strip()
        if len(short_message) > 180:
            short_message = short_message[:177] + "..."

        if short_message:
            print(f"[STEP {step.timestamp}] [{status}] {name} | {short_message}", flush=True)
        else:
            print(f"[STEP {step.timestamp}] [{status}] {name}", flush=True)

    def finish(self, status="PASSED"):
        self.status = status
        self.finished_at = datetime.now()


# =========================
# GLOBAL REPORT INSTANCE
# =========================
report = ExecutionReport()


# =========================
# HTML GENERATOR
# =========================
def write_html_report(report_obj: ExecutionReport, output_dir: Path):

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    file_path = output_dir / "custom_report.html"

    # CREATE THE SCREENSHOT FOLDER INSIDE THE TEMP ZIP FOLDER
    screenshot_dir = output_dir / "screenshots"
    screenshot_dir.mkdir(parents=True, exist_ok=True)

    # Fix screenshot paths
    for step in report_obj.steps:
        if step.screenshot:
            original_path = Path(step.screenshot)

            # If the physical file exists, copy it into our pristine zip folder
            if original_path.exists():
                new_path = screenshot_dir / original_path.name

                # Prevent copying the file onto itself if it's already there
                if original_path.resolve() != new_path.resolve():
                    try:
                        shutil.copy2(original_path, new_path)
                    except Exception as e:
                        print(f"[WARN] Could not copy screenshot {original_path}: {e}")

            # Update the HTML to look for the image inside the local screenshots folder
            step.screenshot = f"screenshots/{original_path.name}"

    duration = ""
    if report_obj.finished_at:
        duration = round(
            (report_obj.finished_at - report_obj.started_at).total_seconds(), 2
        )

    status_map = {
        "PASS": "PASSED",
        "SUCCESS": "PASSED",
        "FAIL": "FAILED",
        "ERROR": "FAILED",
        "WARNING": "MANUAL",
        "WARN": "MANUAL",
        "RUNNING": "INFO",
    }
    status_key = str(report_obj.status or "INFO").upper()
    status_key = status_map.get(status_key, status_key)
    if status_key not in {"PASSED", "FAILED", "MANUAL", "SKIPPED", "INFO"}:
        status_key = "INFO"

    html = []
    html.append("<!DOCTYPE html>")
    html.append("<html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'><title>Test Report</title>")

    html.append("""
    <style>
        :root {
            --bg-color: #f3f4f6;
            --text-color: #1f2937;
            --muted-text: #667085;
            --good: #15803d;
            --warn: #c2410c;
            --bad: #dc2626;
            --info: #0369a1;
            --skipped: #64748b;
            --shadow: 0 16px 38px rgba(15, 23, 42, 0.12);
            --header-bg: linear-gradient(135deg, #1f2937 0%, #334155 100%);
            --header-text: #f8fafc;
            --header-muted: rgba(226, 232, 240, 0.84);
            --header-panel-bg: rgba(15, 23, 42, 0.18);
            --header-border: rgba(148, 163, 184, 0.28);
            --surface-bg: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(248, 250, 252, 0.98) 100%);
            --surface-subtle: #f8fafc;
            --surface-soft-border: #dbe3ee;
            --table-head-bg: linear-gradient(180deg, #f8fafc 0%, #edf2f7 100%);
        }

        * {
            box-sizing: border-box;
        }

        body {
            font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
            background:
                radial-gradient(circle at top, rgba(148, 163, 184, 0.16), transparent 28%),
                radial-gradient(circle at bottom right, rgba(37, 99, 235, 0.08), transparent 24%),
                linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%);
            color: var(--text-color);
            margin: 0;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: auto;
        }

        .header {
            background: var(--header-bg);
            padding: 20px;
            border-radius: 12px;
            box-shadow: var(--shadow);
            margin-bottom: 24px;
            border: 1px solid var(--header-border);
            border-left: 8px solid var(--info);
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 20px;
            flex-wrap: wrap;
        }

        .header.PASSED { border-left-color: var(--good); }
        .header.FAILED { border-left-color: var(--bad); }
        .header.MANUAL { border-left-color: var(--warn); }
        .header.SKIPPED { border-left-color: var(--skipped); }
        .header.INFO { border-left-color: var(--info); }

        .header-left h1 {
            margin: 0 0 8px 0;
            font-size: 28px;
            font-weight: 700;
            color: var(--header-text);
        }

        .header-left p {
            margin: 0;
            color: var(--header-muted);
            font-size: 14px;
            line-height: 1.5;
        }

        .status-text.PASSED { color: #86efac; }
        .status-text.FAILED { color: #fca5a5; }
        .status-text.MANUAL { color: #fdba74; }
        .status-text.SKIPPED { color: #cbd5e1; }
        .status-text.INFO { color: #93c5fd; }

        .meta-data {
            display: flex;
            flex-direction: column;
            gap: 8px;
            font-size: 14px;
            color: var(--header-text);
            background: var(--header-panel-bg);
            padding: 15px;
            border-radius: 8px;
            border: 1px solid var(--header-border);
            min-width: min(100%, 390px);
        }

        .meta-item {
            display: flex;
            justify-content: space-between;
            gap: 16px;
        }

        .meta-label {
            font-weight: 600;
            color: var(--header-muted);
        }

        .section-card {
            background: var(--surface-bg);
            padding: 20px;
            border-radius: 12px;
            box-shadow: var(--shadow);
            border: 1px solid var(--surface-soft-border);
            margin-bottom: 24px;
        }

        .section-card h2 {
            margin: 0 0 14px 0;
            font-size: 20px;
            color: var(--text-color);
        }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            margin-bottom: 14px;
            flex-wrap: wrap;
        }

        .chart-subtitle {
            font-size: 13px;
            font-weight: 600;
            color: var(--muted-text);
        }

        .status {
            padding: 4px 10px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 700;
            color: #fff;
            text-transform: uppercase;
            letter-spacing: 0.3px;
            display: inline-block;
        }

        .status.PASSED { background: var(--good); }
        .status.FAILED { background: var(--bad); }
        .status.MANUAL { background: var(--warn); }
        .status.SKIPPED { background: var(--skipped); }
        .status.INFO { background: var(--info); }

        .step {
            background: #fff;
            border-radius: 12px;
            padding: 16px;
            border: 1px solid var(--surface-soft-border);
            border-left: 6px solid var(--info);
            box-shadow: 0 8px 22px rgba(15, 23, 42, 0.06);
            margin-bottom: 14px;
        }

        .step.PASSED { border-left-color: var(--good); }
        .step.FAILED { border-left-color: var(--bad); }
        .step.MANUAL { border-left-color: var(--warn); }
        .step.SKIPPED { border-left-color: var(--skipped); }
        .step.INFO { border-left-color: var(--info); }

        .step h3 {
            margin: 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 10px;
            font-size: 16px;
        }

        .details {
            margin-top: 12px;
            background: var(--surface-subtle);
            border: 1px solid var(--surface-soft-border);
            border-radius: 8px;
            padding: 10px 12px;
            color: var(--text-color);
            white-space: pre-wrap;
        }

        .time {
            color: var(--muted-text);
            font-size: 12px;
            margin-top: 12px;
        }

        .step-image {
            width: 100%;
            max-width: 100%;
            margin: 12px auto 0;
            border-radius: 10px;
            border: 1px solid var(--surface-soft-border);
            display: block;
            cursor: pointer;
            transition: transform 0.2s ease;
        }

        .step-image:hover {
            transform: scale(1.02);
        }

        .video-player {
            width: 100%;
            max-width: 100%;
            display: block;
            margin: 0 auto;
            border-radius: 10px;
            border: 1px solid var(--surface-soft-border);
            background: #000;
        }

        .wide-table-wrap {
            overflow-x: auto;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            background: #fff;
            border-radius: 10px;
            overflow: hidden;
        }

        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid var(--surface-soft-border);
            vertical-align: top;
        }

        th {
            background: var(--table-head-bg);
            font-weight: 700;
            color: #334155;
        }

        .ws-row {
            cursor: pointer;
        }

        .payload-row td {
            background: #f8fafc;
        }

        pre {
            margin: 0;
            overflow-x: auto;
            white-space: pre-wrap;
            word-break: break-word;
            background: #1f2937;
            color: #f8fafc;
            border-radius: 8px;
            padding: 12px;
        }

        .empty-state {
            padding: 18px;
            border: 1px dashed #cbd5e1;
            border-radius: 10px;
            color: var(--muted-text);
            background: rgba(255, 255, 255, 0.8);
        }

        @media (max-width: 900px) {
            .meta-data {
                min-width: 100%;
            }
        }
    </style>
    <script>
    function togglePayload(id) {
        var row = document.getElementById(id);
        if (row.style.display === "none") {
            row.style.display = "table-row";
        } else {
            row.style.display = "none";
        }
    }
    </script>
    """)

    html.append("</head><body>")
    html.append("<div class='container'>")

    # ================= HEADER =================
    html.append(f"""
    <header class="header {status_key}">
        <div class="header-left">
            <h1>{report_obj.title} - {report_obj.game_name or "Game Not Set"}</h1>
            <p>
                Execution pipeline and detailed step validation.
                Status: <b class="status-text {status_key}">{report_obj.status}</b>
            </p>
        </div>

        <div class="meta-data">
            <div class="meta-item">
                <span class="meta-label">Target URL</span>
                <strong>{report_obj.base_url or "-"}</strong>
            </div>
            <div class="meta-item">
                <span class="meta-label">Test User</span>
                <strong>{report_obj.username or "-"}</strong>
            </div>
            <div class="meta-item">
                <span class="meta-label">Captcha Mode</span>
                <strong>{report_obj.captcha_mode or "-"}</strong>
            </div>
            <div class="meta-item">
                <span class="meta-label">Duration</span>
                <strong>{duration if duration != "" else "-"} seconds</strong>
            </div>
            <div class="meta-item">
                <span class="meta-label">Started</span>
                <strong>{report_obj.started_at.strftime("%Y-%m-%d %H:%M:%S")}</strong>
            </div>
            <div class="meta-item">
                <span class="meta-label">Finished</span>
                <strong>{report_obj.finished_at.strftime("%Y-%m-%d %H:%M:%S") if report_obj.finished_at else "-"}</strong>
            </div>
        </div>
    </header>
    """)

    # ADD VIDEO BLOCK
    if getattr(report_obj, "video_path", None):
        rel_vid_path = Path(report_obj.video_path).name
        video_ext = Path(report_obj.video_path).suffix.lower()
        video_type = "video/mp4"
        if video_ext == ".webm":
            video_type = "video/webm"
        elif video_ext == ".avi":
            video_type = "video/x-msvideo"

        html.append(f"""
        <section class="section-card">
            <h2>Execution Video</h2>
            <video class="video-player" controls>
              <source src="{rel_vid_path}" type="{video_type}">
            </video>
        </section>
        """)

    # ================= SPLIT STEPS =================
    ws_steps = [s for s in report_obj.steps if s.extra and "cmd" in s.extra]
    other_steps = [s for s in report_obj.steps if not (s.extra and "cmd" in s.extra)]

    # ================= WS STEPS =================
    if ws_steps:
        # Create Payload Export Directory
        ws_dir = output_dir / "ws_payloads"
        ws_dir.mkdir(parents=True, exist_ok=True)

        html.append("""
        <section class="section-card">
            <div class="card-header">
                <h2>WebSocket Commands</h2>
                <span class="chart-subtitle">Click a row to view payload</span>
            </div>
            <div class="wide-table-wrap">
                <table>
                    <tr>
                        <th>Command</th>
                        <th>Time</th>
                        <th>Status</th>
                    </tr>
        """)

        for i, step in enumerate(ws_steps):
            cmd = step.extra["cmd"]
            cmd_name = get_cmd_name(cmd)
            payload = step.extra.get("payload", {})
            row_status = str(step.status).upper()

            # Save the physical JSON file to the folder
            safe_name = f"step_{i+1}_{cmd_name.replace(' ', '_')}.json"
            (ws_dir / safe_name).write_text(json.dumps(payload, indent=2), encoding="utf-8")

            html.append(f"""
                    <tr class="ws-row" onclick="togglePayload('payload_{i}')">
                        <td><b>{cmd_name} ({cmd})</b></td>
                        <td>{step.timestamp}</td>
                        <td><span class="status {row_status}">{step.status}</span></td>
                    </tr>
                    <tr id="payload_{i}" class="payload-row" style="display:none;">
                        <td colspan="3"><pre>{json.dumps(payload, indent=2)}</pre></td>
                    </tr>
            """)

        html.append("""
                </table>
            </div>
        </section>
        """)

    # ================= NORMAL STEPS =================
    html.append("<section class='section-card'><h2>Execution Steps</h2>")

    if not other_steps:
        html.append("<div class='empty-state'>No execution steps were recorded.</div>")

    for step in other_steps:
        step_status = str(step.status).upper()
        html.append(f"<article class='step {step_status}'>")
        html.append(f"""
        <h3>
            {step.name}
            <span class='status {step_status}'>{step.status}</span>
        </h3>
        """)

        if step.message:
            html.append(f"<div class='details'>{step.message}</div>")

        html.append(f"<p class='time'><b>Time:</b> {step.timestamp}</p>")

        if step.screenshot:
            html.append(f"<img class='step-image' src='{step.screenshot}' />")

        html.append("</article>")

    html.append("</section>")

    # ================= IMAGE ZOOM =================
    html.append("""
    <script>
    document.querySelectorAll("img").forEach(img => {
        img.onclick = () => {
            const w = window.open("");
            w.document.write(`<img src="${img.src}" style="width:100%">`);
        };
    });
    </script>
    """)

    html.append("</div></body></html>")

    file_path.write_text("".join(html), encoding="utf-8")

    return file_path
