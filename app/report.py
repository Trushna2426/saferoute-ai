import html
import json
import os
from datetime import datetime


def safe(value, default="Not available"):
    if value is None or value == "":
        return default
    return html.escape(str(value))


def export_report_html(report_json: str) -> str:
    report = json.loads(report_json)

    os.makedirs("reports", exist_ok=True)

    route = report.get("route", "SafeRoute")
    route_name = (
        str(route)
        .replace(" ", "_")
        .replace("→", "_to_")
        .replace("/", "_")
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    display_timestamp = datetime.now().strftime("%d %b %Y, %I:%M %p")
    filename = f"reports/{route_name}_{timestamp}.html"

    risk_level = str(report.get("risk_level", "Not available"))
    risk_score = report.get("risk_score", None)
    blind_spot_risk = report.get("blind_spot_risk", "Not available")

    detected_hotspots = report.get("detected_hotspots", []) or []
    blind_spot_reasons = report.get("blind_spot_reasons", []) or []
    recommendations = report.get("recommendations", []) or []

    try:
        risk_score_number = float(risk_score)
    except (TypeError, ValueError):
        risk_score_number = 0

    risk_percent = max(0, min(100, risk_score_number * 10))

    risk_class = risk_level.lower()
    if risk_class not in ["low", "medium", "high", "critical"]:
        risk_class = "unknown"

    hotspots_html = (
        "".join(
            f"""
            <div class="hotspot-card">
                <div class="pin">{index}</div>
                <div>
                    <strong>{safe(hotspot)}</strong>
                    <p>Detected from available accident-prone hotspot data.</p>
                </div>
            </div>
            """
            for index, hotspot in enumerate(detected_hotspots, start=1)
        )
        if detected_hotspots
        else "<p class='empty-state'>No accident-prone hotspots were listed in this report.</p>"
    )

    blind_reasons_html = (
        "".join(f"<li>{safe(reason)}</li>" for reason in blind_spot_reasons)
        if blind_spot_reasons
        else "<li>No specific blind spot reason was listed.</li>"
    )

    recommendations_html = (
        "".join(
            f"""
            <div class="recommendation-card">
                <div class="rec-icon">✓</div>
                <p>{safe(item)}</p>
            </div>
            """
            for item in recommendations
        )
        if recommendations
        else "<p class='empty-state'>No safety recommendations were listed.</p>"
    )

    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>SafeRoute AI Travel Safety Report</title>
<style>
    :root {{
        --navy: #0b1f3a;
        --navy-2: #122b4a;
        --blue: #2563eb;
        --sky: #38bdf8;
        --green: #22c55e;
        --orange: #f59e0b;
        --red: #ef4444;
        --critical: #7f1d1d;
        --purple: #7c3aed;
        --bg: #eef4f8;
        --card: #ffffff;
        --text: #0f172a;
        --muted: #64748b;
        --border: #dbe4ee;
        --shadow: 0 12px 30px rgba(15, 23, 42, 0.08);
    }}

    * {{
        box-sizing: border-box;
    }}

    body {{
        margin: 0;
        font-family: Arial, Helvetica, sans-serif;
        background: var(--bg);
        color: var(--text);
        line-height: 1.6;
    }}

    .page {{
        max-width: 1180px;
        margin: 32px auto;
        background: #f8fbff;
        border-radius: 18px;
        overflow: hidden;
        box-shadow: var(--shadow);
    }}

    .hero {{
        background:
            radial-gradient(circle at 80% 20%, rgba(56, 189, 248, 0.24), transparent 30%),
            linear-gradient(135deg, var(--navy), var(--navy-2));
        color: white;
        padding: 44px 48px;
        display: flex;
        justify-content: space-between;
        gap: 24px;
        align-items: flex-start;
    }}

    .brand {{
        display: flex;
        gap: 18px;
        align-items: center;
    }}

    .logo {{
        width: 72px;
        height: 72px;
        border-radius: 20px;
        background: linear-gradient(135deg, #1d4ed8, #22c55e);
        display: grid;
        place-items: center;
        font-size: 34px;
        box-shadow: 0 10px 24px rgba(0,0,0,0.25);
    }}

    .hero h1 {{
        margin: 0;
        font-size: 42px;
        line-height: 1.1;
        letter-spacing: -1px;
    }}

    .hero h2 {{
        margin: 8px 0 6px;
        color: #38bdf8;
        font-size: 22px;
    }}

    .hero p {{
        margin: 0;
        color: #dbeafe;
    }}

    .timestamp {{
        border: 1px solid rgba(255,255,255,0.28);
        background: rgba(255,255,255,0.08);
        border-radius: 14px;
        padding: 14px 18px;
        min-width: 220px;
        text-align: right;
    }}

    .timestamp span {{
        display: block;
        color: #cbd5e1;
        font-size: 13px;
    }}

    .timestamp strong {{
        font-size: 16px;
    }}

    .content {{
        padding: 28px 34px 38px;
    }}

    .section {{
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 22px;
        margin-bottom: 22px;
        box-shadow: 0 8px 22px rgba(15, 23, 42, 0.04);
    }}

    .section-title {{
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 18px;
    }}

    .section-number {{
        width: 30px;
        height: 30px;
        background: var(--blue);
        color: white;
        border-radius: 50%;
        display: grid;
        place-items: center;
        font-weight: bold;
        font-size: 14px;
    }}

    .section-title h3 {{
        margin: 0;
        font-size: 22px;
    }}

    .summary-grid {{
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 14px;
    }}

    .summary-card {{
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 18px;
        background: linear-gradient(180deg, #ffffff, #f8fafc);
    }}

    .summary-card .icon {{
        width: 42px;
        height: 42px;
        border-radius: 14px;
        background: #dbeafe;
        color: var(--blue);
        display: grid;
        place-items: center;
        font-size: 20px;
        margin-bottom: 12px;
    }}

    .label {{
        color: var(--muted);
        text-transform: uppercase;
        font-size: 12px;
        font-weight: bold;
        letter-spacing: 0.5px;
    }}

    .value {{
        margin-top: 6px;
        font-weight: 800;
        font-size: 17px;
    }}

    .risk-grid {{
        display: grid;
        grid-template-columns: 1fr 1.15fr 1fr;
        gap: 18px;
        align-items: stretch;
    }}

    .risk-level-card,
    .score-card,
    .blind-card {{
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 24px;
        background: #fff;
        text-align: center;
    }}

    .risk-badge {{
        display: inline-block;
        padding: 8px 18px;
        border-radius: 999px;
        color: white;
        font-weight: 800;
        margin: 10px 0;
    }}

    .risk-badge.low {{ background: var(--green); }}
    .risk-badge.medium {{ background: var(--orange); }}
    .risk-badge.high {{ background: var(--red); }}
    .risk-badge.critical {{ background: var(--critical); }}
    .risk-badge.unknown {{ background: var(--muted); }}

    .score-circle {{
        width: 180px;
        height: 180px;
        border-radius: 50%;
        margin: 18px auto;
        background:
            conic-gradient(
                var(--red) 0deg,
                var(--orange) calc({risk_percent} * 1.8deg),
                #e5e7eb calc({risk_percent} * 3.6deg)
            );
        position: relative;
        display: grid;
        place-items: center;
    }}

    .score-circle::before {{
        content: "";
        position: absolute;
        width: 126px;
        height: 126px;
        border-radius: 50%;
        background: white;
    }}

    .score-inner {{
        position: relative;
        z-index: 2;
        font-size: 32px;
        font-weight: 900;
    }}

    .score-inner span {{
        display: block;
        font-size: 16px;
        color: var(--muted);
        font-weight: 700;
    }}

    .blind-icon {{
        width: 96px;
        height: 96px;
        border-radius: 50%;
        background: #ffedd5;
        display: grid;
        place-items: center;
        font-size: 42px;
        margin: 20px auto 12px;
    }}

    .two-column {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 22px;
    }}

    .hotspot-card {{
        display: flex;
        gap: 14px;
        align-items: flex-start;
        border: 1px solid #fecaca;
        background: #fff7f7;
        border-radius: 14px;
        padding: 14px;
        margin-bottom: 12px;
    }}

    .pin {{
        min-width: 34px;
        height: 34px;
        border-radius: 50%;
        background: var(--red);
        color: white;
        display: grid;
        place-items: center;
        font-weight: 800;
    }}

    .hotspot-card p {{
        margin: 4px 0 0;
        color: var(--muted);
        font-size: 14px;
    }}

    .reason-list {{
        margin: 0;
        padding-left: 22px;
    }}

    .reason-list li {{
        margin-bottom: 10px;
    }}

    .recommendations-grid {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 14px;
    }}

    .recommendation-card {{
        display: flex;
        gap: 12px;
        align-items: flex-start;
        border: 1px solid #bfdbfe;
        background: linear-gradient(180deg, #eff6ff, #ffffff);
        padding: 16px;
        border-radius: 14px;
    }}

    .rec-icon {{
        min-width: 30px;
        height: 30px;
        border-radius: 50%;
        background: var(--blue);
        color: white;
        display: grid;
        place-items: center;
        font-weight: bold;
    }}

    .recommendation-card p {{
        margin: 0;
    }}

    .empty-state {{
        color: var(--muted);
        background: #f8fafc;
        border: 1px dashed var(--border);
        padding: 16px;
        border-radius: 12px;
    }}

    .disclaimer {{
        background: linear-gradient(135deg, #f5f3ff, #eff6ff);
        border: 1px solid #ddd6fe;
    }}

    .footer {{
        background: var(--navy);
        color: white;
        text-align: center;
        padding: 18px;
        font-weight: 700;
    }}

    @media (max-width: 980px) {{
        .summary-grid,
        .risk-grid,
        .two-column,
        .recommendations-grid {{
            grid-template-columns: 1fr;
        }}

        .hero {{
            flex-direction: column;
        }}

        .timestamp {{
            text-align: left;
        }}
    }}

    @media print {{
        body {{
            background: white;
        }}

        .page {{
            margin: 0;
            box-shadow: none;
            border-radius: 0;
        }}

        .section {{
            break-inside: avoid;
        }}
    }}
</style>
</head>
<body>
    <main class="page">
        <header class="hero">
            <div class="brand">
                <div class="logo">🛡️</div>
                <div>
                    <h1>SafeRoute AI</h1>
                    <h2>Travel Safety Report</h2>
                    <p>Offline route safety summary generated for demo and review.</p>
                </div>
            </div>
            <div class="timestamp">
                <span>Report Generated</span>
                <strong>{display_timestamp}</strong>
            </div>
        </header>

        <section class="content">
            <div class="section">
                <div class="section-title">
                    <div class="section-number">1</div>
                    <h3>Route Summary</h3>
                </div>
                <div class="summary-grid">
                    <div class="summary-card">
                        <div class="icon">🧭</div>
                        <div class="label">Route</div>
                        <div class="value">{safe(report.get("route"))}</div>
                    </div>
                    <div class="summary-card">
                        <div class="icon">🛣️</div>
                        <div class="label">Provider</div>
                        <div class="value">{safe(report.get("route_provider"))}</div>
                    </div>
                    <div class="summary-card">
                        <div class="icon">📍</div>
                        <div class="label">Distance</div>
                        <div class="value">{safe(report.get("distance_km"))} km</div>
                    </div>
                    <div class="summary-card">
                        <div class="icon">⏱️</div>
                        <div class="label">Duration</div>
                        <div class="value">{safe(report.get("duration_min"))} min</div>
                    </div>
                    <div class="summary-card">
                        <div class="icon">🔄</div>
                        <div class="label">Fallback Used</div>
                        <div class="value">{"Yes" if report.get("fallback_used") else "No"}</div>
                    </div>
                </div>
            </div>

            <div class="section">
                <div class="section-title">
                    <div class="section-number">2</div>
                    <h3>Risk Overview</h3>
                </div>
                <div class="risk-grid">
                    <div class="risk-level-card">
                        <div class="label">Risk Level</div>
                        <div class="risk-badge {risk_class}">{safe(risk_level)}</div>
                        <p>Higher risk routes require stronger attention and safer driving choices.</p>
                    </div>

                    <div class="score-card">
                        <div class="label">Risk Score</div>
                        <div class="score-circle">
                            <div class="score-inner">
                                {safe(risk_score)}
                                <span>/ 10</span>
                            </div>
                        </div>
                        <p>Score is generated using hotspot, route, time, vehicle, and blind-spot factors.</p>
                    </div>

                    <div class="blind-card">
                        <div class="label">Blind Spot Risk</div>
                        <div class="blind-icon">👁️</div>
                        <h3>{safe(blind_spot_risk)}</h3>
                    </div>
                </div>
            </div>

            <div class="section two-column">
                <div>
                    <div class="section-title">
                        <div class="section-number">3</div>
                        <h3>Accident-Prone Hotspots</h3>
                    </div>
                    {hotspots_html}
                </div>

                <div>
                    <div class="section-title">
                        <div class="section-number">4</div>
                        <h3>Blind Spot Reasons</h3>
                    </div>
                    <ul class="reason-list">
                        {blind_reasons_html}
                    </ul>
                </div>
            </div>

            <div class="section">
                <div class="section-title">
                    <div class="section-number">5</div>
                    <h3>Safety Recommendations</h3>
                </div>
                <div class="recommendations-grid">
                    {recommendations_html}
                </div>
            </div>

            <div class="section disclaimer">
                <strong>Disclaimer:</strong>
                <p>{safe(report.get("disclaimer"))}</p>
            </div>
        </section>

        <footer class="footer">
            SafeRoute AI – Intelligent Routes, Safer Journeys
        </footer>
    </main>
</body>
</html>
"""

    with open(filename, "w", encoding="utf-8") as file:
        file.write(html_content)

    return filename