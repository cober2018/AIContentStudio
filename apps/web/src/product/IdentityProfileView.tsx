import { ReactNode, useEffect, useState } from "react";
import { api } from "../api";
import { Chip } from "../components/ui";

type Json = Record<string, any>;
type Catalog = { production_stages?: { id: string; title: string; order: number }[]; skills: { ref: string; purpose?: string }[]; style_presets: { ref: string; config?: Json }[]; quality_profiles: { ref: string; checks?: string[] }[] };
type Names = { catalog: Catalog | null; methods: Record<number, string> };

// Profile values are stored as stable machine words; these are their reader-facing names.
const WORDS: Record<string, string> = {
  engineering_first: "工程优先", evidence_led_engineering: "证据驱动", low: "克制", medium: "适中", high: "高", explicit: "讲明取舍",
  required: "必须有证据", optional: "可选", technical_editorial: "技术编辑风", diagram_first: "图示优先", auto: "自动", custom: "自定义",
  warm: "温暖", calm: "沉稳", direct: "直接", inferred: "推断", unknown: "未确认", text: "文字", image: "图片", video: "视频", audio: "音频",
};
const STYLE_KEYS: Record<string, string> = { voice: "语气", hype: "夸张程度", tradeoffs: "取舍表达", evidence: "证据要求", specificity: "具体程度", tone: "语调", pace: "节奏" };
const VISUAL_KEYS: Record<string, string> = { preset: "视觉预设", diagram_first: "图示优先", density: "信息密度", palette: "配色", typography: "字体" };
const FACT_RULES: Record<string, string> = { fresh_source_required_for_current_claims: "涉及时效的说法必须有最新来源", label_speculation: "推测内容必须标明是推测" };
const MODALITIES = [["text_creative_profile", "文字"], ["graphic_creative_profile", "图文"], ["audio_creative_profile", "音频"], ["video_creative_profile", "视频"]] as const;
const KNOWN = new Set(["positioning", "target_audience", "content_domains", "expression_style", "visual_language", "long_term_views", "value_propositions", "content_boundaries", "risk_boundaries", "public_fact_policy", "brand_voice_version_id", ...MODALITIES.map(([key]) => key)]);

function word(value: unknown): string {
  if (value === true) return "是";
  if (value === false) return "否";
  if (value === null || value === undefined || value === "") return "未设置";
  return WORDS[String(value)] ?? String(value);
}
function list(value: unknown): string[] { return Array.isArray(value) ? value.map(item => typeof item === "string" ? item : typeof item === "object" && item ? String(item.statement || item.text || item.title || JSON.stringify(item)) : String(item)) : []; }
const PRESETS: Record<string, string> = {
  "text.deep-technical": "深度技术", "text.engineering-explainer": "工程讲解", "text.observational-lifestyle": "观察式生活", "text.reflective-lifestyle": "反思式生活", "text.concise-social": "简洁社交",
  "graphic.technical-editorial": "技术编辑", "graphic.architecture-diagram": "架构图解", "graphic.clean-infographic": "清爽信息图", "graphic.warm-magazine": "温暖杂志", "graphic.documentary-photo": "纪实摄影", "graphic.lifestyle-cards": "生活卡片", "graphic.product-neutral": "商品中性",
  "audio.calm-engineer": "沉稳工程师", "audio.clear-explainer": "清晰讲解", "audio.warm-conversational": "温暖对话", "audio.reflective-story": "反思叙事",
  "quality.video.product": "商品视频", "quality.text.technical": "技术内容", "quality.text.lifestyle": "生活内容", "quality.graphic.editorial": "编辑图文", "quality.graphic.lifestyle": "生活图文", "quality.audio.explainer": "讲解音频", "quality.audio.conversational": "对话音频",
};
export function refName(ref: unknown) {
  if (typeof ref !== "string" || !ref) return "";
  const [key, version] = ref.replace(/^studio\./, "").split("@");
  return `${PRESETS[key] || key}${version ? ` · v${version}` : ""}`;
}

export function useNames(): Names {
  const [names, setNames] = useState<Names>({ catalog: null, methods: {} });
  useEffect(() => {
    let active = true;
    Promise.all([
      api.get<Catalog>("/content-identities/creative-catalog").catch(() => null),
      api.get<{ items: { id: number; name: string }[] }>("/capability-memory/?limit=100&offset=0").catch(() => ({ items: [] })),
    ]).then(([catalog, methods]) => { if (active) setNames({ catalog, methods: Object.fromEntries(methods.items.map(item => [item.id, item.name])) }); });
    return () => { active = false; };
  }, []);
  return names;
}

