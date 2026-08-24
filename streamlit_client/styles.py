CSS = """
<style>
:root {
    --border: #252a33;
    --surface-2: #161a20;
    --muted: #8b929e;
    --muted-2: #626975;
    --accent: #7c8cff;
    --accent-2: #9b6cff;
    --mono: "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, monospace;
}

.app-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 2px;
}

.app-header .icon {
    width: 34px;
    height: 34px;
    flex-shrink: 0;
    border-radius: 9px;
    background: linear-gradient(135deg, var(--accent), var(--accent-2));
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: var(--mono);
    font-weight: 600;
    color: white;
}

.app-header h1 {
    font-size: 22px;
    margin: 0;
    letter-spacing: -0.4px;
}

.app-subtitle {
    color: var(--muted);
    font-size: 14px;
    margin: 4px 0 22px;
}

.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 12.5px;
    padding: 5px 10px;
    border-radius: 999px;
    border: 1px solid var(--border);
    background: var(--surface-2);
    color: var(--muted);
}

.status-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
}

.status-dot.online { background: #4ade80; }
.status-dot.offline { background: #f87171; }
.status-dot.unknown { background: #8b929e; }

.sources-wrap {
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px solid var(--border);
}

.sources-label {
    font-family: var(--mono);
    font-size: 11px;
    letter-spacing: 0.03em;
    text-transform: uppercase;
    color: var(--muted-2);
    display: block;
    margin-bottom: 6px;
}

.source-chip {
    display: inline-block;
    font-family: var(--mono);
    font-size: 12px;
    color: var(--muted);
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 3px 9px;
    margin: 0 6px 6px 0;
}

.empty-state {
    text-align: center;
    color: var(--muted-2);
    padding: 60px 20px;
}

.empty-state .icon {
    width: 44px;
    height: 44px;
    margin: 0 auto 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 12px;
    border: 1px solid var(--border);
    font-family: var(--mono);
    font-size: 18px;
    color: var(--muted);
}

.empty-state p {
    margin: 0 0 6px;
    font-size: 15px;
    color: var(--muted);
}

.empty-state .sub {
    font-size: 13px;
    color: var(--muted-2);
}

.error-text {
    color: #f87171;
}
</style>
"""