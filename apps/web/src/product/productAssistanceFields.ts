import type { AssistanceField, AssistanceValue } from "./formAssistanceTypes";
import type { ProductContext, ProductOffer } from "./project/types";
export const productLabels: Record<string, string> = { name: "商品名称", variant: "准确规格", url: "商品链接", description: "商品说明", selling_points: "卖点", excluded_claims: "禁用说法", buyer_situation: "使用场景", purchase_reason_evidence: "购买理由依据", main_objection: "最大顾虑", objection_answer: "顾虑回答", unsuitable_for: "不适用条件", seller_advantage: "商家优势", target_duration_seconds: "目标时长", expression_test: "表达小测试", category: "商品品类" };
export function productAssistanceFields(product: Partial<ProductContext>, update: (patch: Partial<ProductContext>) => void): AssistanceField[] {
 return Object.entries(productLabels).map(([key,label])=>({key,label,value:(product[key]??null) as AssistanceValue,kind:["selling_points","excluded_claims"].includes(key)?"list":key==="target_duration_seconds"?"number":["variant","description","url","purchase_reason_evidence","seller_advantage"].includes(key)?"fact":key==="expression_test"?"choice":"text",...(key==="expression_test"?{options:["scene","demo","compare","faq","selection"]}:{}),apply:value=>update({[key]:value} as Partial<ProductContext>)}));
}
export function offerAssistanceFields(offer: ProductOffer|null, update:(value:ProductOffer)=>void):AssistanceField[]{
 if(!offer)return [];
 return Object.entries({text:"价格说明",currency:"币种",original_price:"原价",sale_price:"售价",conditions:"适用条件",checked_at:"核对时间",valid_until:"截止时间",timezone:"时区"}).map(([key,label])=>({key:`offer.${key}`,label,kind:"fact",value:(offer[key]??null) as AssistanceValue,apply:value=>update({...offer,[key]:value})}));
}