function Block({ title, note, children, stacked }: { title: string; note?: ReactNode; children: ReactNode; stacked?: boolean }) {
  return <section className="border-t border-ink-200/80 py-7 first:border-t-0 first:pt-0">
    <div className={`grid gap-x-10 gap-y-4 ${stacked ? "" : "xl:grid-cols-[168px_minmax(0,1fr)]"}`}>
      <div><h3 className="font-serif text-[17px] font-semibold text-ink-900">{title}</h3>{note && <p className="mt-1 text-[12.5px] leading-relaxed text-ink-500">{note}</p>}</div>
      <div className="min-w-0">{children}</div>
    </div>
  </section>;
}

function Pairs({ rows }: { rows: [string, ReactNode][] }) {
  if (!rows.length) return <Empty />;
  return <dl className="grid gap-x-8 gap-y-4 sm:grid-cols-2">{rows.map(([label, value]) => <div key={label} className="min-w-0"><dt className="text-[12px] text-ink-500">{label}</dt><dd className="mt-1 break-words text-[14.5px] text-ink-900">{value}</dd></div>)}</dl>;
}

function Empty({ text = "未设置" }: { text?: string }) { return <p className="text-[14px] text-ink-400">{text}</p>; }

function Bullets({ items, mark }: { items: string[]; mark: "do" | "dont" | "dot" }) {
  if (!items.length) return <Empty />;
  const glyph = { do: "✓", dont: "✕", dot: "·" }[mark];
  const tone = { do: "text-emerald-600", dont: "text-rose-500", dot: "text-accent-500" }[mark];
  return <ul className="space-y-2">{items.map(item => <li key={item} className="flex gap-3 text-[14.5px] leading-relaxed text-ink-800"><span aria-hidden className={`mt-px w-3 shrink-0 text-center ${tone}`}>{glyph}</span><span className="min-w-0 break-words">{item}</span></li>)}</ul>;
}

function ReferenceStyle({ value }: { value: Json }) {
  const observations: Json[] = Array.isArray(value.observations) ? value.observations : [];
  return <div className="mt-6 rounded-[14px] border border-ink-200 bg-ink-50/70 p-5">
    <p className="eyebrow">参考风格</p>
    {value.text && <StyleText text={String(value.text)} />}
    {observations.length > 0 && <details className="group mt-4">
      <summary className="cursor-pointer list-none text-[13px] font-medium text-ink-700 hover:text-ink-900"><span className="mr-1 inline-block transition-transform group-open:rotate-90">›</span>{observations.length} 条风格观察</summary>
      <ol className="mt-3 space-y-3">{observations.map((item, index) => <li key={index} className="rounded-xl border border-ink-200/80 bg-surface p-4">
        <p className="text-[14px] leading-relaxed text-ink-800">{item.statement}</p>
        <div className="mt-2 flex flex-wrap gap-1.5"><Chip tone={item.certainty === "direct" ? "good" : "neutral"}>{item.certainty === "direct" ? "直接观察" : word(item.certainty)}</Chip><Chip>{word(item.modality)}</Chip>{item.locator && <span className="self-center text-[12px] text-ink-500">{item.locator}</span>}</div>
      </li>)}</ol>
    </details>}
  </div>;
}

// Reference-style notes arrive as one paragraph with inline "1. 2. 3." rules; reading them as a list is far easier.
function StyleText({ text }: { text: string }) {
  const parts = text.split(/\s*(?=(?:^|\s|。|；)?\d{1,2}[.、]\s?)/).map(part => part.trim()).filter(Boolean);
  const rules = parts.filter(part => /^\d{1,2}[.、]/.test(part));
  const lead = parts.filter(part => !/^\d{1,2}[.、]/.test(part)).join(" ");
  if (rules.length < 2) return <p className="mt-2 font-serif text-[15.5px] leading-relaxed text-ink-900">{text}</p>;
  return <div className="mt-2">
    {lead && <p className="font-serif text-[15.5px] leading-relaxed text-ink-900">{lead}</p>}
    <ol className="mt-3 space-y-2">{rules.map(rule => <li key={rule} className="flex gap-3 text-[14px] leading-relaxed text-ink-800"><span className="w-5 shrink-0 font-serif text-[14px] font-semibold text-accent-500">{rule.match(/^\d{1,2}/)?.[0]}</span><span className="min-w-0">{rule.replace(/^\d{1,2}[.、]\s?/, "")}</span></li>)}</ol>
  </div>;
}

