import { CompileResult, RunResult, ExampleMeta } from "./api";

type TabName = "tokens" | "ast" | "ir" | "run";

let activeTab: TabName = "run";
let lastCompile: CompileResult | null = null;
let lastRun: RunResult | null = null;
let stdinValue = "";
let contentRef: HTMLElement | null = null;

export function renderExamples(
  container: HTMLElement,
  examples: ExampleMeta[],
  onPick: (id: string) => void,
): void {
  const groups = new Map<string, ExampleMeta[]>();
  for (const ex of examples) {
    const key = ex.category || "other";
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key)!.push(ex);
  }
  container.innerHTML = "";
  for (const [cat, items] of groups) {
    const g = document.createElement("div");
    g.className = "example-group";
    const title = document.createElement("div");
    title.textContent = cat;
    g.appendChild(title);
    for (const ex of items) {
      const b = document.createElement("button");
      b.className = "example-item";
      b.textContent = ex.name;
      b.onclick = () => onPick(ex.id);
      g.appendChild(b);
    }
    container.appendChild(g);
  }
}

export function setCompile(result: CompileResult): void {
  lastCompile = result;
  renderTab();
}

export function setRun(result: RunResult): void {
  lastRun = result;
  activeTab = "run";
  syncTabButtons();
  renderTab();
}

export function initTabs(tabsEl: HTMLElement, contentEl: HTMLElement): void {
  contentRef = contentEl;
  tabsEl.querySelectorAll<HTMLButtonElement>("button[data-tab]").forEach((btn) => {
    btn.onclick = () => {
      activeTab = btn.dataset.tab as TabName;
      syncTabButtons();
      renderTab();
    };
  });
  syncTabButtons();
  renderTab();
}

function syncTabButtons(): void {
  document.querySelectorAll<HTMLButtonElement>("#tabs button[data-tab]").forEach((b) => {
    b.classList.toggle("active", b.dataset.tab === activeTab);
  });
}

function diagnosticsHtml(diags: { stage: string; line: number; col: number; message: string }[]): string {
  if (!diags.length) return "";
  return diags
    .map((d) => `<div class="diag">${d.stage} ${d.line}:${d.col}: ${escapeHtml(d.message)}</div>`)
    .join("");
}

function renderTab(): void {
  if (!contentRef) return;
  const c = contentRef;
  if (activeTab === "tokens") {
    const toks = lastCompile?.tokens ?? [];
    c.innerHTML =
      diagnosticsHtml(lastCompile?.diagnostics ?? []) +
      `<pre>${toks.map((t) => `${t.type}\t${escapeHtml(t.value)}\t(line ${t.line})`).join("\n")}</pre>`;
  } else if (activeTab === "ast") {
    c.innerHTML =
      diagnosticsHtml(lastCompile?.diagnostics ?? []) +
      `<pre>${escapeHtml(lastCompile?.ast ?? "")}</pre>`;
  } else if (activeTab === "ir") {
    c.innerHTML =
      diagnosticsHtml(lastCompile?.diagnostics ?? []) +
      `<pre>${escapeHtml(lastCompile?.ir ?? "")}</pre>`;
  } else {
    c.innerHTML = renderRun();
    const ta = c.querySelector<HTMLTextAreaElement>("#run-stdin");
    if (ta) {
      ta.value = stdinValue;
      ta.oninput = () => { stdinValue = ta.value; };
    }
  }
}

function renderRun(): string {
  let badge = "";
  if (lastRun) {
    if (lastRun.timed_out) badge = `<span class="exit-timeout">timed out</span>`;
    else if (lastRun.exit_code === 0) badge = `<span class="exit-ok">exit 0</span>`;
    else if (lastRun.exit_code !== null) badge = `<span class="exit-err">exit ${lastRun.exit_code}</span>`;
  }
  const diags = diagnosticsHtml(lastRun?.diagnostics ?? []);
  const out = escapeHtml(lastRun?.stdout ?? "");
  const err = lastRun?.stderr ? `<pre class="diag">${escapeHtml(lastRun.stderr)}</pre>` : "";
  return `
    <label>stdin</label>
    <textarea id="run-stdin" placeholder="input passed to the program"></textarea>
    <div>${badge}</div>
    ${diags}
    <pre>${out}</pre>
    ${err}
  `;
}

export function currentStdin(): string {
  return stdinValue;
}

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}
