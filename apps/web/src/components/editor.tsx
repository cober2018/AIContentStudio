/**
 * TipTap 富文本编辑器（Markdown 双向序列化）。
 * 存储契约：后端 body 仍是 Markdown（导出 md/txt/srt 依赖），编辑器只在边界做转换。
 */
import { EditorContent, useEditor, type Editor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import { Markdown } from "tiptap-markdown";

export interface SelectionRange {
  from: number;
  to: number;
  text: string;
}

interface EditorCallbacks {
  onChange: (markdown: string) => void;
  onSelectionChange: (sel: SelectionRange | null) => void;
}

export function getMarkdown(editor: Editor): string {
  return editor.storage.markdown.getMarkdown() as string;
}

export function useMarkdownEditor(initialContent: string, callbacks: EditorCallbacks): Editor | null {
  return useEditor({
    extensions: [StarterKit, Markdown.configure({ html: false, linkify: false, breaks: true })],
    content: initialContent,
    onUpdate: ({ editor }) => callbacks.onChange(getMarkdown(editor)),
    onSelectionUpdate: ({ editor }) => {
      const { from, to, empty } = editor.state.selection;
      callbacks.onSelectionChange(empty ? null : { from, to, text: editor.state.doc.textBetween(from, to, "\n") });
    },
  });
}

/** 载入新稿件内容（不触发 onChange，避免误标 dirty）。 */
export function loadContent(editor: Editor, markdown: string): void {
  editor.commands.setContent(markdown, false);
}

/** 取选区前后各 pad 字符作为改写上下文。 */
export function selectionContext(editor: Editor, sel: SelectionRange, pad = 100) {
  const size = editor.state.doc.content.size;
  return {
    context_before: editor.state.doc.textBetween(Math.max(0, sel.from - pad), sel.from, "\n"),
    context_after: editor.state.doc.textBetween(sel.to, Math.min(size, sel.to + pad), "\n"),
  };
}

/** 用改写结果精确替换原选区（按位置，不做字符串查找）。 */
export function replaceSelection(editor: Editor, sel: SelectionRange, text: string): void {
  editor.chain().focus().insertContentAt({ from: sel.from, to: sel.to }, text).run();
}

const TOOL_BUTTON =
  "rounded px-2 py-0.5 text-xs text-slate-600 hover:bg-slate-100 disabled:opacity-40";

function ToolButton({ label, isActive, onClick }: {
  label: string;
  isActive: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      className={`${TOOL_BUTTON} ${isActive ? "bg-gray-200 font-medium text-gray-900" : ""}`}
      onMouseDown={(e) => e.preventDefault()}
      onClick={onClick}
    >
      {label}
    </button>
  );
}

export function EditorToolbar({ editor }: { editor: Editor }) {
  return (
    <div className="flex flex-wrap items-center gap-1 border-b border-slate-100 bg-white px-4 py-1.5">
      <ToolButton label="标题" isActive={editor.isActive("heading", { level: 2 })}
        onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()} />
      <ToolButton label="小标题" isActive={editor.isActive("heading", { level: 3 })}
        onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()} />
      <ToolButton label="B" isActive={editor.isActive("bold")}
        onClick={() => editor.chain().focus().toggleBold().run()} />
      <ToolButton label="I" isActive={editor.isActive("italic")}
        onClick={() => editor.chain().focus().toggleItalic().run()} />
      <ToolButton label="• 列表" isActive={editor.isActive("bulletList")}
        onClick={() => editor.chain().focus().toggleBulletList().run()} />
      <ToolButton label="1. 列表" isActive={editor.isActive("orderedList")}
        onClick={() => editor.chain().focus().toggleOrderedList().run()} />
      <ToolButton label="引用" isActive={editor.isActive("blockquote")}
        onClick={() => editor.chain().focus().toggleBlockquote().run()} />
    </div>
  );
}

export { EditorContent };
