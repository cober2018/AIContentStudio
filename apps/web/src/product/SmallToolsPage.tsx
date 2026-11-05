import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { FolderOpen } from "lucide-react";
import { api, ApiError } from "../api";
import { Button, Chip, EmptyState, ErrorBanner, Page, PageHeader, Section, Spinner } from "../components/ui";

type Job = {
  id: string;
  status: "queued" | "running" | "done" | "failed";
  source: string;
  name: string;
  folder: string;
  duration_ms: number;
  video: boolean;
  files: Record<string, string>;
  cues?: number;
  frames?: number;
  preview?: string;
  error?: { message?: string } | null;
  started_at: string;
  finished_at?: string;
};

const STATUS: Record<Job["status"], [string, "neutral" | "info" | "good" | "bad"]> = {
  queued: ["排队中", "neutral"], running: ["转写中", "info"], done: ["完成", "good"], failed: ["失败", "bad"],
};

function length(ms: number) {
  const seconds = Math.round(ms / 1000);
  const hours = Math.floor(seconds / 3600);
  const clock = `${String(Math.floor(seconds % 3600 / 60)).padStart(2, "0")}:${String(seconds % 60).padStart(2, "0")}`;
  return hours ? `${hours}:${clock}` : clock;
}

function when(value?: string) {
  return value ? new Date(value).toLocaleString("zh-CN", { month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit" }) : "";
}

function errorText(error: unknown) {
  const detail = error instanceof ApiError ? error.detail as { message?: string } | string | undefined : undefined;
  return (typeof detail === "string" ? detail : detail?.message) || (error instanceof Error ? error.message : "操作失败");
}

function JobRow({ job }: { job: Job }) {
  const [message, setMessage] = useState("");
  const [label, tone] = STATUS[job.status];
  const files = Object.entries(job.files || {}).filter(([kind]) => kind !== "images");
  async function reveal() {
    setMessage("");
    try { await api.post(`/tools/media-transcriptions/${job.id}/reveal`, {}); } catch (cause) { setMessage(errorText(cause)); }
  }
  return <li className="space-y-2 py-4">
    <div className="flex flex-wrap items-center gap-2">
      <Chip tone={tone}>{label}</Chip>
      <span className="min-w-0 break-all font-medium text-ink-900">{job.name}</span>
      <span className="text-[12.5px] text-ink-500">{job.video ? "视频" : "音频"} · {length(job.duration_ms)} · {when(job.started_at)}</span>
    </div>
    <p className="break-all text-[12.5px] text-ink-500">源文件：{job.source}</p>
    {job.status === "failed" && <p className="text-[13px] text-rose-700">{job.error?.message || "转写失败"}</p>}
    {job.status === "done" && <>
      <p className="text-[13px] text-ink-600">{job.cues ?? 0} 句{job.frames ? ` · ${job.frames} 张截图` : ""} · 生成 {files.map(([kind]) => kind).join(" / ")}</p>
      {job.preview && <p className="line-clamp-2 text-[13px] leading-relaxed text-ink-700">{job.preview}</p>}
    </>}
    <div className="flex flex-wrap items-center gap-2">
      <span className="min-w-0 break-all text-[12.5px] text-ink-500">输出：{job.folder}</span>
      {job.status === "done" && <Button size="sm" variant="secondary" onClick={() => void reveal()}><span className="inline-flex items-center gap-1"><FolderOpen size={13} aria-hidden />在访达中显示</span></Button>}
      {message && <span role="status" className="text-[12.5px] text-rose-700">{message}</span>}
    </div>
  </li>;
}

export default function SmallToolsPage() {
  const query = useQuery({
    queryKey: ["media-transcriptions"],
    queryFn: () => api.get<{ jobs: Job[] }>("/tools/media-transcriptions"),
    // Jobs run in the background; keep checking only while one is still going.
    refetchInterval: (state) => state.state.data?.jobs.some((job) => job.status === "queued" || job.status === "running") ? 5000 : false,
  });
  return <Page>
    <PageHeader eyebrow="工具" title="小工具" lead="常用的小功能，由第三方模型通过 MCP 调用平台来执行；这里看说明和执行记录。" />
    <Section eyebrow="小工具" title="媒体转文字">
      <div className="space-y-3 text-[14px] leading-relaxed text-ink-700">
        <p>把本机或素材盘上的一个音频、视频文件转成纯文字（.txt）、字幕（.srt）和 md 笔记。视频的 md 按画面切换分段、每段配一张截图；纯音频只有文字。用平台本机转写，不联网、不花钱；超过 10 分钟的文件自动分段转。</p>
        <p>默认存到素材盘「自媒体素材/AIContentStudio/转写/文件名/」，也可以让模型存到指定文件夹；同一个文件再转一次会另建带序号的文件夹，不覆盖。</p>
        <p className="rounded-lg bg-ink-50 px-3 py-2 text-[13px] text-ink-600">对第三方模型说：「用平台把 /Volumes/…/文件.mp4 转成文字、字幕和 md」。MCP 工具：<code>start_media_transcription</code> 提交，<code>get_media_transcription</code> 查结果。</p>
      </div>
    </Section>
    <Section title="转写记录" aside={<span>最近 100 条</span>}>
      {query.isPending ? <Spinner label="读取转写记录…" />
        : query.isError ? <ErrorBanner message={errorText(query.error)} />
        : query.data.jobs.length === 0 ? <EmptyState title="还没有转写记录" hint="让第三方模型调用「媒体转文字」后，这里会列出每次的结果。" />
        : <ul className="divide-y divide-ink-200/80">{query.data.jobs.map((job) => <JobRow key={job.id} job={job} />)}</ul>}
    </Section>
  </Page>;
}
