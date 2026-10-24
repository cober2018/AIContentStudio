import { lazy, Suspense, type ComponentType } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Spinner } from "../components/ui";
const ProductWorkbench = lazy(()=>import("./ProductWorkbench"));
export default function WorkbenchEntry({queue: ProductionQueuePage}:{queue:ComponentType<{workspace?:"product"|"persona"}>}){const [params]=useSearchParams();const workspace=params.get("workspace");
  if(workspace==='product')return <Suspense fallback={<Spinner/>}><ProductWorkbench/></Suspense>;
  if(workspace==='persona')return <Suspense fallback={<Spinner/>}><ProductionQueuePage workspace="persona"/></Suspense>;
  return <div className="mx-auto w-full max-w-[1240px] px-5 pb-20 pt-8 sm:px-8 md:pt-12 lg:px-12 space-y-8"><h1 className="text-2xl font-semibold">这次要制作什么？</h1><div className="grid gap-5 sm:grid-cols-2">{[['persona','角色内容','从主题与本人知识开始，制作文字、图文、音频或视频。'],['product','商品视频','先选择 SKU，再确定销售主线、镜头和素材，完成专业剪辑。']].map(([key,name,description])=><Link key={key} to={`/production?workspace=${key}`} className="rounded-2xl border bg-white p-6 hover:border-indigo-400"><h2 className="text-lg font-semibold">{name}</h2><p className="mt-3 text-sm text-slate-500">{description}</p><span className="mt-5 block text-indigo-700">进入工作台 →</span></Link>)}</div><Link className="text-sm text-slate-500" to="/projects">查看全部项目与内容矩阵</Link></div>;
}