export function CreativeProfile({ label, value, names }: { label: string; value: Json; names: Names }) {
  const catalog = names.catalog;
  const skill = catalog?.skills.find(item => item.ref === value.skill_ref);
  const stages = Object.entries((value.production_stages || {}) as Record<string, { enabled?: boolean; methods?: Json[] }>)
    .sort(([a], [b]) => (catalog?.production_stages?.find(item => item.id === a)?.order ?? 99) - (catalog?.production_stages?.find(item => item.id === b)?.order ?? 99));
  const model = "按 设置 → AI 与模型 的路由";
  const methodName = (method: Json) => method.source_kind === "studio_builtin"
    ? catalog?.skills.find(item => item.ref === method.skill_ref)?.purpose || refName(method.skill_ref)
    : names.methods[method.artifact_id] ? `${names.methods[method.artifact_id]}` : `能力记忆 #${method.artifact_id}`;
  return <article className="rounded-[16px] border border-ink-200/90 bg-surface p-5 sm:p-6">
    <header className="flex flex-wrap items-baseline justify-between gap-2">
      <h4 className="font-serif text-[18px] font-semibold text-ink-900">{label}</h4>
      <span className="text-[12px] text-ink-500">{word(value.mode)}模式</span>
    </header>
    <p className="mt-2 text-[14px] leading-relaxed text-ink-700">{skill?.purpose || refName(value.skill_ref) || "未选择主方法"}</p>
    <dl className="mt-4 grid gap-x-6 gap-y-3 text-[13px] sm:grid-cols-3 [&_dd]:break-words">
      <div><dt className="text-ink-500">风格预设</dt><dd className="mt-0.5 text-ink-900">{refName(value.style_preset_ref) || "未设置"}</dd></div>
      <div><dt className="text-ink-500">质量标准</dt><dd className="mt-0.5 text-ink-900">{refName(value.quality_profile_ref) || "未设置"}</dd></div>
      <div><dt className="text-ink-500">模型</dt><dd className="mt-0.5 break-words text-ink-900">{model}</dd></div>
    </dl>
    {stages.length > 0 && <ol className="mt-5 grid gap-px overflow-hidden rounded-xl border border-ink-200/80 bg-ink-200/80 sm:grid-cols-2">
      {stages.map(([stage, config], index) => {
        const enabled = config?.enabled !== false;
        const methods = (config?.methods || []).filter(method => method.enabled !== false);
        return <li key={stage} className={`bg-surface px-4 py-3 ${enabled ? "" : "opacity-55"}`}>
          <div className="flex items-baseline gap-2"><span className="font-serif text-[12.5px] tabular-nums text-ink-400">{String(index + 1).padStart(2, "0")}</span><span className="text-[13.5px] font-medium text-ink-900">{catalog?.production_stages?.find(item => item.id === stage)?.title || stage}</span>{!enabled && <span className="ml-auto text-[11.5px] text-ink-500">已关闭</span>}</div>
          {enabled && <p className="mt-1 pl-7 text-[12.5px] leading-relaxed text-ink-600">{methods.length ? methods.map(methodName).join(" · ") : "未配置方法"}</p>}
        </li>;
      })}
      {stages.length % 2 === 1 && <li aria-hidden className="hidden bg-surface sm:block" />}
    </ol>}
    {value.parameters && Object.keys(value.parameters).length > 0 && <p className="mt-3 text-[12.5px] text-ink-500">参数：{Object.entries(value.parameters).map(([key, item]) => `${key} = ${typeof item === "object" ? JSON.stringify(item) : item}`).join("；")}</p>}
  </article>;
}

