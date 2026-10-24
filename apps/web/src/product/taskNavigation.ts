import { useLocation } from "react-router-dom";

const taskPath = /^(?:\/|\/home|\/opportunities(?:\/\d+)?|\/projects(?:\/\d+(?:\/units\/\d+\/production)?)?|\/production|\/review|\/learning)$/;

export function taskReturn(value: string | null, fallback = "", depth = 0): string {
  if (!value || value.length > 16000 || !value.startsWith("/") || value.startsWith("//") || /[\\\u0000-\u001f]/.test(value)) return fallback;
  try {
    const url = new URL(value, "https://studio.local");
    if (url.origin !== "https://studio.local" || !taskPath.test(url.pathname)) return fallback;
    const previous = depth < 8 ? taskReturn(url.searchParams.get("return_to"), "", depth + 1) : "";
    if (previous) url.searchParams.set("return_to", previous); else url.searchParams.delete("return_to");
    return `${url.pathname}${url.search}${url.hash}`;
  } catch { return fallback; }
}

export function useTaskLink() {
  const location = useLocation();
  return (target: string) => {
    const safeTarget = taskReturn(target);
    if (!safeTarget) return target;
    const destination = new URL(safeTarget, "https://studio.local");
    function withoutDestination(source: string): string {
      if (!source) return "";
      const prior = new URL(source, "https://studio.local");
      const upstream = withoutDestination(prior.searchParams.get("return_to") || "");
      if (prior.pathname === destination.pathname) return upstream;
      if (upstream) prior.searchParams.set("return_to", upstream);
      else prior.searchParams.delete("return_to");
      return `${prior.pathname}${prior.search}${prior.hash}`;
    }
    // Remove the previous visit to the destination so repeated review/edit trips cannot grow the chain.
    const current = withoutDestination(taskReturn(`${location.pathname}${location.search}${location.hash}`));
    if (current) destination.searchParams.set("return_to", current);
    return `${destination.pathname}${destination.search}${destination.hash}`;
  };
}
