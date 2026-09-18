import { useNavigate } from "react-router-dom";
import { ChevronDown } from "lucide-react";

// 启动页：内部项目免登录，点开始直接进入系统。
// 视觉基调 = 全站主题：纯白底、gray-900 文字、黑色点缀、Space Grotesk × Kudryashev 双字体。

const VIDEO_URL =
  "https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260718_132657_c3ce20d7-d20a-4498-b552-6d966fe3720a.mp4";

export default function Landing() {
  const navigate = useNavigate();

  return (
    <div className="relative flex h-screen flex-col overflow-hidden bg-white">
      {/* 顶部导航 */}
      <nav className="z-10 flex items-center justify-between px-6 pt-6 md:px-10 md:pt-10 lg:px-14">
        <span className="font-grotesk text-sm font-medium tracking-tight text-gray-900">ai content studio</span>
        <span className="h-3 w-3 rounded-full border-[3px] border-solid border-black" />
      </nav>

      {/* 背景视频：居中 80%，四边白色渐隐 */}
      <div className="absolute inset-0 z-0 flex items-center justify-center">
        <div className="relative h-[80%] w-[80%] overflow-hidden">
          <video src={VIDEO_URL} className="h-full w-full object-cover" autoPlay loop muted playsInline />
          {/* 四边白→透明渐隐，把视频融进白底 */}
          <div className="pointer-events-none absolute inset-x-0 top-0 h-24 bg-gradient-to-b from-white to-transparent" />
          <div className="pointer-events-none absolute inset-x-0 bottom-0 h-24 bg-gradient-to-t from-white to-transparent" />
          <div className="pointer-events-none absolute inset-y-0 left-0 w-24 bg-gradient-to-r from-white to-transparent" />
          <div className="pointer-events-none absolute inset-y-0 right-0 w-24 bg-gradient-to-l from-white to-transparent" />
        </div>
      </div>

      {/* 主内容 */}
      <main className="z-10 flex flex-1 flex-col items-center justify-center px-6 text-center">
        <h1 className="text-4xl font-thin leading-[1.1] tracking-tight text-gray-900 sm:text-5xl md:text-6xl lg:text-7xl xl:text-8xl">
          <span className="font-kudryashev">facts first, </span>
          <span className="font-grotesk">content flows.</span>
        </h1>
        <p className="mt-6 max-w-md font-helvetica text-sm leading-relaxed text-gray-900 sm:mt-8 sm:text-base md:max-w-lg lg:max-w-xl lg:text-lg">
          事实驱动的内容生产中心——从量化数据与舆情转写中沉淀可信事实，面向抖音、小红书、公众号
          生成经校验与审核的内容，一键出库。
        </p>
        <button
          onClick={() => navigate("/dashboard")}
          className="mt-10 rounded-full border border-gray-900 px-8 py-2.5 font-grotesk text-sm font-medium text-gray-900 transition-colors hover:bg-gray-900 hover:text-white"
        >
          开始使用
        </button>
      </main>

      {/* 底部：版权 / 下滑进入 / 状态点 */}
      <footer className="z-10 flex items-center justify-between px-6 pb-6 md:px-10 md:pb-10 lg:px-14">
        <span className="font-helvetica text-xs text-gray-500 sm:text-sm">© 2026 AI Content Studio · Internal</span>
        <button
          aria-label="开始"
          onClick={() => navigate("/dashboard")}
          className="absolute bottom-6 left-1/2 -translate-x-1/2 sm:bottom-10"
        >
          <ChevronDown className="h-6 w-6 animate-bounce text-gray-800 sm:h-7 sm:w-7" strokeWidth={1.5} />
        </button>
        <div className="flex items-center gap-4">
          <span className="font-helvetica text-xs text-gray-700 sm:text-sm">v0.1</span>
          <span className="font-helvetica text-xs text-gray-700 sm:text-sm">事实不可漂移</span>
        </div>
      </footer>
    </div>
  );
}
