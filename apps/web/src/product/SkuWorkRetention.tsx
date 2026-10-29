import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { Button, ErrorBanner, Field, inputClass } from "../components/ui";
export default function SkuWorkRetention({projectId,unitId,readOnly}:{projectId:number;unitId:number;readOnly:boolean}){
  const [skuId,setSkuId]=useState<number|null>(null);const [name,setName]=useState("");const [error,setError]=useState("");const [notice,setNotice]=useState("");const [busy,setBusy]=useState(false);
  const [groups,setGroups]=useState({visual:true,sound:true,methods:true});
  const base=`/content-projects/${projectId}/units/${unitId}`;
  useEffect(()=>{let active=true;void api.get<{sku_id:number|null}>(`${base}/production-profile`).then(p=>{if(active)setSkuId(p.sku_id);}).catch(e=>{if(active)setError(e instanceof Error?e.message:"商品关联读取失败");});return()=>{active=false;};},[base]);
  async function save(kind:"plan"|"reference"){setBusy(true);setError("");setNotice("");try{
    if(!skuId)throw new Error("作品还未关联SKU，请先在商品库明确选择商品。");
    if(kind==='reference'){
      const result=await api.get<{items:{id:number;payload_hash:string}[]}>(`${base}/master-revisions`);const master=result.items[0];if(!master)throw new Error("先保存作品版本再留存参考。");
      await api.post(`/product-skus/${skuId}/references`,{master_id:master.id,master_hash:master.payload_hash});setNotice("已留存精确作品版本；缺少成片或工程的部分仍保持待补。");
    }else{
      if(!name.trim())throw new Error("填写方案名称。");if(!Object.values(groups).some(Boolean))throw new Error("至少选择一组可复用设置。");
      const p=await api.get<{settings:Record<string,unknown>}>(`${base}/production-profile`);const fields=[...(groups.visual?['work_type','creation_mode','reference_notes','visual_style','continuity_notes','shared_references']:[]),...(groups.sound?['speech_mode','dialogue_language','music_direction']:[]),...(groups.methods?['production_stages','video_creative_profile']:[])];
      const settings=Object.fromEntries(fields.filter(k=>p.settings[k]!==undefined).map(k=>[k,p.settings[k]]));
      await api.post(`/product-skus/${skuId}/plans`,{name:name.trim(),source_unit_id:unitId,include_methods:groups.methods,settings});setNotice("已另存此SKU创作方案；默认方案与已有作品不变。单次台词、事实、价格和通过状态未复制。");
    }
  }catch(e){setError(e instanceof Error?e.message:"保存失败");}finally{setBusy(false);}}
  return <details className="mb-5 rounded-xl border bg-white p-4"><summary className="cursor-pointer font-medium">保留作品与可复用设置</summary>{error&&<ErrorBanner message={error}/>} {!skuId?<p className="mt-3 text-sm text-slate-500">旧作品待关联SKU，不会按名称自动配对。<Link className="ml-2 text-indigo-700 underline" to="/production?workspace=product">前往商品库</Link></p>:<div className="mt-4 space-y-4"><Button variant="secondary" disabled={readOnly||busy} onClick={()=>void save('reference')}>留存已保存作品版本为参考</Button><Field label="创作方案名称"><input maxLength={200} className={inputClass} value={name} onChange={e=>setName(e.target.value)}/></Field><div className="flex flex-wrap gap-4">{([['visual','表达与视觉'],['sound','声音与配乐方向'],['methods','阶段方法与模型配置']] as const).map(([k,label])=><label className="text-sm" key={k}><input type="checkbox" checked={groups[k]} onChange={e=>setGroups({...groups,[k]:e.target.checked})}/> {label}</label>)}</div><Button disabled={readOnly||busy} onClick={()=>void save('plan')}>保存为此SKU的新创作方案</Button><p className="text-xs text-slate-500">按已保存配置另存；保存方案不自动设为默认。参考作品固定主稿版本，发布资格另行审核。</p></div>}{notice&&<p role="status" className="mt-2 text-sm text-emerald-700">{notice}</p>}</details>;
}
