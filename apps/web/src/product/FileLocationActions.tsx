import { Copy, FolderOpen } from "lucide-react";
import { useState } from "react";
import { api, ApiError } from "../api";

function errorText(error: unknown) {
  const detail = error instanceof ApiError ? error.detail as { message?: string } | string | undefined : undefined;
  return (typeof detail === "string" ? detail : detail?.message) || (error instanceof Error ? error.message : "操作失败");
}

// Files live on this machine, so the player points at the file itself instead of offering a download.
// `base` is an API path whose /location and /reveal return the platform's own record of the file.
export default function FileLocationActions({ base }: { base: string }) {
  const [message, setMessage] = useState("");
  async function run(action: "reveal" | "copy") {
    setMessage("");
    try {
      if (action === "reveal") {
        await api.post(`${base}/reveal`, {});
      } else {
        const { path } = await api.get<{ path: string }>(`${base}/location`);
        await navigator.clipboard.writeText(path);
        setMessage("已复制路径");
      }
    } catch (cause) { setMessage(errorText(cause)); }
  }
  const button = "inline-flex items-center gap-1 rounded-md bg-black/60 px-2 py-1 text-[12px] text-white hover:bg-black/80";
  return <div className="absolute right-2 top-2 z-10 flex flex-col items-end gap-1">
    <div className="flex gap-1">
      <button type="button" className={button} onClick={() => void run("reveal")}><FolderOpen size={13} aria-hidden />在访达中显示</button>
      <button type="button" className={button} onClick={() => void run("copy")}><Copy size={13} aria-hidden />复制路径</button>
    </div>
    {message && <span role="status" className="rounded-md bg-black/70 px-2 py-0.5 text-[11px] text-white">{message}</span>}
  </div>;
}
