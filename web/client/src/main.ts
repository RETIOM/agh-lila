import "./styles.css";
import * as api from "./api";
import {
  createEditor, applyHighlights, applyDiagnostics, getDoc, setDoc, setVim, vimEnabled,
  darkModeEnabled, setDarkMode,
} from "./editor";
import {
  renderExamples, setCompile, setRun, initTabs, currentStdin,
} from "./panels";

const STARTER = `fn main() -> int {\n    println("Hello, LILA!");\n    return 0;\n}\n`;
const SCRATCH_KEY = "lila-scratch";

let isScratch = true;

function loadScratch(): string {
  return localStorage.getItem(SCRATCH_KEY) ?? STARTER;
}

function debounce<T extends (...args: any[]) => void>(fn: T, ms: number): T {
  let h: number | undefined;
  return ((...args: any[]) => {
    if (h) window.clearTimeout(h);
    h = window.setTimeout(() => fn(...args), ms);
  }) as T;
}

async function refresh(view: ReturnType<typeof createEditor>) {
  const src = getDoc(view);
  if (isScratch) localStorage.setItem(SCRATCH_KEY, src);
  try {
    const [spans, result] = await Promise.all([api.highlight(src), api.compile(src)]);
    applyHighlights(view, spans);
    applyDiagnostics(view, result.diagnostics);
    setCompile(result);
  } catch (e) {
    console.error(e);
  }
}

function initResizeHandles(): void {
  const sidebar = document.getElementById("sidebar")!;
  const outputPane = document.getElementById("output-pane")!;
  const leftHandle = document.getElementById("resize-left")!;
  const rightHandle = document.getElementById("resize-right")!;

  function makeDragger(
    handle: HTMLElement,
    getSize: () => number,
    setSize: (px: number) => void,
    minPx: number,
    maxPx: () => number,
  ): void {
    handle.addEventListener("mousedown", (e) => {
      e.preventDefault();
      const startX = e.clientX;
      const startSize = getSize();
      handle.classList.add("dragging");

      function onMove(e: MouseEvent) {
        const delta = e.clientX - startX;
        const next = Math.max(minPx, Math.min(maxPx(), startSize + delta));
        setSize(next);
      }
      function onUp() {
        handle.classList.remove("dragging");
        document.removeEventListener("mousemove", onMove);
        document.removeEventListener("mouseup", onUp);
      }
      document.addEventListener("mousemove", onMove);
      document.addEventListener("mouseup", onUp);
    });
  }

  makeDragger(
    leftHandle,
    () => sidebar.offsetWidth,
    (px) => { sidebar.style.width = `${px}px`; },
    120,
    () => window.innerWidth - 400,
  );

  makeDragger(
    rightHandle,
    () => outputPane.offsetWidth,
    (px) => { outputPane.style.width = `${px}px`; },
    200,
    () => window.innerWidth - sidebar.offsetWidth - 200,
  );
}

async function main() {
  // Apply dark mode before the editor is created so it gets the right theme.
  if (darkModeEnabled()) document.body.classList.add("dark");

  initResizeHandles();

  const editorEl = document.getElementById("editor")!;
  editorEl.textContent = "";

  let view: ReturnType<typeof createEditor>;
  const debounced = debounce(() => refresh(view), 150);
  view = createEditor(editorEl, loadScratch(), debounced);

  initTabs(document.getElementById("tabs")!, document.getElementById("tab-content")!);

  const examplesEl = document.getElementById("examples")!;
  const scratchBtn = document.createElement("button");
  scratchBtn.className = "example-item";
  scratchBtn.textContent = "✎ Scratch";
  scratchBtn.onclick = () => {
    isScratch = true;
    setDoc(view, loadScratch());
    refresh(view);
  };
  examplesEl.appendChild(scratchBtn);

  const listEl = document.createElement("div");
  examplesEl.appendChild(listEl);
  const examples = await api.listExamples();
  renderExamples(listEl, examples, async (id) => {
    const source = await api.getExample(id);
    isScratch = false;
    setDoc(view, source);
    refresh(view);
  });

  document.getElementById("run-btn")!.onclick = async () => {
    const result = await api.run(getDoc(view), currentStdin());
    applyDiagnostics(view, result.diagnostics);
    setRun(result);
  };

  const vimBox = document.getElementById("vim-checkbox") as HTMLInputElement;
  vimBox.checked = vimEnabled();
  vimBox.onchange = () => setVim(view, vimBox.checked);

  const darkBox = document.getElementById("dark-checkbox") as HTMLInputElement;
  darkBox.checked = darkModeEnabled();
  darkBox.onchange = () => setDarkMode(view, darkBox.checked);

  refresh(view);
}

main();
