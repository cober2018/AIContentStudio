import type { TextMark, TextRun } from "./TextStudioModel.ts";

type EditorMark = { type: string; attrs?: Record<string, unknown> };
type EditorNode = { type?: string; text?: string; attrs?: Record<string, unknown>; marks?: EditorMark[]; content?: EditorNode[] };

const MARKS = new Set(["bold", "italic", "code", "link"]);

export function runsToTiptap(runs: TextRun[]): EditorNode {
  const content: EditorNode[] = [];
  for (const run of runs) {
    const parts = run.text.split("\n");
    parts.forEach((part, index) => {
      if (index) content.push({ type: "hardBreak" });
      if (part) content.push({ type: "text", text: part, ...(run.marks.length ? { marks: run.marks.map((mark) => mark.type === "link" ? { type: "link", attrs: { href: mark.href } } : { type: mark.type }) } : {}) });
    });
  }
  return { type: "doc", content: [{ type: "paragraph", ...(content.length ? { content } : {}) }] };
}

export function tiptapToRuns(doc: EditorNode): TextRun[] {
  if (doc.type !== "doc" || doc.content?.length !== 1 || doc.content[0].type !== "paragraph") throw new Error("Unsupported editor structure");
  const runs: TextRun[] = [];
  for (const node of doc.content[0].content || []) {
    let text: string;
    let marks: TextMark[];
    if (node.type === "hardBreak") { text = "\n"; marks = []; }
    else if (node.type === "text" && typeof node.text === "string") {
      text = node.text;
      marks = (node.marks || []).map((mark) => {
        if (!MARKS.has(mark.type)) throw new Error(`Unsupported editor mark: ${mark.type}`);
        if (mark.type === "link") {
          const href = mark.attrs?.href;
          if (typeof href !== "string" || !/^https?:\/\/[^\s]+$/.test(href)) throw new Error("Unsupported editor link");
          return { type: "link", href };
        }
        return { type: mark.type as TextMark["type"] };
      });
      marks.sort((a, b) => ["bold", "italic", "code", "link"].indexOf(a.type) - ["bold", "italic", "code", "link"].indexOf(b.type));
    } else throw new Error(`Unsupported editor node: ${node.type}`);
    const previous = runs[runs.length - 1];
    if (previous && JSON.stringify(previous.marks) === JSON.stringify(marks)) previous.text += text;
    else runs.push({ text, marks });
  }
  return runs;
}
