import { EditorView, basicSetup } from "codemirror";
import { EditorState, StateEffect, StateField, RangeSetBuilder, Compartment } from "@codemirror/state";
import { indentUnit } from "@codemirror/language";
import { Decoration, DecorationSet } from "@codemirror/view";
import { setDiagnostics, lintGutter, Diagnostic as CMDiagnostic } from "@codemirror/lint";
import { vim } from "@replit/codemirror-vim";
import { typeToClass, lilaTheme, lilaDarkTheme } from "./theme";
import { Span, Diagnostic } from "./api";

const setHighlights = StateEffect.define<Span[]>();

const highlightField = StateField.define<DecorationSet>({
  create() { return Decoration.none; },
  update(deco, tr) {
    deco = deco.map(tr.changes);
    for (const e of tr.effects) {
      if (e.is(setHighlights)) {
        const docLen = tr.state.doc.length;
        const builder = new RangeSetBuilder<Decoration>();
        for (const s of e.value) {
          if (s.start < s.end && s.end <= docLen) {
            builder.add(s.start, s.end, Decoration.mark({ class: typeToClass(s.type) }));
          }
        }
        deco = builder.finish();
      }
    }
    return deco;
  },
  provide: (f) => EditorView.decorations.from(f),
});

const vimCompartment = new Compartment();
const themeCompartment = new Compartment();

export function vimEnabled(): boolean {
  return localStorage.getItem("lila-vim") === "1";
}

export function darkModeEnabled(): boolean {
  return localStorage.getItem("lila-dark") === "1";
}

export function createEditor(parent: HTMLElement, doc: string, onChange: () => void): EditorView {
  const view = new EditorView({
    parent,
    state: EditorState.create({
      doc,
      extensions: [
        vimCompartment.of(vimEnabled() ? vim() : []),
        themeCompartment.of(darkModeEnabled() ? lilaDarkTheme : lilaTheme),
        indentUnit.of("    "),
        basicSetup,
        highlightField,
        lintGutter(),
        EditorView.updateListener.of((u) => {
          if (u.docChanged) onChange();
        }),
      ],
    }),
  });
  return view;
}

export function applyHighlights(view: EditorView, spans: Span[]): void {
  view.dispatch({ effects: setHighlights.of(spans) });
}

export function setDoc(view: EditorView, text: string): void {
  view.dispatch({ changes: { from: 0, to: view.state.doc.length, insert: text } });
}

export function getDoc(view: EditorView): string {
  return view.state.doc.toString();
}

export function setVim(view: EditorView, on: boolean): void {
  localStorage.setItem("lila-vim", on ? "1" : "0");
  view.dispatch({ effects: vimCompartment.reconfigure(on ? vim() : []) });
}

export function setDarkMode(view: EditorView, on: boolean): void {
  localStorage.setItem("lila-dark", on ? "1" : "0");
  view.dispatch({ effects: themeCompartment.reconfigure(on ? lilaDarkTheme : lilaTheme) });
  document.body.classList.toggle("dark", on);
}

export function applyDiagnostics(view: EditorView, diags: Diagnostic[]): void {
  const doc = view.state.doc;
  const cm: CMDiagnostic[] = diags.map((d) => {
    const lineNo = Math.min(Math.max(d.line, 1), doc.lines);
    const line = doc.line(lineNo);
    const from = Math.min(line.from + Math.max(d.col - 1, 0), line.to);
    const to = Math.min(from + 1, line.to);
    return { from, to, severity: "error", message: `[${d.stage}] ${d.message}` };
  });
  view.dispatch(setDiagnostics(view.state, cm));
}
