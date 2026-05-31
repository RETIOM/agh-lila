import { EditorView } from "@codemirror/view";

const TYPE_TO_CLASS: Record<string, string> = {
  FN: "tok-keyword", RETURN: "tok-keyword", IF: "tok-keyword", ELSE: "tok-keyword",
  FOR: "tok-keyword", IN: "tok-keyword", WHILE: "tok-keyword", DO: "tok-keyword",
  BREAK: "tok-keyword", CONTINUE: "tok-keyword", AS: "tok-keyword",
  TRUE: "tok-bool", FALSE: "tok-bool",
  INTEGER_LITERAL: "tok-number", FLOAT_LITERAL: "tok-number",
  STRING_LITERAL: "tok-string", CHAR_LITERAL: "tok-char",
  ID: "tok-ident", COMMENT: "tok-comment",
};

const TYPE_PREFIX_CLASS: Array<[string, string]> = [["TYPE_", "tok-type"]];

const OPERATORS = new Set([
  "PLUS", "MINUS", "TIMES", "DIVIDE", "MOD", "INC", "DEC",
  "EQ", "NEQ", "LT", "GT", "LE", "GE", "AND", "OR", "NOT",
  "BIT_AND", "BIT_OR", "BIT_XOR", "BIT_NOT", "LSHIFT", "RSHIFT",
  "ASSIGN", "ADD_ASSIGN", "SUB_ASSIGN", "MUL_ASSIGN", "DIV_ASSIGN", "MOD_ASSIGN",
]);

const PUNCT = new Set([
  "LPAREN", "RPAREN", "LBRACE", "RBRACE", "LBRACKET", "RBRACKET",
  "COMMA", "SEMI", "ARROW", "DOTDOT",
]);

export function typeToClass(type: string): string {
  if (type in TYPE_TO_CLASS) return TYPE_TO_CLASS[type];
  for (const [prefix, cls] of TYPE_PREFIX_CLASS) if (type.startsWith(prefix)) return cls;
  if (OPERATORS.has(type)) return "tok-operator";
  if (PUNCT.has(type)) return "tok-punct";
  return "tok-ident";
}

export const lilaTheme = EditorView.theme({
  ".tok-keyword": { color: "#9467bd" },
  ".tok-type": { color: "#1f77b4", fontWeight: "bold" },
  ".tok-bool": { color: "#9467bd" },
  ".tok-number": { color: "#d62728" },
  ".tok-string": { color: "#2ca02c" },
  ".tok-char": { color: "#2ca02c" },
  ".tok-ident": { color: "#1f77b4" },
  ".tok-operator": { color: "#2ca02c" },
  ".tok-punct": { color: "#ff7f0e" },
  ".tok-comment": { color: "#888888", fontStyle: "italic" },
});

export const lilaDarkTheme = EditorView.theme({
  "&": { backgroundColor: "#1e1e1e", color: "#d4d4d4" },
  ".cm-content": { caretColor: "#d4d4d4" },
  ".cm-cursor": { borderLeftColor: "#d4d4d4" },
  "& .cm-selectionBackground": { background: "#264f78" },
  "&.cm-focused > .cm-scroller > .cm-selectionLayer .cm-selectionBackground": { background: "#264f78" },
  ".cm-gutters": { backgroundColor: "#1e1e1e", color: "#858585", borderRight: "1px solid #333" },
  ".cm-activeLineGutter": { backgroundColor: "#1f2a36" },
  ".cm-activeLine": { backgroundColor: "rgba(255,255,255,0.05)" },
  ".tok-keyword": { color: "#c586c0" },
  ".tok-type": { color: "#4ec9b0", fontWeight: "bold" },
  ".tok-bool": { color: "#c586c0" },
  ".tok-number": { color: "#b5cea8" },
  ".tok-string": { color: "#ce9178" },
  ".tok-char": { color: "#ce9178" },
  ".tok-ident": { color: "#9cdcfe" },
  ".tok-operator": { color: "#d4d4d4" },
  ".tok-punct": { color: "#d4d4d4" },
  ".tok-comment": { color: "#6a9955", fontStyle: "italic" },
}, { dark: true });