export function ProfileOverview({ profile, showCreative = true }: { profile: Json; showCreative?: boolean }) {
  const names = useNames();
  const style: Json = profile.expression_style && typeof profile.expression_style === "object" ? profile.expression_style : {};
  const visual: Json = profile.visual_language && typeof profile.visual_language === "object" ? profile.visual_language : {};
  const facts: Json = profile.public_fact_policy && typeof profile.public_fact_policy === "object" ? profile.public_fact_policy : {};
  const creative = MODALITIES.filter(([key]) => profile[key] && typeof profile[key] === "object");
  const extra = Object.keys(profile).filter(key => !KNOWN.has(key));
  const styleRows = Object.entries(style).filter(([key]) => key !== "reference_style").map(([key, value]) => [STYLE_KEYS[key] || key, typeof value === "object" ? JSON.stringify(value) : word(value)] as [string, ReactNode]);
  const visualRows = Object.entries(visual).map(([key, value]) => [VISUAL_KEYS[key] || key, typeof value === "object" ? JSON.stringify(value) : word(value)] as [string, ReactNode]);
  return <div>
    <Block title="身份" note="这个角色是谁、对谁说话">
      {profile.positioning ? <p className="font-serif text-[21px] leading-[1.55] text-ink-900">{String(profile.positioning)}</p> : <Empty text="还没有写定位" />}
      <div className="mt-6 grid gap-6 sm:grid-cols-2">
        <div><p className="eyebrow mb-2.5">目标受众</p>{list(profile.target_audience).length ? <div className="flex flex-wrap gap-1.5">{list(profile.target_audience).map(item => <Chip key={item}>{item}</Chip>)}</div> : <Empty />}</div>
        <div><p className="eyebrow mb-2.5">内容领域</p>{list(profile.content_domains).length ? <div className="flex flex-wrap gap-1.5">{list(profile.content_domains).map(item => <Chip key={item} tone="accent">{item}</Chip>)}</div> : <Empty />}</div>
      </div>
    </Block>
    <Block title="表达" note="语气、证据习惯与参考风格">
      <Pairs rows={styleRows} />
      {style.reference_style && typeof style.reference_style === "object" && <ReferenceStyle value={style.reference_style} />}
      {profile.brand_voice_version_id != null && <p className="mt-4 text-[13px] text-ink-500">品牌语气版本 #{String(profile.brand_voice_version_id)}</p>}
    </Block>
    <Block title="视觉" note="图文与视频的画面倾向"><Pairs rows={visualRows} /></Block>
    <Block title="观点与边界" note="长期立场，以及不碰的事">
      <div className="grid gap-8 md:grid-cols-2">
        <div><p className="eyebrow mb-3">价值主张</p><Bullets items={list(profile.value_propositions)} mark="dot" /></div>
        <div><p className="eyebrow mb-3">长期观点</p><Bullets items={list(profile.long_term_views)} mark="dot" /></div>
        <div><p className="eyebrow mb-3">内容边界</p><Bullets items={list(profile.content_boundaries)} mark="do" /></div>
        <div><p className="eyebrow mb-3">风险边界</p><Bullets items={list(profile.risk_boundaries)} mark="dont" /></div>
      </div>
      {Object.keys(facts).length > 0 && <div className="mt-7"><p className="eyebrow mb-3">公开事实规则</p><Bullets mark="do" items={Object.entries(facts).filter(([, value]) => value !== false).map(([key, value]) => FACT_RULES[key] || `${key}${value === true ? "" : `：${word(value)}`}`)} /></div>}
    </Block>
    {showCreative && creative.length > 0 && <Block stacked title="创作配置" note="每种内容形态默认怎么做、按什么步骤">
      <div className="grid gap-4">{creative.map(([key, label]) => <CreativeProfile key={key} label={label} value={profile[key]} names={names} />)}</div>
    </Block>}
    {extra.length > 0 && <Block title="其他资料"><Pairs rows={extra.map(key => [key, typeof profile[key] === "object" ? JSON.stringify(profile[key]) : word(profile[key])])} /></Block>}
    <details className="group border-t border-ink-200/80 pt-5">
      <summary className="cursor-pointer list-none text-[13px] text-ink-500 hover:text-ink-800"><span className="mr-1 inline-block transition-transform group-open:rotate-90">›</span>查看原始数据</summary>
      <pre className="mt-3 max-h-[480px] overflow-auto rounded-xl bg-ink-900 p-4 font-mono text-[12px] leading-relaxed text-ink-100">{JSON.stringify(profile, null, 2)}</pre>
    </details>
  </div>;
}
