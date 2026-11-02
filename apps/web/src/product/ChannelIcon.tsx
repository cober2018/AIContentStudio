// Platform site icons stored under public/channel-icons; they only identify the channel in the studio's interface.
const ICONS = new Set(["baijia", "bilibili", "douyin", "juejin", "kuaishou", "netease", "penguin", "toutiao", "wechat", "wechat_channels", "weibo", "x", "xiaohongshu", "xueqiu", "youtube", "zhihu"]);

export function channelIconUrl(channel?: string | null) {
  const key = (channel || "").split(/[.:/]/)[0];
  return ICONS.has(key) ? `/channel-icons/${key}.png` : null;
}

export default function ChannelIcon({ channel, size = 16, className = "" }: { channel?: string | null; size?: number; className?: string }) {
  const url = channelIconUrl(channel);
  return url ? <img src={url} alt="" aria-hidden width={size} height={size} className={`inline-block shrink-0 rounded-[3px] align-[-3px] ${className}`} /> : null;
}
