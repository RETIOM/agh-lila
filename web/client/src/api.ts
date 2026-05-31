export interface Span { start: number; end: number; type: string; }
export interface Token { type: string; value: string; line: number; col: number; }
export interface Diagnostic { stage: string; line: number; col: number; message: string; severity: string; }
export interface CompileResult { tokens: Token[]; ast: string | null; ir: string | null; diagnostics: Diagnostic[]; }
export interface RunResult { stdout: string; stderr: string; exit_code: number | null; timed_out: boolean; diagnostics: Diagnostic[]; }
export interface ExampleMeta { id: string; category: string; name: string; }

async function post<T>(url: string, body: unknown): Promise<T> {
  const r = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`${url} -> ${r.status}`);
  return r.json() as Promise<T>;
}

export const highlight = (source: string) =>
  post<{ spans: Span[] }>("/api/highlight", { source }).then((r) => r.spans);

export const compile = (source: string) =>
  post<CompileResult>("/api/compile", { source });

export const run = (source: string, stdin: string) =>
  post<RunResult>("/api/run", { source, stdin });

export async function listExamples(): Promise<ExampleMeta[]> {
  const r = await fetch("/api/examples");
  return r.json();
}

export async function getExample(id: string): Promise<string> {
  const r = await fetch(`/api/examples/${id}`);
  return (await r.json()).source as string;
}
