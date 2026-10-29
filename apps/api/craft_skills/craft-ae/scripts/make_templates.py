"""Author the data-driven AE template projects into the local template store.

Usage: python3 make_templates.py <store> [template-id ...]
Each template is <store>/<id>/<version>/template.aepx (XML) with its image files beside it.
Expressions read one JSON literal between /*AICS_DATA*/ and /*AICS_END*/; aerender cannot load JSON footage,
so a render rewrites that literal in a copy of the XML and never scripts the running AE.
Run it only when After Effects has no unsaved project open: it starts a new project for each template.
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

# A changed template gets a new version folder; earlier versions stay as they were.
VERSIONS = {"compare-pair": "v2"}
SAMPLES = {
    "number-card": {"number": "99%", "label": "跨洋数据走海底光缆", "source": "来源：TeleGeography"},
    "title-card": {"kicker": "海底光缆", "title": "消息怎么跨过大洋", "subtitle": "一条微信背后的物理旅程"},
    "diagram-flow": {"title": "一条消息的路线", "step1": "手机发出", "step2": "基站与城域网", "step3": "登陆站", "step4": "海底光缆"},
    "photo-push": {"caption": "深海里的光缆只有水管那么粗", "tag": "AI 示意", "_images": ["image"]},
    "compare-pair": {"left_label": "海底光缆", "right_label": "浇花水管", "note": "深海段只有水管那么粗", "tag": "", "_images": []},
    "map-route": {"title": "上海 → 洛杉矶", "from": "上海", "to": "洛杉矶", "from_x": 0.78, "from_y": 0.42, "to_x": 0.18, "to_y": 0.44},
    "keyword-contrast": {"sentence": "能留住人的|不是流量|是", "beats": "", "word": "信任"},
    "keyword-slab": {"line1": "这一步最容易被忽略", "word": "先定目标"},
    "impact-line": {"sentence": "三秒看懂选购重点", "accent": "重点", "sub": "接下来只讲清楚一件事"},
    "outline-box-title": {"title": "核心卖点", "sub": "就这一个"},
    "split-rise-title": {"title": "选对比买贵更重要", "sub": "本期的第一条原则"},
    "quote-card": {"line1": "好的工具", "line2": "不是功能最多", "line3": "而是你每天都会打开", "line4": "用久了才知道", "accent": "每天,用久了", "source": "—— 本期总结"},
    "quote-hold": {"line1": "方法可以学", "line2": "节奏可以练", "line3": "坚持才是门槛"},
    "pair-blocks": {"top": "不是买得越多越好", "bottom": "而是用得越久越值"},
    "ring-mark": {"x": 0.5, "y": 0.4, "w": 0.4, "h": 0.08, "label": "关键在这一行", "accent": "这一行"},
    "callout-label": {"p1_x": 0.3, "p1_y": 0.3, "p1_text": "接口", "p2_x": 0.7, "p2_y": 0.55, "p2_text": "指示灯", "p3_x": 0, "p3_y": 0, "p3_text": ""},
    "magnifier": {"x": 0.5, "y": 0.35, "r": 0.12},
    "focus-dim": {"regions": "0.5,0.25,0.8,0.1;0.5,0.5,0.8,0.1;0.5,0.75,0.8,0.1"},
    "host-to-chip": {"caption": "看这组数据", "face_x": 0.46, "face_y": 0.405, "face_size": 0.49, "chip_size": 300, "_images": ["host", "graphic"]},
    "host-parallel": {"item1": "看细节", "item2": "看场景", "item3": "看上手", "beats": "1.0-2.6,3.4-5.0,5.8-6.9", "_images": ["img1", "img2", "img3"]},
    "name-plate": {"name": "林一", "title": "十年家居设计师"},
    "name-chevron": {"name": "林一", "title": "十年家居设计师"},
    "value-swap": {"sentence": "上下文窗口从", "old": "128K", "new": "1M", "note": "一年翻了八倍"},
    "count-title": {"number": "3", "rest": "个方法", "line2": "解决收纳难题"},
    "metric-trend": {"label": "本周剪辑效率", "value": 67, "unit": "%", "points": "39,48,55,67", "xlabels": "周一,周二,周三,周四", "source": "数据：本账号后台"},
    "number-roll": {"label": "2024 全年营销费用", "prefix": "¥", "from": 0, "to": 3000000000, "decimals": 0, "unit": "", "delta": "+45%", "note": "比上一年多花了九亿"},
    "term-card": {"term": "量化宽松", "tag": "QE", "icon": "¥", "line1": "央行印钱买入国债等资产", "line2": "把流动性压进市场、刺激经济"},
    "pick-one": {"question": "五个方案，我选哪个？", "options": "方案A·全手动,方案B·半自动,方案C·全自动,方案D·外包,方案E·先不做", "answer": 3, "result": "每月省下 72 小时", "accent": "72 小时"},
    "line-story": {"title": "指数点位 · 五年推演", "source": "历史已发生 · 后两年为假设", "history": "3200,3350,3280,3520,3460,3700", "forecast": "3780,3900,4115", "alt": "3850,4100,4400", "xlabels": "2020,,2021,,2022,,2023,,2024", "turn_label": "这里买入", "end_label": "", "alt_label": "乐观情形"},
    "bar-grow": {"title": "年营收（亿元）", "labels": "2020,2021,2022,2023,2024", "values": "12,18,27,45,86", "highlight": 5, "conclusion": "", "source": "来源：公司年报"},
    "glass-board": {"kicker": "TALKCRAFT · 口播", "title": "口播工作流", "step1": "文稿", "step2": "配音", "step3": "成片", "step4": "", "summary": "一遍过 · 3 分 20 秒", "_images": ["host"]},
    "step-line": {"title": "三步开始", "step1": "先把目标写成一句话", "step2": "砍掉两件不做的事", "step3": "今天就动第一步", "step4": "", "step5": "", "current": 1},
    "converge": {"title": "四个平台的数据，怎么汇成一张表", "s1": "抖音", "s2": "小红书", "s3": "B 站", "s4": "公众号", "result": "一张表", "note": "每天 8 点自动更新"},
    "line-carry": {"a_title": "第一部分 · 为什么慢", "a_sub": "三个拖慢流程的地方", "b_title": "第二部分 · 怎么快", "b_sub": "把三处改成自动", "_images": ["image"]},
    "timeline-travel": {"kicker": "更新记录", "title": "每个月都在更新", "points": "2026.07|公开发布|第一版上线;2026.08|模板库|加入 16 个模板;2026.09|素材搜索|接入免费素材库;2026.10|一句话成片|输入需求自动出片", "stop": 4},
    "slider-compare": {"before_label": "调色前", "after_label": "调色后", "_images": ["before", "after"]},
    "split-6040": {"title": "它一晚上干了三件事", "p1": "读完 40 份资料", "p2": "写好三版初稿", "p3": "跑测试、修 bug", "_images": ["image"]},
    "before-after-scrub": {"after_label": "改版后", "before_label": "改版前", "_images": ["after"]},
    "chapter-card": {"number": "01", "title": "泡沫是怎么吹起来的", "sub": "2006—2008", "color": "ink"},
    "chapter-list": {"c1": "先说结论", "c2": "钱是怎么被拿走的", "c3": "三个最常见的坑", "c4": "你今天能做什么", "c5": "", "current": 2},
    "title-to-label": {"title": "第二步 · 拆解需求", "p1": "把一句话需求拆成 3~5 个小目标", "p2": "每个小目标写清做完长什么样", "p3": "先做最不确定的那一个"},
    "lead-word": {"word": "效率", "rest": "才是唯一的护城河", "accent": "护城河", "sub": "不是参数，也不是模型大小"},
    "news-desk": {"line_x": 0.08, "line_y": 0.3, "line_w": 0.5, "source": "来源：示例报道", "_images": ["image1", "image2"]},
    "layout-relay": {"cap1": "主图 · 整体", "cap2": "细节 · 镜头", "cap3": "上手 · 握持", "_images": ["image1", "image2", "image3"]},
    "grid-hero": {"hero": 3, "cap1": "候选 ①", "cap2": "候选 ②", "cap3": "候选 ③ · 最终选它", "cap4": "候选 ④", "_images": ["image1", "image2", "image3", "image4"]},
    "echo-bed": {"title": "网友发来的现场画面", "source": "手机拍摄 · 原比例 9:16", "_images": ["image"]},
    "route-pin": {"p1_x": 0.3, "p1_y": 0.2, "p1_name": "北京 · 总部", "p2_x": 0.6, "p2_y": 0.45, "p2_name": "上海 · 中转仓", "p3_x": 0.42, "p3_y": 0.72, "p3_name": "深圳 · 工厂", "_images": ["map"]},
    "shape-wipe": {"direction": "left", "color": "ink"},
    "color-slam": {"line1": "不是不会用", "line2": "是没想清楚", "kicker": "01 · 最常见的卡点", "color": "blue", "_images": ["image"]},
    "follow-button": {"hint": "点个关注，下期讲选购", "label": "关注", "done": "已关注"},
    "follow-card-x": {"name": "陈叙白", "handle": "@chenxubai", "bio": "十年产品设计，现在做独立开发", "following": "286", "followers": "12.4万", "button": "关注", "done": "已关注", "_images": ["avatar"]},
    "follow-card-dy": {"name": "林一", "account": "账号：linyi2026", "likes": "3.2万", "following": "238", "fans": "6455", "bio": "持续分享家居收纳和好物测评", "bio2": "每周三、周六更新", "button": "+ 关注", "done": "已关注", "_images": ["avatar"]},
    "product-hero": {"name": "头戴降噪耳机", "sub": "H2 · 40 小时续航", "tag": "新品", "_images": ["product"]},
    "product-angles": {"a1": "正面", "a2": "侧面", "a3": "收纳盒", "a4": "", "_images": ["img1", "img2", "img3"]},
    "selling-points": {"t1": "主动降噪", "d1": "通勤路上安静下来", "t2": "40 小时续航", "d2": "一周只充一次电", "t3": "230 克轻量", "d3": "戴一天头不累", "beats": "", "_images": ["product"]},
    "check-list": {"title": "这几点都有", "i1": "主动降噪", "i2": "40 小时续航", "i3": "IPX4 防水", "i4": "双设备连接", "i5": "", "beats": ""},
    "spec-table": {"title": "参数一览", "rows": "重量|230 g;续航|40 小时;充电|Type-C 快充;降噪|主动降噪;蓝牙|5.3", "highlight": 2, "_images": ["product"]},
    "compare-table": {"title": "和上一代比", "ours": "新款", "other": "旧款", "rows": "主动降噪|✓|✗;续航|40 小时|24 小时;防水|✓|✓;双设备连接|✓|✗"},
    "dimension-mark": {"w_label": "宽 18 cm", "h_label": "高 20 cm", "d_label": "厚 8 cm", "bx0": 0.28, "by0": 0.32, "bx1": 0.7, "by1": 0.72, "_images": ["product"]},
    "price-drop": {"label": "券后到手价", "original": "¥399", "price": "¥259", "saving": "立减 ¥140"},
    "deal-timer": {"label": "限时优惠", "ends": "今晚 24:00 截止", "countdown": 8130},
    "layer-stack": {"title": "四层结构", "layers": "外层|防泼水面料;保暖层|蓬松棉;贴肤层|亲肤针织;衬里|防静电"},
    "use-steps": {"title": "三步上手", "s1": "长按开机", "d1": "自动进入配对", "s2": "戴上耳机", "d2": "听到提示音即连接", "s3": "双击切换模式", "d3": "降噪 / 通透一键切换", "beats": "", "_images": ["img1", "img2", "img3"]},
    "review-cards": {"title": "买家怎么说", "r1_text": "降噪比我想的好，地铁里能安静下来", "r1_name": "王小雨", "r1_stars": 5, "r2_text": "续航真的长，一周充一次", "r2_name": "李", "r2_stars": 5, "r3_text": "就是夹头，要戴一阵适应", "r3_name": "陈", "r3_stars": 4, "source": "来源：示例评价", "beats": ""},
    "cert-card": {"k1": "第三方机构检测", "k2": "电池安全测试通过", "k3": "报告编号可查", "source": "来源：示例检测报告", "_images": ["cert"]},
    "buy-cta": {"name": "头戴降噪耳机", "price": "¥259", "cta": "点下方链接看看", "_images": ["product"]},
    "color-swatch": {"c1": "云白", "c2": "雾蓝", "c3": "曜黑", "c4": "", "_images": ["img1", "img2", "img3"]},
}
IMAGES = {"map-route": ["map.png"], "photo-push": ["image.png"], "compare-pair": ["left.png", "right.png"],
          "ring-mark": ["image.png"], "callout-label": ["image.png"], "magnifier": ["image.png"], "focus-dim": ["image.png"],
          "host-to-chip": ["host.png", "graphic.png"], "glass-board": ["host.png"], "line-carry": ["image.png"],
          "slider-compare": ["before.png", "after.png"], "split-6040": ["image.png"], "before-after-scrub": ["before.png", "after.png"], "host-parallel": ["img1.png", "img2.png", "img3.png"],
          "news-desk": ["image1.png", "image2.png"], "layout-relay": ["image1.png", "image2.png", "image3.png"], "grid-hero": ["image1.png", "image2.png", "image3.png", "image4.png"],
          "echo-bed": ["image.png"], "route-pin": ["map.png"], "color-slam": ["image.png"], "follow-card-x": ["avatar.png"], "follow-card-dy": ["avatar.png"],
          "product-hero": ["product.png"], "product-angles": ["img1.png", "img2.png", "img3.png", "img4.png"], "selling-points": ["product.png"], "spec-table": ["product.png"],
          "dimension-mark": ["product.png"], "use-steps": ["img1.png", "img2.png", "img3.png"], "cert-card": ["cert.png"], "buy-cta": ["product.png"], "color-swatch": ["img1.png", "img2.png", "img3.png", "img4.png"]}

JSX = r'''
var STORE=__STORE__; var IDS=__IDS__; var SAMPLES=__SAMPLES__; var DATA=""; var VERSIONS=__VERSIONS__; var LOG=__LOG__; var ASPECT=__ASPECT__; var FNL=__FNL__;
var W=1080,H=1920,FPS=30,LEN=10;
var BG=[0.035,0.047,0.067],ACCENT=[0.31,0.89,0.69],WHITE=[1,1,1],GREY=[0.62,0.66,0.72],CHIP=[0.06,0.12,0.2];
var D='var d=/*AICS_DATA*/'+DATA+'/*AICS_END*/;';
var CENTER='var r=sourceRectAtTime(time,false);[r.left+r.width/2,r.top+r.height/2]';
function fit(m){return 'var r=sourceRectAtTime(time,false);var k=r.width>'+m+'?'+m+'/r.width:1;value*k';}
function ease(p){for(var k=1;k<=p.numKeys;k++){var e=new KeyframeEase(0,80);var n=p.value instanceof Array?p.value.length:1;if(p.propertyValueType==PropertyValueType.TwoD_SPATIAL||p.propertyValueType==PropertyValueType.ThreeD_SPATIAL)n=1;var a=[];for(var i=0;i<n;i++)a.push(e);p.setTemporalEaseAtKey(k,a,a);}}
function base(comp){comp.layers.addSolid(BG,"base",W,H,1);
 var g=comp.layers.addSolid(ACCENT,"glow",W,H,1);var m=g.property("ADBE Mask Parade").addProperty("ADBE Mask Atom");var s=new Shape();
 s.vertices=[[140,-300],[W-140,-300],[W-140,700],[140,700]];s.closed=true;m.property("ADBE Mask Shape").setValue(s);m.property("ADBE Mask Feather").setValue([420,420]);g.property("Opacity").setValue(16);}
function text(comp,name,field,size,color,font,y,maxw){var l=comp.layers.addText(name);l.name="@"+field;var p=l.property("Source Text");var t=p.value;t.resetCharStyle();t.font=font;t.fontSize=size;t.fillColor=color;t.applyFill=true;t.applyStroke=false;t.justification=ParagraphJustification.CENTER_JUSTIFY;p.setValue(t);
 p.expression=D+'String(d["'+field+'"]||"")';l.property("Anchor Point").expression=CENTER;l.property("Position").setValue([W/2,y]);l.property("Scale").expression=fit(maxw||960);return l;}
function rise(l,t0,dy){var p=l.property("Position");var v=p.value;p.setValueAtTime(t0,[v[0],v[1]+(dy||30)]);p.setValueAtTime(t0+0.45,v);ease(p);var o=l.property("Opacity");o.setValueAtTime(t0,0);o.setValueAtTime(t0+0.35,100);}
function pop(l,t0){var s=l.property("Scale");s.setValueAtTime(t0,[60,60]);s.setValueAtTime(t0+0.25,[106,106]);s.setValueAtTime(t0+0.4,[100,100]);ease(s);var o=l.property("Opacity");o.setValueAtTime(t0,0);o.setValueAtTime(t0+0.15,100);}
function bar(comp,y,t0){var s=comp.layers.addShape();s.name="accent bar";var g=s.property("Contents").addProperty("ADBE Vector Group").property("Contents");var r=g.addProperty("ADBE Vector Shape - Rect");r.property("Size").setValue([140,8]);r.property("Roundness").setValue(4);
 g.addProperty("ADBE Vector Graphic - Fill").property("Color").setValue(ACCENT);s.property("Position").setValue([W/2,y]);var sc=s.property("Scale");sc.setValueAtTime(t0,[0,100]);sc.setValueAtTime(t0+0.5,[100,100]);ease(sc);return s;}
function box(comp,name,w,h,y,fill,stroke){var s=comp.layers.addShape();s.name=name;var g=s.property("Contents").addProperty("ADBE Vector Group").property("Contents");var r=g.addProperty("ADBE Vector Shape - Rect");r.property("Size").setValue([w,h]);r.property("Roundness").setValue(28);
 g.addProperty("ADBE Vector Graphic - Fill").property("Color").setValue(fill);if(stroke){var st=g.addProperty("ADBE Vector Graphic - Stroke");st.property("Color").setValue(stroke);st.property("Stroke Width").setValue(4);}s.property("Position").setValue([W/2,y]);return s;}
function hideEmpty(l,field){l.property("Opacity").expression=D+'d["'+field+'"]?value:0';}

function numberCard(comp){
 var n=text(comp,"99%","number",280,ACCENT,"PingFangSC-Semibold",860,960);pop(n,0.2);
 var b=bar(comp,1040,0.6);
 var l=text(comp,"label","label",64,WHITE,"PingFangSC-Semibold",1140,960);rise(l,0.7);
 var s=text(comp,"source","source",30,GREY,"PingFangSC-Regular",1500,960);rise(s,1.1,10);hideEmpty(s,"source");}
function titleCard(comp){
 var k=text(comp,"kicker","kicker",40,ACCENT,"PingFangSC-Semibold",760,900);rise(k,0.15,20);hideEmpty(k,"kicker");
 var t=text(comp,"title","title",104,WHITE,"PingFangSC-Semibold",900,960);rise(t,0.35);
 bar(comp,1010,0.8);
 var s=text(comp,"subtitle","subtitle",48,GREY,"PingFangSC-Regular",1100,960);rise(s,1.0,20);hideEmpty(s,"subtitle");}
function diagramFlow(comp){
 var t=text(comp,"title","title",76,WHITE,"PingFangSC-Semibold",420,960);rise(t,0.15);bar(comp,500,0.5);
 for(var i=0;i<4;i++){var y=700+i*290;var t0=0.6+i*0.4;var f="step"+(i+1);
  if(i>0){var a=comp.layers.addShape();a.name="arrow "+i;var g=a.property("Contents").addProperty("ADBE Vector Group").property("Contents");var sh=new Shape();sh.vertices=[[0,-40],[0,40]];sh.closed=false;
   g.addProperty("ADBE Vector Shape - Group").property("Path").setValue(sh);var st=g.addProperty("ADBE Vector Graphic - Stroke");st.property("Color").setValue(ACCENT);st.property("Stroke Width").setValue(6);
   var tp=a.property("Contents").addProperty("ADBE Vector Filter - Trim");tp.property("End").setValueAtTime(t0-0.2,0);tp.property("End").setValueAtTime(t0+0.1,100);a.property("Position").setValue([W/2,y-145]);hideEmpty(a,f);}
  var b=box(comp,"box "+(i+1),760,170,y,CHIP,ACCENT);var o=b.property("Opacity");o.setValueAtTime(t0,0);o.setValueAtTime(t0+0.3,100);hideEmpty(b,f);
  var l=text(comp,f,f,56,WHITE,"PingFangSC-Semibold",y,680);rise(l,t0+0.05,16);hideEmpty(l,f);}}
function mapRoute(comp,folder){
 var img=app.project.importFile(new ImportOptions(new File(folder.fsName+"/map.png")));var m=comp.layers.add(img);m.name="@map";
 m.property("Scale").expression='var k=Math.min(thisComp.width/width,thisComp.height/height)*100;[k,k]';m.property("Opacity").setValue(55);
 var sp=D+'var L=thisComp.layer("@map");var k=L.scale[0]/100;function P(x,y){return [thisComp.width/2+(x-0.5)*L.width*k,thisComp.height/2+(y-0.5)*L.height*k];}';
 var r=comp.layers.addShape();r.name="route";var g=r.property("Contents").addProperty("ADBE Vector Group").property("Contents");var path=g.addProperty("ADBE Vector Shape - Group").property("Path");
 path.expression=sp+'var a=P(d.from_x,d.from_y),b=P(d.to_x,d.to_y);var dx=(b[0]-a[0])/3;createPath([a,b],[[0,0],[-dx,-220]],[[dx,-220],[0,0]],false)';
 var st=g.addProperty("ADBE Vector Graphic - Stroke");st.property("Color").setValue(ACCENT);st.property("Stroke Width").setValue(8);st.property("Line Cap").setValue(2);
 r.property("Anchor Point").setValue([0,0]);r.property("Position").setValue([0,0]);
 var tp=r.property("Contents").addProperty("ADBE Vector Filter - Trim");tp.property("End").setValueAtTime(0.6,0);tp.property("End").setValueAtTime(2.0,100);ease(tp.property("End"));
 var ends=[["from",0.4],["to",1.9]];for(var i=0;i<2;i++){var key=ends[i][0],t0=ends[i][1];
  var dot=comp.layers.addShape();dot.name=key+" dot";var dg=dot.property("Contents").addProperty("ADBE Vector Group").property("Contents");dg.addProperty("ADBE Vector Shape - Ellipse").property("Size").setValue([34,34]);dg.addProperty("ADBE Vector Graphic - Fill").property("Color").setValue(ACCENT);
  dot.property("Position").expression=sp+'P(d.'+key+'_x,d.'+key+'_y)';var sc=dot.property("Scale");sc.setValueAtTime(t0,[0,0]);sc.setValueAtTime(t0+0.3,[100,100]);ease(sc);
  var lb=text(comp,key,key,44,WHITE,"PingFangSC-Semibold",0,400);lb.property("Position").expression=sp+'var p=P(d.'+key+'_x,d.'+key+'_y);[p[0],p[1]-60]';var o=lb.property("Opacity");o.setValueAtTime(t0+0.1,0);o.setValueAtTime(t0+0.4,100);}
 var t=text(comp,"title","title",76,WHITE,"PingFangSC-Semibold",300,960);rise(t,0.15);bar(comp,380,0.5);}

function chipText(comp,field,size,y,right){var l=text(comp,field,field,size,WHITE,"PingFangSC-Semibold",y,600);
 if(right){l.property("Position").setValue([W-70,y]);l.property("Anchor Point").expression='var r=sourceRectAtTime(time,false);[r.left+r.width,r.top+r.height/2]';}
 return l;}
function cornerTag(comp){
 var tb=box(comp,"tag box",10,64,180,[0,0,0],null);tb.property("Contents").property(1).property("Contents").property(1).property("Roundness").setValue(32);
 tb.property("Contents").property(1).property("Contents").property(1).property("Size").expression='var l=thisComp.layer("@tag");var r=l.sourceRectAtTime(time,false);[r.width+44,64]';
 tb.property("Position").expression='var l=thisComp.layer("@tag");var r=l.sourceRectAtTime(time,false);['+(W-70)+'-r.width/2,180]';tb.property("Opacity").setValue(55);hideEmpty(tb,"tag");
 var t=chipText(comp,"tag",30,180,true);hideEmpty(t,"tag");}
function photoPush(comp,folder){
 var img=app.project.importFile(new ImportOptions(new File(folder.fsName+"/image.png")));var m=comp.layers.add(img);m.name="@image";
 m.property("Scale").expression='var k=Math.max(thisComp.width/width,thisComp.height/height)*100*(1+0.08*Math.min(time/6,1));[k,k]';
 var shade=comp.layers.addSolid([0,0,0],"lower shade",W,H,1);var sm=shade.property("ADBE Mask Parade").addProperty("ADBE Mask Atom");var sh=new Shape();
 sh.vertices=[[0,1380],[W,1380],[W,H],[0,H]];sh.closed=true;sm.property("ADBE Mask Shape").setValue(sh);sm.property("ADBE Mask Feather").setValue([0,260]);shade.property("Opacity").setValue(70);
 var c=text(comp,"caption","caption",56,WHITE,"PingFangSC-Semibold",1600,960);rise(c,0.4,20);hideEmpty(c,"caption");
 var tb=box(comp,"tag box",10,64,180,[0,0,0],null);tb.property("Contents").property(1).property("Contents").property(1).property("Roundness").setValue(32);
 tb.property("Contents").property(1).property("Contents").property(1).property("Size").expression='var l=thisComp.layer("@tag");var r=l.sourceRectAtTime(time,false);[r.width+44,64]';
 tb.property("Position").expression='var l=thisComp.layer("@tag");var r=l.sourceRectAtTime(time,false);['+(W-70)+'-r.width/2,180]';tb.property("Opacity").setValue(55);hideEmpty(tb,"tag");
 var t=chipText(comp,"tag",30,180,true);hideEmpty(t,"tag");}
function comparePair(comp,folder){
 var xs=[290,790],sides=["left","right"];
 for(var i=0;i<2;i++){var side=sides[i],x=xs[i];
  var frame=box(comp,side+" frame",460,640,860,CHIP,ACCENT);frame.property("Position").setValue([x,860]);var fo=frame.property("Opacity");fo.setValueAtTime(0.2+i*0.3,0);fo.setValueAtTime(0.5+i*0.3,100);
  var matte=box(comp,side+" matte",452,632,860,WHITE,null);matte.property("Position").setValue([x,860]);
  var img=app.project.importFile(new ImportOptions(new File(folder.fsName+"/"+side+".png")));var m=comp.layers.add(img);m.name="@"+side;m.moveAfter(matte);
  m.property("Position").setValue([x,860]);m.property("Scale").expression='var k=Math.max(452/width,632/height)*100;[k,k]';m.setTrackMatte(matte,TrackMatteType.ALPHA);
  m.property("Opacity").expression=D+'(d._images&&d._images.indexOf("'+side+'")>=0)?value:0';
  var big=text(comp,side+"_label",side+"_label",72,WHITE,"PingFangSC-Semibold",860,400);big.property("Position").setValue([x,860]);
  big.property("Opacity").expression=D+'(d._images&&d._images.indexOf("'+side+'")>=0)?0:value';
  var lb=text(comp,side+" label",side+"_label",48,ACCENT,"PingFangSC-Semibold",1250,440);lb.name="@"+side+"_label caption";lb.property("Position").setValue([x,1250]);rise(lb,0.5+i*0.3,16);
  lb.property("Opacity").expression=D+'(d._images&&d._images.indexOf("'+side+'")>=0)?value:0';}
 var vs=text(comp,"≈","vs",64,GREY,"PingFangSC-Semibold",860,200);vs.property("Source Text").expression='"≈"';pop(vs,0.9);
 var n=text(comp,"note","note",52,WHITE,"PingFangSC-Semibold",1420,960);rise(n,1.2,20);hideEmpty(n,"note");
 cornerTag(comp);}

// ---- batch 1 (change ae-template-library-batch): heavy type, flat accents, white blocks; overlays render with alpha ----
var HV="SourceHanSansSC-Heavy",H_=1920,BOLD="SourceHanSansSC-Bold",MED="SourceHanSansSC-Medium",REG="SourceHanSansSC-Regular",SONG="STSongti-SC-Black";
var INK=[0.07,0.07,0.09],PAPER=[1,1,1],MUTE=[0.45,0.47,0.51],LINE=[0.86,0.87,0.89],CANVAS=[0.965,0.965,0.97],CHAR=[0.11,0.11,0.125];
var RED=[0.9,0.29,0.17],TEAL=[0.05,0.62,0.6],BLUE=[0.1,0.42,0.86],VIOLET=[0.45,0.37,0.96],YELLOW=[1,0.84,0.22],ORANGE=[0.96,0.47,0.1];
var MX=84;
function alphaQueue(comp){var rq=app.project.renderQueue.items.add(comp);var om=rq.outputModule(1);var ts=om.templates,pick=null,i;
 for(i=0;i<ts.length;i++){if(/alpha/i.test(ts[i])&&/(高品质|High Quality)/i.test(ts[i])){pick=ts[i];break;}}
 if(!pick)throw new Error("no alpha output module template");om.applyTemplate(pick);}
function grp(s){return s.property("Contents").property(1).property("Contents");}
function softShadow(l,op,soft,dist){var fx=l.property("ADBE Effect Parade").addProperty("ADBE Drop Shadow");fx.property("ADBE Drop Shadow-0002").setValue(op||60);fx.property("ADBE Drop Shadow-0003").setValue(180);fx.property("ADBE Drop Shadow-0004").setValue(dist||10);fx.property("ADBE Drop Shadow-0005").setValue(soft||40);}
function hold(p,t,a,b){p.setValueAtTime(t-0.001,a);p.setValueAtTime(t,b);p.setInterpolationTypeAtKey(1,KeyframeInterpolationType.HOLD);}
function bez(p,inf,outf){for(var k=1;k<=p.numKeys;k++){var n=(p.propertyValueType==PropertyValueType.TwoD_SPATIAL||p.propertyValueType==PropertyValueType.ThreeD_SPATIAL)?1:(p.value instanceof Array?p.value.length:1);var a=[],b=[];for(var i=0;i<n;i++){a.push(new KeyframeEase(0,inf||75));b.push(new KeyframeEase(0,outf||75));}p.setTemporalEaseAtKey(k,a,b);}}
function tx(comp,field,size,color,font,x,y,maxw,align,track){var l=comp.layers.addText(field);l.name="@"+field;var p=l.property("Source Text");var t=p.value;t.resetCharStyle();t.font=font;t.fontSize=size;t.fillColor=color;t.applyFill=true;t.applyStroke=false;t.tracking=track||0;
 t.justification=align=="left"?ParagraphJustification.LEFT_JUSTIFY:ParagraphJustification.CENTER_JUSTIFY;p.setValue(t);p.expression=D+'String(d["'+field+'"]||"")';
 l.property("Anchor Point").expression=align=="left"?'var r=sourceRectAtTime(time,false);[r.left,r.top+r.height/2]':CENTER;l.property("Position").setValue([x,y]);l.property("Scale").expression=fit(maxw||900);return l;}
function accent(l,field,accField,color,n){var an=l.property("ADBE Text Properties").property("ADBE Text Animators").addProperty("ADBE Text Animator");an.property("ADBE Text Animator Properties").addProperty("ADBE Text Fill Color").setValue(color);
 var sel=an.property("ADBE Text Selectors").addProperty("ADBE Text Selector");sel.property("ADBE Text Range Advanced").property("ADBE Text Range Units").setValue(2);
 var pre=D+'var s=String(d["'+field+'"]||"");var a=String(d["'+accField+'"]||"").split(/[,，]/)['+(n||0)+']||"";var i=a?s.indexOf(a):-1;';
 sel.property("ADBE Text Index Start").expression=pre+'i<0?0:i';sel.property("ADBE Text Index End").expression=pre+'i<0?0:i+a.length';}
// Union of the named layers' text boxes in comp space, so blocks hug whatever text the data supplies.
function unionExpr(names,pad){return 'var N='+JSON.stringify(names)+';var x0=1e9,y0=1e9,x1=-1e9,y1=-1e9;for(var i=0;i<N.length;i++){var L=thisComp.layer(N[i]);if(L.opacity==0&&L.opacity.numKeys==0)continue;var r=L.sourceRectAtTime(time,false);if(r.width<1)continue;var a=L.toComp([r.left,r.top]),b=L.toComp([r.left+r.width,r.top+r.height]);x0=Math.min(x0,a[0],b[0]);y0=Math.min(y0,a[1],b[1]);x1=Math.max(x1,a[0],b[0]);y1=Math.max(y1,a[1],b[1]);}if(x1<x0){x0=x1=-5000;y0=y1=-5000;}var P=['+pad[0]+','+pad[1]+'];';}
function block(comp,name,names,pad,fill,stroke,round){var s=comp.layers.addShape();s.name=name;var g=s.property("Contents").addProperty("ADBE Vector Group").property("Contents");g.addProperty("ADBE Vector Shape - Rect");
 if(fill)g.addProperty("ADBE Vector Graphic - Fill").property("Color").setValue(fill);if(stroke){var st=g.addProperty("ADBE Vector Graphic - Stroke");st.property("Color").setValue(stroke[0]);st.property("Stroke Width").setValue(stroke[1]);}
 var r=grp(s).property("ADBE Vector Shape - Rect");var u=unionExpr(names,pad);r.property("Size").expression=u+'[x1-x0+2*P[0],y1-y0+2*P[1]]';r.property("Position").expression=u+'[(x0+x1)/2,(y0+y1)/2]';r.property("Roundness").setValue(round||0);
 s.property("Anchor Point").setValue([0,0]);s.property("Position").setValue([0,0]);return s;}
function grow(s,t0,t1,from){var sc=s.property("Scale");sc.setValueAtTime(t0,from||[0,100]);sc.setValueAtTime(t1,[100,100]);bez(sc,80,60);}
function originAt(s,names,pad,side){var u=unionExpr(names,pad);var e=side=="left"?'[x0-P[0],(y0+y1)/2]':'[(x0+x1)/2,(y0+y1)/2]';s.property("Anchor Point").expression=u+e;s.property("Position").expression=u+e;}
function fade(l,t0,t1){var o=l.property("Opacity");o.setValueAtTime(t0,0);o.setValueAtTime(t1,100);}
function lift(l,t0,dy,dur){var p=l.property("Position");var v=p.value;p.setValueAtTime(t0,[v[0],v[1]+dy]);p.setValueAtTime(t0+(dur||0.45),v);bez(p,85,40);fade(l,t0,t0+(dur||0.45)*0.6);}
function exitAll(comp){var a=comp.layers.addSolid([1,1,1],"exit",W,H_,1);a.adjustmentLayer=true;var fx=a.property("ADBE Effect Parade").addProperty("ADBE Geometry2");
 fx.property("ADBE Geometry2-0008").expression=D+'var e=(d._duration_ms||4000)/1000;linear(time,e-0.35,e-0.05,100,0)';
 fx.property("ADBE Geometry2-0002").expression=D+'var e=(d._duration_ms||4000)/1000;value+[0,linear(time,e-0.35,e-0.05,0,24)]';}
function lineShape(comp,name,color,sw){var s=comp.layers.addShape();s.name=name;var g=s.property("Contents").addProperty("ADBE Vector Group").property("Contents");g.addProperty("ADBE Vector Shape - Group");
 var st=g.addProperty("ADBE Vector Graphic - Stroke");st.property("Color").setValue(color);st.property("Stroke Width").setValue(sw);st.property("Line Cap").setValue(2);st.property("Line Join").setValue(2);s.property("Anchor Point").setValue([0,0]);s.property("Position").setValue([0,0]);
 return [s,grp(s).property("ADBE Vector Shape - Group").property("Path")];}
function trimIn(s,t0,t1){var tp=s.property("Contents").addProperty("ADBE Vector Filter - Trim");var e=tp.property("End");e.setValueAtTime(t0,0);e.setValueAtTime(t1,100);bez(e,80,40);return tp;}
function canvas(comp,color){var b=comp.layers.addSolid(color,"canvas",W,H_,1);return b;}
function card(comp,folder,file,name,boxW,boxH,cx,cy){var it=app.project.importFile(new ImportOptions(new File(folder.fsName+"/"+file)));var m=comp.layers.add(it);m.name=name;
 m.property("Scale").expression='var k=Math.min('+boxW+'/width,'+boxH+'/height)*100;[k,k]';m.property("Position").setValue([cx,cy]);
 var f=comp.layers.addShape();f.name=name+" frame";var g=f.property("Contents").addProperty("ADBE Vector Group").property("Contents");g.addProperty("ADBE Vector Shape - Rect");var st=g.addProperty("ADBE Vector Graphic - Stroke");st.property("Color").setValue(LINE);st.property("Stroke Width").setValue(2);
 var r=grp(f).property("ADBE Vector Shape - Rect");r.property("Size").expression='var L=thisComp.layer("'+name+'");var k=L.scale[0]/100;[L.width*k,L.height*k]';r.property("Roundness").setValue(18);
 f.property("Position").expression='thisComp.layer("'+name+'").position';softShadow(m,40,50,14);m.moveBefore(f);f.moveBefore(m);return m;}
function PL(name){return D+'var L=thisComp.layer("'+name+'");var k=L.scale[0]/100;function P(x,y){return [L.position[0]+(x-0.5)*L.width*k,L.position[1]+(y-0.5)*L.height*k];}';}
function dot(comp,name,size,color){var s=comp.layers.addShape();s.name=name;var g=s.property("Contents").addProperty("ADBE Vector Group").property("Contents");g.addProperty("ADBE Vector Shape - Ellipse").property("Size").setValue([size,size]);g.addProperty("ADBE Vector Graphic - Fill").property("Color").setValue(color);return s;}
function ring(comp,name,color,sw){var s=comp.layers.addShape();s.name=name;var g=s.property("Contents").addProperty("ADBE Vector Group").property("Contents");g.addProperty("ADBE Vector Shape - Ellipse");var st=g.addProperty("ADBE Vector Graphic - Stroke");st.property("Color").setValue(color);st.property("Stroke Width").setValue(sw);st.property("Line Cap").setValue(2);return [s,grp(s).property("ADBE Vector Shape - Ellipse")];}

// Hidden twin with keyed opacity: blocks size to it, so a word that appears later never makes its card jump.
function ghost(comp,field,size,font,x,y,maxw,align){var g=tx(comp,field,size,INK,font,x,y,maxw,align);g.name="@"+field+" box";var o=g.property("Opacity");o.setValueAtTime(0,0);o.setValueAtTime(1,0);return g;}
function keywordContrast(comp){
 // The sentence comes in phrase by phrase at the speaker's breath points ("|" in the text); optional beats are the seconds each phrase starts.
 var BT='var raw=String(d.sentence||""),seg=raw.split("|"),bt=String(d.beats||"").split(/[,，]/),B=[];for(var i=0;i<seg.length;i++){var v=parseFloat(bt[i]);B.push(isNaN(v)?0.3+i*0.45:v);}var tw=B[B.length-1]+0.45;';
 var s=tx(comp,"sentence",64,INK,BOLD,W/2,1130,692);srcE(s,'String(d.sentence||"").replace(/\\|/g,"")');
 var an=s.property("ADBE Text Properties").property("ADBE Text Animators").addProperty("ADBE Text Animator");var pr=an.property("ADBE Text Animator Properties");pr.addProperty("ADBE Text Opacity").setValue(0);pr.addProperty("ADBE Text Position 3D").setValue([0,18,0]);
 var sel=an.property("ADBE Text Selectors").addProperty("ADBE Text Expressible Selector");
 sel.property("ADBE Text Expressible Amount").expression=D+BT+'var n=0,b=B[0];for(var i=0;i<seg.length;i++){if(textIndex<=n+seg[i].length){b=B[i];break;}n+=seg[i].length;}var a=1-ease(time,b,b+0.22,0,1);selectorValue*a';
 var w=tx(comp,"word",190,BLUE,SONG,W/2,1300,692);var gw=ghost(comp,"word",190,SONG,W/2,1300,692);
 w.property("Opacity").expression=D+BT+'linear(time,tw,tw+0.2,0,100)';w.property("Position").expression=D+BT+'[value[0],value[1]+30*(1-ease(time,tw,tw+0.42,0,1))]';
 w.property("Scale").expression=D+BT+'var r=sourceRectAtTime(time,false);var f=r.width>692?692/r.width:1;var k=linear(ease(time,tw,tw+0.38,0,1),0,1,1.12,1);[100*f*k,100*f*k]';
 var N=["@sentence","@word box"];var b=block(comp,"card",N,[64,52],PAPER,null,28);b.moveToEnd();softShadow(b,45,60,16);originAt(b,N,[64,52]);grow(b,0.1,0.4,[94,94]);fade(b,0.1,0.3);exitAll(comp);}
function keywordSlab(comp){
 var l1=tx(comp,"line1",118,INK,HV,MX+44,1110,740,"left");var w=tx(comp,"word",132,PAPER,HV,MX+44,1278,740,"left");
 var b1=block(comp,"line1 block",["@line1"],[44,22],PAPER,null,6);b1.moveToEnd();softShadow(b1,40,50,12);originAt(b1,["@line1"],[44,22],"left");grow(b1,0.3,0.55);
 var sl=block(comp,"slab",["@word"],[44,24],RED,null,4);sl.moveBefore(w);sl.moveAfter(w);originAt(sl,["@word"],[44,24],"left");sl.property("Rotation").setValue(-2.5);grow(sl,0.62,0.86);
 w.property("Rotation").setValue(-2.5);hold(l1.property("Opacity"),0.5,0,100);hold(w.property("Opacity"),0.86,0,100);var sc=w.property("Scale");sc.setValueAtTime(0.86,[112,112]);sc.setValueAtTime(1.03,[100,100]);bez(sc,85,40);exitAll(comp);}
function impactLine(comp){
 var s=tx(comp,"sentence",112,INK,HV,W/2,1160,692);accent(s,"sentence","accent",ORANGE,0);var u=tx(comp,"sub",40,MUTE,MED,W/2,1280,692);
 var b=block(comp,"panel",["@sentence","@sub"],[70,64],PAPER,null,24);b.moveToEnd();softShadow(b,45,60,16);originAt(b,["@sentence","@sub"],[70,64]);grow(b,0.2,0.5,[96,96]);fade(b,0.2,0.4);
 var sc=s.property("Scale");sc.setValueAtTime(0.45,[108,108]);sc.setValueAtTime(0.65,[100,100]);bez(sc,90,40);fade(s,0.45,0.52);lift(u,0.9,12,0.4);
 var cs=[[-1,-1],[1,-1],[1,1],[-1,1]];var U=unionExpr(["@sentence","@sub"],[70,64]);
 for(var i=0;i<4;i++){var c=lineShape(comp,"corner "+(i+1),ORANGE,6);var sx=cs[i][0],sy=cs[i][1];
  c[1].expression=U+'var cx='+(sx<0?'x0-P[0]-22':'x1+P[0]+22')+',cy='+(sy<0?'y0-P[1]-22':'y1+P[1]+22')+';var o=linear(time,0.45,0.75,14,0);cx+='+sx+'*o;cy+='+sy+'*o;createPath([[cx,cy-('+sy+')*48],[cx,cy],[cx-('+sx+')*48,cy]],[],[],false)';fade(c[0],0.45,0.6);}
 exitAll(comp);}
function outlineBoxTitle(comp){
 var t=tx(comp,"title",104,INK,HV,MX+60,1100,720,"left");var su=tx(comp,"sub",60,PAPER,HV,MX+60,1260,700,"left");
 var fs=block(comp,"frame stroke",["@title"],[52,34],null,[VIOLET,7],22);fs.moveToEnd();trimIn(fs,0.25,0.85);
 var f=block(comp,"frame fill",["@title"],[52,34],PAPER,null,22);f.moveToEnd();softShadow(f,40,50,12);fade(f,0.25,0.5);
 var chip=block(comp,"chip",["@sub"],[36,14],VIOLET,null,12);chip.moveBefore(su);chip.moveAfter(su);originAt(chip,["@sub"],[36,14],"left");grow(chip,1.0,1.25);chip.property("Opacity").expression=D+'d.sub?value:0';
 lift(t,0.6,14,0.4);hold(su.property("Opacity"),1.25,0,100);
 for(var i=0;i<3;i++){var c=lineShape(comp,"chevron "+(i+1),VIOLET,6);c[1].expression=unionExpr(["@sub"],[36,14])+'var x=x0-P[0]+'+(i*40+10)+',y=y1+P[1]+56;createPath([[x,y-16],[x+14,y],[x,y+16]],[],[],false)';
  c[0].property("Opacity").expression=D+'d.sub?(time<'+(1.35+i*0.1)+'?0:(time<'+(1.6+i*0.1)+'?100:60)):0';}
 exitAll(comp);}
function splitRiseTitle(comp){
 // Characters are pulled up from below the underline, overshoot, and the line gives one small shake once all have landed.
 var l=tx(comp,"title",112,INK,HV,W/2,1160,692);var su=tx(comp,"sub",38,MUTE,MED,W/2,1300,692,null,40);
 var b=block(comp,"panel",["@title","@sub"],[64,60],PAPER,null,24);b.moveToEnd();softShadow(b,45,60,16);originAt(b,["@title","@sub"],[64,60]);grow(b,0.1,0.4,[96,96]);fade(b,0.1,0.3);
 var mk=l.property("ADBE Mask Parade").addProperty("ADBE Mask Atom");mk.property("ADBE Mask Shape").expression='var r=sourceRectAtTime(5,false);var y=r.top+r.height+8;createPath([[r.left-400,r.top-800],[r.left+r.width+400,r.top-800],[r.left+r.width+400,y],[r.left-400,y]],[],[],true)';
 var an=l.property("ADBE Text Properties").property("ADBE Text Animators").addProperty("ADBE Text Animator");an.property("ADBE Text Animator Properties").addProperty("ADBE Text Position 3D").setValue([0,150,0]);
 var sel=an.property("ADBE Text Selectors").addProperty("ADBE Text Expressible Selector");
 sel.property("ADBE Text Expressible Amount").expression='var p=clamp((time-(0.4+(textIndex-1)*0.06))/0.5,0,1);var e=1-Math.pow(1-p,3);var a=(1-e)-0.24*Math.sin(p*Math.PI)*(p<1?1:0);selectorValue*a';
 l.property("Rotation").expression='var n=text.sourceText.length;var u=time-(0.4+(n-1)*0.06+0.5);(u>0&&u<0.45)?2.4*Math.sin(u*42)*Math.exp(-u*8):0';
 var ul=lineShape(comp,"underline",INK,5);ul[1].expression='var L=thisComp.layer("@title");var r=L.sourceRectAtTime(5,false);var k=L.scale[0]/100,p=L.position;var w=r.width*k/2,y=p[1]+(r.top+r.height)*k-L.anchorPoint[1]*k+18;createPath([[p[0]-w,y],[p[0]+w,y]],[],[],false)';trimIn(ul[0],0.15,0.45);
 lift(su,1.3,10,0.4);exitAll(comp);}
function quoteCard(comp){
 canvas(comp,CHAR);
 for(var i=0;i<4;i++){var f="line"+(i+1);var l=tx(comp,f,88,PAPER,HV,W/2,700+i*150,692);accent(l,f,"accent",YELLOW,0);accent(l,f,"accent",YELLOW,1);lift(l,0.3+i*0.16,26,0.45);
  l.property("Opacity").expression=D+'d["'+f+'"]?value:0';}
 var s=tx(comp,"source",30,[0.55,0.56,0.6],MED,W/2,1400,692,null,120);lift(s,1.1,8,0.4);s.property("Opacity").expression=D+'d.source?value:0';}
function quoteHold(comp){
 for(var i=0;i<3;i++){var f="line"+(i+1);var l=tx(comp,f,68,INK,BOLD,MX+64,1050+i*104,740,"left");lift(l,0.35+i*0.17,14,0.4);}
 var b=block(comp,"panel",["@line1","@line2","@line3"],[64,58],PAPER,null,24);b.moveToEnd();softShadow(b,45,60,16);originAt(b,["@line1","@line2","@line3"],[64,58]);grow(b,0.15,0.45,[96,96]);fade(b,0.15,0.35);
 var hl=block(comp,"highlight",["@line3"],[14,6],YELLOW,null,6);var l3=comp.layer("@line3");hl.moveAfter(l3);
 originAt(hl,["@line3"],[14,6],"left");grow(hl,1.55,1.8);var sc=l3.property("Scale");sc.setValueAtTime(1.8,[104,104]);sc.setValueAtTime(1.98,[100,100]);bez(sc,85,40);exitAll(comp);}
function pairBlocks(comp){
 var rows=[["top",1100,TEAL,PAPER,null,0.4],["bottom",1252,PAPER,INK,[LINE,2],0.52]];
 for(var i=0;i<2;i++){var f=rows[i][0],y=rows[i][1],t0=rows[i][5];var l=tx(comp,f,96,rows[i][3],HV,MX+40,y,720,"left");
  var b=block(comp,f+" block",["@"+f],[40,20],rows[i][2],rows[i][4],6);b.moveBefore(l);b.moveAfter(l);originAt(b,["@"+f],[40,20],"left");grow(b,t0,t0+0.26);if(i==1)softShadow(b,35,40,10);
  var w=l.property("ADBE Effect Parade").addProperty("ADBE Linear Wipe");w.property("ADBE Linear Wipe-0002").setValue(270);var c=w.property("ADBE Linear Wipe-0001");c.setValueAtTime(t0+0.067,100);c.setValueAtTime(t0+0.327,0);bez(c,80,50);}
 exitAll(comp);}
function ringMark(comp,folder){
 canvas(comp,CANVAS);var m=card(comp,folder,"image.png","@image",920,1000,W/2,800);
 var e=ring(comp,"ring",ORANGE,7);e[1].property("Size").expression=PL("@image")+'[Math.max(d.w*L.width*k*1.2,120),Math.max(d.h*L.height*k*1.7,80)]';
 e[0].property("Position").expression=PL("@image")+'P(d.x,d.y)';e[0].property("Rotation").setValue(-5);var tp=trimIn(e[0],0.45,0.95);tp.property("Offset").setValue(-40);
 var lb=tx(comp,"label",64,INK,HV,W/2,1400,692);lift(lb,1.0,16,0.4);lb.property("Opacity").expression=D+'d.label?value:0';accent(lb,"label","accent",ORANGE,0);}
function calloutLabel(comp,folder){
 canvas(comp,CANVAS);var m=card(comp,folder,"image.png","@image",760,1100,W/2,860);
 for(var i=1;i<=3;i++){var px="p"+i+"_x",py="p"+i+"_y",pt="p"+i+"_text",t0=0.5+(i-1)*0.55;var A=PL("@image")+'var a=P(d.'+px+',d.'+py+');var s=d.'+px+'<0.5?-1:1;var c=[s<0?90:846,a[1]-60];var b=[a[0]+s*Math.min(80,Math.abs(c[0]-a[0])/3),c[1]];';
  var dt=dot(comp,"dot "+i,22,RED);dt.property("Position").expression=A+'a';var ds=dt.property("Scale");ds.setValueAtTime(t0,[0,0]);ds.setValueAtTime(t0+0.2,[100,100]);bez(ds,85,40);dt.property("Opacity").expression=D+'d["'+pt+'"]?value:0';
  var hl=ring(comp,"halo "+i,RED,3);hl[1].property("Size").setValue([22,22]);hl[0].property("Position").expression=A+'a';var hs=hl[0].property("Scale");hs.setValueAtTime(t0+0.1,[100,100]);hs.setValueAtTime(t0+0.55,[300,300]);hl[0].property("Opacity").expression=D+'d["'+pt+'"]?linear(time,'+(t0+0.1)+','+(t0+0.55)+',100,0):0';
  var ln=lineShape(comp,"leader "+i,RED,3);ln[1].expression=A+'createPath([a,b,c],[],[],false)';trimIn(ln[0],t0+0.2,t0+0.55);ln[0].property("Opacity").expression=D+'d["'+pt+'"]?value:0';
  var lb=tx(comp,pt,44,INK,BOLD,0,0,320);lb.property("Position").expression=A+'var r=sourceRectAtTime(time,false);var w=r.width*scale[0]/100;[s<0?c[0]+w/2:c[0]-w/2,c[1]-58]';
  var bx=block(comp,pt+" card",["@"+pt],[24,16],PAPER,[LINE,2],12);bx.moveBefore(lb);bx.moveAfter(lb);softShadow(bx,30,30,8);
  fade(lb,t0+0.5,t0+0.7);bx.property("Opacity").expression=D+'d["'+pt+'"]?Math.min(1,Math.max(0,(time-'+(t0+0.5)+')/0.2))*100:0';lb.property("Opacity").expression=D+'d["'+pt+'"]?value:0';}}
function magnifier(comp,folder){
 canvas(comp,CANVAS);var m=card(comp,folder,"image.png","@image",920,1180,W/2,860);
 var dim=comp.layers.addSolid([0.2,0.2,0.22],"dim",W,H_,1);dim.property("Opacity").setValueAtTime(0.45,0);dim.property("Opacity").setValueAtTime(0.75,22);
 var Q=PL("@image")+'var p=P(d.x,d.y);var R=(d.r||0.12)*L.width*k*1.8;var c=[Math.min(Math.max(p[0]+(d.x<0.5?300:-300),R+40),1040-R),p[1]+(d.y<0.55?R+160:-(R+160))];';
 var src=comp.layers.addShape();src.name="source box";var sg=src.property("Contents").addProperty("ADBE Vector Group").property("Contents");sg.addProperty("ADBE Vector Shape - Rect");var ss=sg.addProperty("ADBE Vector Graphic - Stroke");ss.property("Color").setValue(RED);ss.property("Stroke Width").setValue(3);
 var sr=grp(src).property("ADBE Vector Shape - Rect");sr.property("Size").expression=Q+'[R/1.8*2,R/1.8*1.1]';sr.property("Roundness").setValue(8);src.property("Position").expression=Q+'p';fade(src,0.45,0.6);
 var ln=lineShape(comp,"connector",RED,2);ln[1].expression=Q+'var v=[c[0]-p[0],c[1]-p[1]];var n=Math.sqrt(v[0]*v[0]+v[1]*v[1]);var u=[v[0]/n,v[1]/n];createPath([[p[0]+u[0]*R/1.8,p[1]+u[1]*R/1.8*0.55],[c[0]-u[0]*R,c[1]-u[1]*R]],[],[],false)';trimIn(ln[0],0.75,1.0);
 var lens=dot(comp,"lens",10,PAPER);grp(lens).property("ADBE Vector Shape - Ellipse").property("Size").expression=Q+'[R*2,R*2]';lens.property("Position").expression=Q+'c';var ls=lens.property("Scale");ls.setValueAtTime(0.45,[0,0]);ls.setValueAtTime(0.75,[100,100]);bez(ls,85,40);
 var z=comp.layers.add(m.source);z.name="@image zoom";z.moveAfter(lens);z.property("Scale").expression=PL("@image")+'[L.scale[0]*1.8,L.scale[1]*1.8]';z.property("Position").expression=Q+'[c[0]-(p[0]-L.position[0])*1.8,c[1]-(p[1]-L.position[1])*1.8]';z.setTrackMatte(lens,TrackMatteType.ALPHA);
 var rg=ring(comp,"lens ring",INK,4);rg[1].property("Size").expression=Q+'[R*2,R*2]';rg[0].property("Position").expression=Q+'c';var rs=rg[0].property("Scale");rs.setValueAtTime(0.45,[0,0]);rs.setValueAtTime(0.75,[100,100]);bez(rs,85,40);softShadow(rg[0],40,40,10);}
var RECTS=D+'var L=thisComp.layer("@image");var k=L.scale[0]/100;var rs=String(d.regions||"").split(";");var R=[];for(var i=0;i<rs.length;i++){var v=rs[i].split(",");if(v.length==4)R.push([+v[0],+v[1],+v[2],+v[3]]);}'+
 'var n=Math.max(R.length,1);var e=(d._duration_ms||6000)/1000;var seg=(e-1.2)/n;var j=Math.min(Math.floor(Math.max(time-0.45,0)/seg),n-1);var a=R[Math.max(j-1,0)]||[0.5,0.5,0.4,0.2],b=R[j]||a;var f=j>0?ease(time-0.45-j*seg,0,0.25,0,1):1;'+
 'var q=[a[0]+(b[0]-a[0])*f,a[1]+(b[1]-a[1])*f,a[2]+(b[2]-a[2])*f,a[3]+(b[3]-a[3])*f];var cx=L.position[0]+(q[0]-0.5)*L.width*k,cy=L.position[1]+(q[1]-0.5)*L.height*k,hw=q[2]*L.width*k/2,hh=q[3]*L.height*k/2;'+
 'var pts=[[cx-hw,cy-hh],[cx+hw,cy-hh],[cx+hw,cy+hh],[cx-hw,cy+hh]];';
function focusDim(comp,folder){
 // Outside the box turns grey rather than dark, so the content stays readable while the eye follows the frame.
 canvas(comp,CANVAS);var m=card(comp,folder,"image.png","@image",920,1180,W/2,860);
 var dim=comp.layers.addSolid([0.52,0.52,0.54],"grey out",W,H_,1);var mk=dim.property("ADBE Mask Parade").addProperty("ADBE Mask Atom");mk.inverted=true;mk.property("ADBE Mask Shape").expression=RECTS+'createPath(pts,[],[],true)';
 dim.property("Opacity").expression=D+'var e=(d._duration_ms||6000)/1000;Math.min(linear(time,0.45,0.75,0,62),linear(time,e-0.6,e-0.2,62,0))';
 var o=lineShape(comp,"focus outline",ORANGE,6);o[1].expression=RECTS+'createPath(pts,[],[],true)';o[0].property("Opacity").expression=D+'var e=(d._duration_ms||6000)/1000;Math.min(linear(time,0.45,0.75,0,100),linear(time,e-0.6,e-0.2,100,0))';}
function hostToChip(comp,folder){
 canvas(comp,CANVAS);var gimg=card(comp,folder,"graphic.png","@graphic",900,820,W/2,720);var gp=gimg.property("Position");gp.setValueAtTime(1.15,[W/2+600,720]);gp.setValueAtTime(1.65,[W/2,720]);bez(gp,90,40);fade(gimg,1.15,1.35);
 var gf=comp.layer("@graphic frame");gf.property("Opacity").expression='thisComp.layer("@graphic").opacity';
 // Scale is solved from the head-and-neck span, not fixed, so any source framing ends with the whole face plus neck inside the chip with room to spare.
 var SOLVE=D+'var e=d.chip_size||300,s0=Math.max(1080/width,1920/height),s1=e/((d.face_size||0.5)*height*1.25),t=ease(time,1.0,1.45,0,1),s=linear(t,0,1,s0,s1),C=['+MX+'+e/2+16,1300];';
 var FACE=PL("@host")+'var p=[L.position[0]+(d.face_x-0.5)*L.width*k,L.position[1]+(d.face_y-0.5)*L.height*k];';
 var mask=dot(comp,"chip mask",10,PAPER);var me=grp(mask).property("ADBE Vector Shape - Ellipse").property("Size");
 me.expression=D+'var e=d.chip_size||300;var s=linear(ease(time,1.0,1.45,0,1),0,1,4000,e);[s,s]';
 mask.property("Position").expression=FACE+'p';
 var it=app.project.importFile(new ImportOptions(new File(folder.fsName+"/host.png")));var h=comp.layers.add(it);h.name="@host";h.moveAfter(mask);
 h.property("Scale").expression=SOLVE+'[s*100,s*100]';
 // Lerping position and scale with the same t moves the face in a straight line onto the chip seat.
 h.property("Position").expression=SOLVE+'var bx=C[0]-(d.face_x-0.5)*width*s1,by=C[1]-(d.face_y-0.5)*height*s1;[540+(bx-540)*t,960+(by-960)*t]';
 h.setTrackMatte(mask,TrackMatteType.ALPHA);
 var bed=dot(comp,"chip bed",10,PAPER);bed.moveAfter(h);grp(bed).property("ADBE Vector Shape - Ellipse").property("Size").expression=D+'var e=d.chip_size||300;[e,e]';
 bed.property("Position").expression=FACE+'p';bed.property("Opacity").expression='linear(time,1.35,1.45,0,100)';
 var rg=ring(comp,"chip ring",PAPER,8);rg[1].property("Size").expression=D+'var e=(d.chip_size||300)+16;[e,e]';
 rg[0].property("Position").expression=FACE+'p';fade(rg[0],1.4,1.55);softShadow(rg[0],45,40,10);
 var c=tx(comp,"caption",56,INK,HV,MX+230,1300,540,"left");
 c.property("Position").expression=D+'var r=thisComp.layer("chip ring").position;var s=d.chip_size||300;[r[0]+s/2+52,r[1]]';
 c.property("Opacity").expression=D+'d.caption?linear(time,1.7,2.0,0,100):0';}
function hostParallel(comp,folder){
 // Still thumbnails wait in a row; each one grows out of its slot when its part of the narration starts and is fully back before the next one opens,
 // so the panel follows the spoken order. beats are "open-close" seconds per image; without a close it returns 0.7 s before the next opens.
 var G=D+'var I=d._images||[],H=["img1","img2","img3"],n=0;for(var q=0;q<3;q++)if(I.indexOf(H[q])>=0)n=q+1;n=Math.max(n,1);var e=(d._duration_ms||7000)/1000;var bt=String(d.beats||"").split(/[,，]/),B=[],K=[];for(var q=0;q<n;q++){var z=String(bt[q]||"").split("-"),v=parseFloat(z[0]),w=parseFloat(z[1]);B.push(isNaN(v)?1.2+q*2.2:v);K.push(isNaN(w)?null:w);}'+
  'function CL(i){if(K[i]!==null)return K[i];return i<n-1?B[i+1]-0.7:e-0.9;}function A(i){if(i>=n)return 0;var c=Math.max(CL(i),B[i]+0.45);return ease(time,B[i],B[i]+0.45,0,1)-ease(time,c,c+0.4,0,1);}function SL(i){return [540+(i-(n-1)/2)*300,380,272,190];}var BIG=[540,880,920,1180];'+
  'function GEO(i){var a=SL(i),b=BIG,t=A(i);return [a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t,a[2]+(b[2]-a[2])*t,a[3]+(b[3]-a[3])*t];}function OTH(i){var m=0;for(var j=0;j<n;j++)if(j!=i)m=Math.max(m,A(j));return 1-m;}';
 for(var i=0;i<3;i++){var t0=0.3+i*0.12,VIS=G+'var v=(I.indexOf("img'+(i+1)+'")>=0)?linear(time,'+t0+','+(t0+0.25)+',0,100):0;v*(A('+i+')>0.01?1:OTH('+i+'))';
  var bd=rect(comp,"img"+(i+1)+" border",10,10,PAPER,22,null);bd[0].property("Position").setValue([0,0]);softShadow(bd[0],55,50,14);
  bd[1].property("Size").expression=G+'var g=GEO('+i+');[g[2]+14,g[3]+14]';bd[1].property("Position").expression=G+'var g=GEO('+i+');[g[0],g[1]]';bd[0].property("Opacity").expression=VIS;
  var ph=photo(comp,folder,"img"+(i+1)+".png","@img"+(i+1),272,190,540,330,16);
  grp(ph[1]).property("ADBE Vector Shape - Rect").property("Size").expression=G+'var g=GEO('+i+');[g[2],g[3]]';ph[1].property("Position").expression=G+'var g=GEO('+i+');[g[0],g[1]]';
  ph[0].property("Position").expression=G+'var g=GEO('+i+');[g[0],g[1]]';ph[0].property("Opacity").expression=VIS;
  ph[0].property("Scale").expression=G+'var g=GEO('+i+');var push=1+0.1*clamp((time-B['+i+'])/3,0,1)*A('+i+');var k=Math.max(g[2]/width,g[3]/height)*100*push;[k,k]';
  var lb=tx(comp,"item"+(i+1),34,PAPER,HV,0,0,900,"left");lb.property("Position").expression=G+'var g=GEO('+i+'),t=A('+i+');[g[0]-g[2]/2+18+22*t,g[1]+g[3]/2-26-40*t]';
  lb.property("Scale").expression=G+'var t=A('+i+');var s=100*(1+1.1*t);[s,s]';lb.property("Opacity").expression=VIS;
  var lc=block(comp,"item"+(i+1)+" chip",["@item"+(i+1)],[14,8],INK,null,8);under(lc,lb);follow(lc,lb,0.6);}
 exitAll(comp);}
function namePlate(comp){
 var n=tx(comp,"name",72,INK,HV,MX+64,1170,700,"left");var t=tx(comp,"title",36,MUTE,MED,MX+64,1260,700,"left");
 var pl=block(comp,"plate",["@name","@title"],[40,30],PAPER,null,16);pl.moveToEnd();softShadow(pl,45,50,12);originAt(pl,["@name","@title"],[40,30],"left");grow(pl,0.3,0.6);
 var ab=lineShape(comp,"accent",BLUE,10);ab[1].expression=unionExpr(["@name","@title"],[40,30])+'createPath([[x0-P[0]+5,y0-P[1]+20],[x0-P[0]+5,y1+P[1]-20]],[],[],false)';trimIn(ab[0],0.3,0.55);
 lift(n,0.5,12,0.4);lift(t,0.65,10,0.4);t.property("Opacity").expression=D+'d.title?value:0';exitAll(comp);}
function nameChevron(comp){
 var n=tx(comp,"name",76,INK,HV,MX+40,1150,760,"left");var t=tx(comp,"title",40,PAPER,BOLD,MX+40,1252,640,"left");
 var nb=block(comp,"name block",["@name"],[40,18],PAPER,null,10);nb.moveToEnd();softShadow(nb,40,40,10);originAt(nb,["@name"],[40,18],"left");grow(nb,0.3,0.55);
 var np=n.property("Position");np.setValueAtTime(0.4,[MX+14,1150]);np.setValueAtTime(0.66,[MX+40,1150]);bez(np,85,40);fade(n,0.4,0.55);
 var cb=block(comp,"title chip",["@title"],[40,14],VIOLET,null,10);cb.moveBefore(t);cb.moveAfter(t);originAt(cb,["@title"],[40,14],"left");grow(cb,0.55,0.77);cb.property("Opacity").expression=D+'d.title?value:0';
 fade(t,0.84,0.9);t.property("Opacity").expression=D+'d.title?value:0';
 for(var i=0;i<3;i++){var c=lineShape(comp,"chevron "+(i+1),VIOLET,7);c[1].expression=unionExpr(["@title"],[40,14])+'var x=x1+P[0]+28+'+(i*34)+',y=(y0+y1)/2;createPath([[x,y-15],[x+14,y],[x,y+15]],[],[],false)';
  c[0].property("Opacity").expression=D+'d.title?(time<'+(0.9+i*0.1)+'?0:(time<'+(1.12+i*0.1)+'?100:55)):0';}
 exitAll(comp);}

// ---- batch 2: numbers, charts, steps, comparisons ----
var NUMF='function NUM(f){var a=String(d[f]===undefined?"":d[f]).split(/[,，]/),o=[];for(var i=0;i<a.length;i++){var z=parseFloat(a[i]);if(!isNaN(z))o.push(z);}return o;}';
var LISTF='function LST(f){var a=String(d[f]||"").split(/[,，]/),o=[];for(var i=0;i<a.length;i++){var z=a[i].replace(/^\\s+|\\s+$/g,"");if(z)o.push(z);}return o;}';
var FMT='function F(v,dp){var s=Math.abs(v).toFixed(dp||0).split(".");s[0]=s[0].replace(/\\B(?=(\\d{3})+(?!\\d))/g,",");return (v<0?"-":"")+s.join(".");}function DP(v){var t=String(v).split(".")[1];return t?Math.min(t.length,2):0;}';
function srcE(l,e){l.property("Source Text").expression=D+e;}
function rightAnchor(l){l.property("Anchor Point").expression='var r=sourceRectAtTime(time,false);[r.left+r.width,r.top+r.height/2]';}
function rect(comp,name,w,h,fill,round,stroke){var s=comp.layers.addShape();s.name=name;var g=s.property("Contents").addProperty("ADBE Vector Group").property("Contents");g.addProperty("ADBE Vector Shape - Rect");if(fill)g.addProperty("ADBE Vector Graphic - Fill");if(stroke)g.addProperty("ADBE Vector Graphic - Stroke");
 var c=grp(s);var r=c.property("ADBE Vector Shape - Rect");r.property("Size").setValue([w,h]);r.property("Roundness").setValue(round||0);if(fill)c.property("ADBE Vector Graphic - Fill").property("Color").setValue(fill);
 if(stroke){var st=c.property("ADBE Vector Graphic - Stroke");st.property("Color").setValue(stroke[0]);st.property("Stroke Width").setValue(stroke[1]);}return [s,r];}
function hollow(comp,name,size,color,sw){var s=comp.layers.addShape();s.name=name;var g=s.property("Contents").addProperty("ADBE Vector Group").property("Contents");g.addProperty("ADBE Vector Shape - Ellipse");g.addProperty("ADBE Vector Graphic - Fill");g.addProperty("ADBE Vector Graphic - Stroke");
 var c=grp(s);c.property("ADBE Vector Shape - Ellipse").property("Size").setValue([size,size]);c.property("ADBE Vector Graphic - Fill").property("Color").setValue(PAPER);var st=c.property("ADBE Vector Graphic - Stroke");st.property("Color").setValue(color);st.property("Stroke Width").setValue(sw);return s;}
function staticPath(prop,pts){var sh=new Shape();sh.vertices=pts;sh.closed=false;prop.setValue(sh);}
function filledPath(comp,name,color){var s=comp.layers.addShape();s.name=name;var g=s.property("Contents").addProperty("ADBE Vector Group").property("Contents");g.addProperty("ADBE Vector Shape - Group");g.addProperty("ADBE Vector Graphic - Fill");var c=grp(s);c.property("ADBE Vector Graphic - Fill").property("Color").setValue(color);
 s.property("Anchor Point").setValue([0,0]);s.property("Position").setValue([0,0]);return [s,c.property("ADBE Vector Shape - Group").property("Path")];}
function photo(comp,folder,file,name,w,h,cx,cy,round){var mt=rect(comp,name+" matte",w,h,PAPER,round||0,null);mt[0].property("Position").setValue([cx,cy]);
 var it=app.project.importFile(new ImportOptions(new File(folder.fsName+"/"+file)));var m=comp.layers.add(it);m.name=name;m.moveAfter(mt[0]);
 m.property("Scale").expression='var k=Math.max('+w+'/width,'+h+'/height)*100;[k,k]';m.property("Position").setValue([cx,cy]);m.setTrackMatte(mt[0],TrackMatteType.ALPHA);return [m,mt[0]];}
function rigNull(comp,name){var r=comp.layers.addNull();r.name=name;r.property("Anchor Point").setValue([0,0]);r.property("Position").setValue([0,0]);return r;}
function under(b,l){b.moveBefore(l);b.moveAfter(l);}
function follow(b,l,k){b.property("Opacity").expression='thisComp.layer("'+l.name+'").opacity'+(k?'*'+k:'');}
function dashes(s,dash,gap){var d=grp(s).property("ADBE Vector Graphic - Stroke").property("ADBE Vector Stroke Dashes");d.addProperty("ADBE Vector Stroke Dash 1").setValue(dash);d.addProperty("ADBE Vector Stroke Gap 1").setValue(gap);}

function valueSwap(comp){
 var s=tx(comp,"sentence",60,INK,BOLD,MX+60,900,730,"left");var o=tx(comp,"old",150,INK,HV,MX+60,1075,730,"left");var n=tx(comp,"new",190,RED,HV,MX+60,1258,730,"left");var t=tx(comp,"note",40,MUTE,MED,MX+60,1400,730,"left");
 var N=["@sentence","@old","@new","@note"];var b=block(comp,"panel",N,[60,52],PAPER,null,24);b.moveToEnd();softShadow(b,45,60,16);originAt(b,N,[60,52]);grow(b,0.15,0.45,[96,96]);fade(b,0.15,0.35);
 lift(s,0.3,14,0.4);lift(o,0.45,20,0.4);var oo=o.property("Opacity");oo.setValueAtTime(1.1,100);oo.setValueAtTime(1.4,45);var os=o.property("Scale");os.setValueAtTime(1.1,[100,100]);os.setValueAtTime(1.4,[62,62]);bez(os,80,50);
 var st=lineShape(comp,"strike",RED,10);st[1].expression=unionExpr(["@old"],[0,0])+'var y=(y0+y1)/2;createPath([[x0-16,y],[x1+16,y]],[],[],false)';trimIn(st[0],0.8,1.05);
 var ns=n.property("Scale");ns.setValueAtTime(1.35,[130,130]);ns.setValueAtTime(1.6,[100,100]);bez(ns,90,40);fade(n,1.35,1.45);fade(t,1.75,2.0);exitAll(comp);}
function countTitle(comp){
 var n=tx(comp,"number",280,VIOLET,HV,MX+60,1100,560,"left");srcE(n,'var s=String(d.number||"");var m=s.match(/^(\\d+)(.*)$/);if(m&&+m[1]<=999){var t=ease(time,0.3,0.85,0,1);Math.round(+m[1]*t)+m[2];}else s');
 var r=tx(comp,"rest",100,INK,HV,0,0,520,"left");r.property("Position").expression='var L=thisComp.layer("@number");var q=L.sourceRectAtTime(time,false);var p=L.toComp([q.left+q.width,q.top+q.height]);var m=sourceRectAtTime(time,false);[p[0]+22,p[1]-m.height/2*scale[1]/100-4]';
 var l2=tx(comp,"line2",100,INK,HV,MX+60,1300,730,"left");
 var N=["@number","@rest","@line2"];var b=block(comp,"panel",N,[60,48],PAPER,null,24);b.moveToEnd();softShadow(b,45,60,16);originAt(b,N,[60,48]);grow(b,0.15,0.45,[96,96]);fade(b,0.15,0.35);
 var sc=n.property("Scale");sc.setValueAtTime(0.3,[125,125]);sc.setValueAtTime(0.6,[100,100]);bez(sc,90,40);fade(n,0.3,0.38);fade(r,0.8,1.0);lift(l2,1.0,16,0.4);exitAll(comp);}
function metricTrend(comp){
 canvas(comp,PAPER);var X0=MX+40,X1=846;
 var CH=D+NUMF+'var V=NUM("points");var n=Math.max(V.length,2);var lo=Math.min.apply(null,V),hi=Math.max.apply(null,V);var pd=(hi-lo)*0.2||1;lo-=pd;hi+=pd;function X(i){return '+X0+'+'+(X1-X0)+'*i/(n-1);}function Y(v){return 1340-(v-lo)/(hi-lo)*480;}';
 var lb=tx(comp,"label",44,MUTE,MED,X0,520,880,"left");lift(lb,0.2,10,0.4);
 var v=tx(comp,"value",250,TEAL,HV,X0,720,680,"left");srcE(v,NUMF+FMT+'var V=NUM("points");var e=+d.value||0;var a=V.length?V[0]:0;var t=ease(time,0.5,1.7,0,1);F(a+(e-a)*t,DP(e))');fade(v,0.45,0.6);
 var u=tx(comp,"unit",90,TEAL,HV,0,0,300,"left");u.property("Position").expression='var L=thisComp.layer("@value");var q=L.sourceRectAtTime(time,false);var p=L.toComp([q.left+q.width,q.top+q.height]);var m=sourceRectAtTime(time,false);[p[0]+14,p[1]-m.height/2*scale[1]/100]';fade(u,0.6,0.8);
 for(var k=0;k<2;k++){var a=filledPath(comp,k?"down":"up",TEAL);a[1].expression=unionExpr(["@value","@unit"],[0,0])+'var x=x1+30,y=(y0+y1)/2+10,s=24;createPath('+(k?'[[x,y-s],[x+2*s,y-s],[x+s,y+s]]':'[[x,y+s],[x+2*s,y+s],[x+s,y-s]]')+',[],[],true)';
  a[0].property("Opacity").expression=CH+'var up=V[V.length-1]>=V[0];('+(k?'!up':'up')+')?linear(time,1.6,1.8,0,100):0';}
 var ys=[860,1100,1340];for(var k=0;k<3;k++){var gl=lineShape(comp,"grid "+k,k==2?[0.72,0.73,0.76]:LINE,k==2?3:2);staticPath(gl[1],[[X0,ys[k]],[X1,ys[k]]]);fade(gl[0],0.3,0.5);}
 var tl=lineShape(comp,"trend",TEAL,7);tl[1].expression=CH+'var p=[];for(var i=0;i<V.length;i++)p.push([X(i),Y(V[i])]);createPath(p,[],[],false)';trimIn(tl[0],0.5,1.7);
 for(var i=0;i<8;i++){var dd=hollow(comp,"pt "+i,24,TEAL,5);dd.property("Position").expression=CH+'V.length>'+i+'?[X('+i+'),Y(V['+i+'])]:[-200,-200]';
  dd.property("Scale").expression=CH+'var t0=0.5+1.2*'+i+'/(n-1);var s=ease(time,t0,t0+0.15,0,100);[s,s]';
  var xl=tx(comp,"xl"+i,28,MUTE,REG,0,1385,200);srcE(xl,LISTF+'LST("xlabels")['+i+']||""');xl.property("Position").expression=CH+'[X('+i+'),1385]';fade(xl,0.4,0.6);}
 var so=tx(comp,"source",28,MUTE,REG,X0,1450,880,"left");fade(so,1.8,2.0);}
function numberRoll(comp){
 canvas(comp,PAPER);var X0=MX+40;var bar=rect(comp,"bar",64,8,INK,4,null);bar[0].property("Anchor Point").setValue([-32,0]);bar[0].property("Position").setValue([X0,900]);grow(bar[0],0.15,0.45);
 var lb=tx(comp,"label",44,MUTE,MED,X0,990,880,"left");lift(lb,0.2,10,0.4);
 var v=tx(comp,"to",150,INK,HV,X0,1140,742,"left");srcE(v,'var a=+d.from||0,b=+d.to||0,dp=d.decimals||0;var t=Math.min(Math.max((time-0.45)/1.6,0),1);t=1-Math.pow(1-t,3);var x=a+(b-a)*t;var ip=String(Math.floor(Math.abs(x))),dg=String(Math.floor(Math.abs(b))).length;while(ip.length<dg)ip="0"+ip;var s=ip.replace(/\\B(?=(\\d{3})+(?!\\d))/g,",");if(dp)s+="."+Math.abs(x).toFixed(dp).split(".")[1];String(d.prefix||"")+s+String(d.unit||"")');
 v.property("Scale").expression='var r=sourceRectAtTime(inPoint+4,false);var k=r.width>742?742/r.width:1;value*k';fade(v,0.4,0.5);
 var cl=[RED,TEAL];for(var k=0;k<2;k++){var vis=D+'var dn=String(d.delta||"").charAt(0)=="-";(d.delta&&'+(k?'dn':'!dn')+')?linear(time,2.05,2.25,0,100):0';
  var dt=tx(comp,"delta",60,cl[k],HV,X0+66,1300,600,"left");dt.name="@delta"+(k?" down":"");srcE(dt,'String(d.delta||"").replace(/^[+-]/,"")');dt.property("Opacity").expression=vis;
  var a=filledPath(comp,k?"delta down arrow":"delta up arrow",cl[k]);a[1].setValue((function(){var sh=new Shape();sh.vertices=k?[[X0,1278],[X0+44,1278],[X0+22,1320]]:[[X0,1322],[X0+44,1322],[X0+22,1280]];sh.closed=true;return sh;})());a[0].property("Opacity").expression=vis;}
 var nt=tx(comp,"note",40,MUTE,MED,X0,1420,880,"left");lift(nt,2.3,10,0.4);}
function termCard(comp){
 var ic=dot(comp,"icon dot",104,BLUE);ic.property("Position").setValue([MX+112,1180]);fade(ic,0.35,0.5);
 var il=tx(comp,"icon",54,PAPER,HV,MX+112,1180,90);srcE(il,'String(d.icon||String(d.term||"").charAt(0))');fade(il,0.4,0.55);
 var tm=tx(comp,"term",72,INK,HV,MX+196,1156,600,"left");lift(tm,0.45,12,0.4);
 var tg=tx(comp,"tag",30,BLUE,BOLD,0,0,300,"left");tg.property("Position").expression='var L=thisComp.layer("@term");var q=L.sourceRectAtTime(time,false);var p=L.toComp([q.left+q.width,q.top+q.height/2]);[p[0]+40,p[1]]';fade(tg,0.7,0.85);
 var tb=block(comp,"tag chip",["@tag"],[16,8],[0.9,0.94,1],null,8);under(tb,tg);follow(tb,tg);
 var l1=tx(comp,"line1",40,MUTE,MED,MX+196,1250,660,"left");var l2=tx(comp,"line2",40,MUTE,MED,MX+196,1310,660,"left");lift(l1,0.8,10,0.4);lift(l2,0.9,10,0.4);
 var N=["icon dot","@term","@tag","@line1","@line2"];var b=block(comp,"card",N,[44,40],PAPER,null,26);b.moveToEnd();softShadow(b,45,60,16);originAt(b,N,[44,40],"left");grow(b,0.15,0.45);fade(b,0.15,0.3);exitAll(comp);}
function pickOne(comp){
 canvas(comp,PAPER);var q=tx(comp,"question",84,INK,HV,W/2,560,940);lift(q,0.2,14,0.4);
 // The reveal holds with every option still on screen and the rest dimmed; only a result line collapses them afterwards.
 var A=D+LISTF+'var O=LST("options");var a=Math.round(d.answer||1)-1;var C=d.result?1:0;';
 for(var i=0;i<6;i++){var f="opt"+(i+1),y=770+i*130,t0=0.5+i*0.09;
  var POS=A+'var y='+y+';if('+i+'==a&&C){y+=(690-y)*ease(time,4.1,4.5,0,1);}[540,y]';
  var OP=A+'var v=O['+i+']?linear(time,'+t0+','+(t0+0.2)+',0,100):0;if('+i+'!=a){v*=linear(time,2.2,2.45,1,0.3);if(C)v*=linear(time,4.0,4.2,1,0);}v';
  var SC=A+'var r=sourceRectAtTime(time,false);var f=r.width>580?580/r.width:1;var k=('+i+'==a)?1+0.06*Math.sin(Math.PI*clamp((time-2.2)/0.25,0,1)):linear(time,2.2,2.45,1,0.95);value*f*k';
  var t=tx(comp,f,56,INK,BOLD,540,y,580);srcE(t,LISTF+'LST("options")['+i+']||""');t.property("Position").expression=POS;t.property("Opacity").expression=OP;t.property("Scale").expression=SC;
  var b=block(comp,f+" chip",["@"+f],[52,24],PAPER,[LINE,2],48);under(b,t);follow(b,t);
  var PK=A+'('+i+'==a&&O['+i+'])?linear(time,2.2,2.35,0,100):0';
  var bi=block(comp,f+" pick",["@"+f],[52,24],INK,null,48);under(bi,t);bi.property("Opacity").expression=PK;
  var w=tx(comp,f,56,PAPER,BOLD,540,y,580);w.name="@"+f+" w";srcE(w,LISTF+'LST("options")['+i+']||""');w.property("Position").expression='thisComp.layer("@'+f+'").position';w.property("Scale").expression='thisComp.layer("@'+f+'").scale';w.property("Opacity").expression=PK;}
 var r=tx(comp,"result",68,INK,HV,W/2,960,940);accent(r,"result","accent",BLUE,0);accent(r,"result","accent",BLUE,1);fade(r,4.5,4.8);}
function lineStory(comp){
 canvas(comp,PAPER);var ti=tx(comp,"title",64,INK,HV,MX+40,430,880,"left");lift(ti,0.15,12,0.4);var so=tx(comp,"source",30,MUTE,REG,MX+40,505,880,"left");fade(so,0.3,0.5);
 var CH=D+NUMF+FMT+'var H=NUM("history"),G=NUM("forecast"),K=NUM("alt");var all=H.concat(G,K);var l0=Math.min.apply(null,all),h0=Math.max.apply(null,all);var raw=(h0-l0)/4||1,mg=Math.pow(10,Math.floor(Math.log(raw)/Math.LN10)),cs=[1,2,2.5,5,10],st=mg,lo=0;for(var c=0;c<cs.length;c++){st=cs[c]*mg;lo=Math.floor(l0/st)*st;if(lo+4*st>=h0)break;}var hi=lo+4*st;var n=Math.max(H.length+G.length,2),ti=Math.max(H.length-1,0);function X(i){return 170+680*i/(n-1);}function Y(v){return 1400-(v-lo)/(hi-lo)*660;}';
 for(var k=0;k<5;k++){var gl=lineShape(comp,"grid "+k,k==0?[0.72,0.73,0.76]:LINE,k==0?3:2);gl[1].expression=CH+'var y=Y(lo+'+k+'*st);createPath([[170,y],[850,y]],[],[],false)';fade(gl[0],0.2,0.4);
  var yt=tx(comp,"yt"+k,26,MUTE,REG,0,0,200,"left");rightAnchor(yt);yt.property("Source Text").expression=CH+'F(lo+'+k+'*st,DP(st))';yt.property("Position").expression=CH+'[150,Y(lo+'+k+'*st)]';fade(yt,0.2,0.4);}
 for(var i=0;i<10;i++){var xl=tx(comp,"xl"+i,26,MUTE,REG,0,0,160);srcE(xl,'String((String(d.xlabels||"").split(/[,，]/))['+i+']||"")');xl.property("Position").expression=CH+'[X('+i+'),1440]';fade(xl,0.2,0.4);}
 var hs=lineShape(comp,"history",[0.55,0.57,0.6],5);hs[1].expression=CH+'var p=[];for(var i=0;i<H.length;i++)p.push([X(i),Y(H[i])]);createPath(p,[],[],false)';trimIn(hs[0],0.3,1.1);
 var fc=lineShape(comp,"forecast",RED,7);fc[1].expression=CH+'var p=[[X(ti),Y(H[ti])]];for(var j=0;j<G.length;j++)p.push([X(ti+1+j),Y(G[j])]);createPath(p,[],[],false)';trimIn(fc[0],1.5,2.5);
 var al=lineShape(comp,"alt",INK,4);al[1].expression=CH+'var p=[[X(ti),Y(H[ti])]];for(var j=0;j<K.length;j++)p.push([X(ti+1+j),Y(K[j])]);createPath(p,[],[],false)';trimIn(al[0],2.7,3.5);dashes(al[0],16,12);al[0].property("Opacity").expression=D+'d.alt?100:0';
 var rp=ring(comp,"ripple",RED,3);rp[1].property("Size").setValue([26,26]);rp[0].property("Position").expression=CH+'[X(ti),Y(H[ti])]';var rs=rp[0].property("Scale");rs.setValueAtTime(1.1,[100,100]);rs.setValueAtTime(1.6,[340,340]);rp[0].property("Opacity").expression='time<1.1?0:linear(time,1.1,1.6,100,0)';
 var tu=hollow(comp,"turn",26,RED,6);tu.property("Position").expression=CH+'[X(ti),Y(H[ti])]';var us=tu.property("Scale");us.setValueAtTime(1.1,[0,0]);us.setValueAtTime(1.25,[100,100]);bez(us,85,40);
 var TL=CH+'var y=Y(H[ti]),dn=y<1240;';
 var tl=tx(comp,"turn_label",32,RED,BOLD,0,0,300);tl.property("Position").expression=TL+'[X(ti),dn?y+110:y-110]';fade(tl,1.25,1.45);
 var tc=block(comp,"turn chip",["@turn_label"],[18,10],PAPER,[RED,2],8);under(tc,tl);follow(tc,tl);
 var ld=lineShape(comp,"turn leader",RED,2);ld[1].expression=TL+'var x=X(ti);createPath(dn?[[x,y+20],[x,y+86]]:[[x,y-20],[x,y-86]],[],[],false)';follow(ld[0],tl);
 var el=tx(comp,"end_label",34,RED,HV,0,0,300);rightAnchor(el);el.property("Source Text").expression=CH+'String(d.end_label||(G.length?F(G[G.length-1],DP(G[G.length-1])):""))';el.property("Position").expression=CH+'var j=G.length-1;j>=0?[X(ti+1+j)+12,Y(G[j])-58]:[-500,0]';fade(el,2.5,2.65);
 var ec=block(comp,"end chip",["@end_label"],[16,10],PAPER,[RED,2],8);under(ec,el);follow(ec,el);
 var kl=tx(comp,"alt_label",30,INK,BOLD,0,0,300);rightAnchor(kl);kl.property("Position").expression=CH+'var j=K.length-1;j>=0?[X(ti+1+j)+12,Y(K[j])-56]:[-500,0]';fade(kl,3.5,3.65);
 var kc=block(comp,"alt chip",["@alt_label"],[16,10],PAPER,[INK,2],8);under(kc,kl);follow(kc,kl);}
function barGrow(comp){
 canvas(comp,PAPER);var ti=tx(comp,"title",64,INK,HV,MX+40,430,880,"left");lift(ti,0.15,12,0.4);var co=tx(comp,"conclusion",52,RED,HV,MX+40,530,880,"left");fade(co,2.2,2.5);
 var CH=D+NUMF+FMT+'var V=NUM("values");var n=Math.max(V.length,1);var mx=Math.max.apply(null,V.concat([0]))||1;var sl=680/n,bw=Math.min(sl*0.62,120);var hl=(d.highlight?Math.round(d.highlight):n)-1;function X(i){return 170+sl*(i+0.5);}function HT(i){return Math.max(V[i],0)/mx*600;}';
 var ax=lineShape(comp,"baseline",[0.55,0.57,0.6],3);staticPath(ax[1],[[170,1390],[850,1390]]);var ay=lineShape(comp,"axis",LINE,2);staticPath(ay[1],[[170,740],[170,1390]]);fade(ax[0],0.25,0.45);fade(ay[0],0.25,0.45);
 for(var i=0;i<8;i++){var t0=0.45+i*0.12;var T=CH+'var t=ease(time,'+t0+','+(t0+0.55)+',0,1);';
  for(var k=0;k<2;k++){var vis=CH+'('+i+'<V.length&&'+(k?'':'!')+'('+i+'==hl))?100:0';
   var b=rect(comp,"bar "+i+(k?" hl":""),10,10,k?RED:[0.83,0.84,0.86],4,null);b[0].property("Position").setValue([0,0]);b[1].property("Size").expression=T+'[bw,Math.max(HT('+i+')*t,0.01)]';b[1].property("Position").expression=T+'[X('+i+'),1390-HT('+i+')*t/2]';b[0].property("Opacity").expression=vis;
   var vl=tx(comp,"v"+i+(k?"h":""),k?46:40,k?RED:INK,HV,0,0,200);vl.property("Source Text").expression=T+(i<0?'':'')+'V.length>'+i+'?F(V['+i+']*t,DP(V['+i+'])):""';vl.property("Position").expression=T+'[X('+i+'),1390-HT('+i+')*t-36]';vl.property("Opacity").expression=CH+'(('+i+'<V.length&&'+(k?'':'!')+'('+i+'==hl))?100:0)*(time>'+(t0+0.05)+'?1:0)';}
  var xl=tx(comp,"xl"+i,28,MUTE,REG,0,0,160);srcE(xl,LISTF+'LST("labels")['+i+']||""');xl.property("Position").expression=CH+'[X('+i+'),1432]';fade(xl,0.3,0.5);}
 var so=tx(comp,"source",28,MUTE,REG,MX+40,1468,880,"left");fade(so,2.3,2.5);}
function glassBoard(comp,folder){
 canvas(comp,[0.06,0.06,0.09]);var gw=comp.layers.addSolid(VIOLET,"glow",W,H_,1);var gm=gw.property("ADBE Mask Parade").addProperty("ADBE Mask Atom");var sh=new Shape();sh.vertices=[[140,180],[940,180],[940,1100],[140,1100]];sh.closed=true;gm.property("ADBE Mask Shape").setValue(sh);gm.property("ADBE Mask Feather").setValue([500,500]);gw.property("Opacity").setValue(45);
 var rg=rigNull(comp,"host rig");var back=rect(comp,"host back",600,640,[0.1,0.1,0.14],28,null);back[0].property("Position").setValue([W/2,600]);softShadow(back[0],60,80,20);
 var hp=photo(comp,folder,"host.png","@host",600,640,W/2,600,28);var fr=rect(comp,"host frame",600,640,null,28,[PAPER,2]);fr[0].property("Position").setValue([W/2,600]);grp(fr[0]).property("ADBE Vector Graphic - Stroke").property("ADBE Vector Stroke Opacity").setValue(25);
 back[0].parent=rg;hp[0].parent=rg;hp[1].parent=rg;fr[0].parent=rg;var rp=rg.property("Position");rp.setValueAtTime(0.1,[0,70]);rp.setValueAtTime(0.6,[0,0]);bez(rp,85,40);fade(back[0],0.1,0.35);fade(hp[0],0.1,0.35);fade(fr[0],0.1,0.35);
 var gp=rect(comp,"glass",900,560,PAPER,32,[PAPER,2]);gp[0].property("Position").setValue([W/2,1190]);var gc=grp(gp[0]);gc.property("ADBE Vector Graphic - Fill").property("ADBE Vector Fill Opacity").setValue(7);gc.property("ADBE Vector Graphic - Stroke").property("ADBE Vector Stroke Opacity").setValue(20);
 var gs=gp[0].property("Scale");gs.setValueAtTime(0.4,[96,96]);gs.setValueAtTime(0.75,[100,100]);bez(gs,85,40);fade(gp[0],0.4,0.6);
 var kk=tx(comp,"kicker",26,[0.62,0.64,0.74],MED,W/2,975,880,null,300);fade(kk,0.6,0.8);var ti=tx(comp,"title",76,PAPER,HV,W/2,1040,880);lift(ti,0.6,14,0.4);
 var CNT=D+'var S=[d.step1,d.step2,d.step3,d.step4];var n=0;for(var q=0;q<4;q++)if(S[q])n++;n=Math.max(n,1);var tw=n*190+(n-1)*58;function XC(i){return 540-tw/2+95+i*248;}';
 for(var i=0;i<4;i++){var t0=0.9+i*0.35,f="step"+(i+1),VIS=D+'d["'+f+'"]?linear(time,'+t0+','+(t0+0.2)+',0,100):0',POP=D+'var s=ease(time,'+t0+','+(t0+0.25)+',85,100);[s,s]';
  if(i>0){var ar=lineShape(comp,"arrow "+i,BLUE,4);ar[1].expression=CNT+'var x0=XC('+(i-1)+')+105,x1=XC('+i+')-105;createPath([[x0,1220],[x1,1220],[x1-12,1208],[x1,1220],[x1-12,1232]],[],[],false)';trimIn(ar[0],t0-0.25,t0);ar[0].property("Opacity").expression=D+'d["'+f+'"]?100:0';}
  var tile=rect(comp,"tile "+i,190,190,PAPER,24,[PAPER,2]);var tc=grp(tile[0]);tc.property("ADBE Vector Graphic - Fill").property("ADBE Vector Fill Opacity").setValue(9);tc.property("ADBE Vector Graphic - Stroke").property("ADBE Vector Stroke Opacity").setValue(24);
  tile[0].property("Position").expression=CNT+'[XC('+i+'),1220]';tile[0].property("Opacity").expression=VIS;tile[0].property("Scale").expression=POP;
  var nd=dot(comp,"num dot "+i,58,BLUE);nd.property("Position").expression=CNT+'[XC('+i+'),1180]';nd.property("Opacity").expression=VIS;nd.property("Scale").expression=POP;
  var nt=tx(comp,"n"+i,30,PAPER,HV,0,0,60);nt.property("Source Text").expression='"'+(i+1)+'"';nt.property("Position").expression=CNT+'[XC('+i+'),1180]';nt.property("Opacity").expression=VIS;
  var st=tx(comp,f,34,PAPER,BOLD,0,0,170);st.property("Position").expression=CNT+'[XC('+i+'),1265]';st.property("Opacity").expression=VIS;}
 var sm=tx(comp,"summary",32,PAPER,BOLD,W/2,1410,860);sm.property("Opacity").expression=D+'var S=[d.step1,d.step2,d.step3,d.step4];var n=0;for(var q=0;q<4;q++)if(S[q])n++;var t0=0.9+n*0.35+0.1;d.summary?linear(time,t0,t0+0.25,0,100):0';
 var sp=block(comp,"summary pill",["@summary"],[30,14],[0.13,0.16,0.32],[BLUE,2],40);under(sp,sm);follow(sp,sm);}
function stepLine(comp){
 canvas(comp,PAPER);var ti=tx(comp,"title",64,INK,HV,MX+40,420,880,"left");lift(ti,0.15,12,0.4);
 var LX=MX+70,CNT=D+'var S=[d.step1,d.step2,d.step3,d.step4,d.step5];var n=0;for(var q=0;q<5;q++)if(S[q])n++;n=Math.max(n,1);var cur=Math.min(Math.max(Math.round(d.current||1),1),n)-1;var te=0.3+0.35*n+0.4;';
 var ln=lineShape(comp,"rail",LINE,4);ln[1].expression=CNT+'createPath([['+LX+',580],['+LX+',620+200*(n-1)+30]],[],[],false)';var tp=ln[0].property("Contents").addProperty("ADBE Vector Filter - Trim");tp.property("End").expression=CNT+'linear(time,0.3,0.3+0.35*n,0,100)';
 var caps=["第一步","第二步","第三步","第四步","第五步"];
 for(var i=0;i<5;i++){var y=620+i*200,t0=0.3+0.35*i+0.2,f="step"+(i+1),VIS=D+'d["'+f+'"]?linear(time,'+(t0+0.07)+','+(t0+0.27)+',0,100):0';
  var nd=dot(comp,"node "+i,22,INK);nd.property("Position").setValue([LX,y]);nd.property("Scale").expression=D+'var s=d["'+f+'"]?ease(time,'+t0+','+(t0+0.15)+',0,100):0;[s,s]';
  var cp=tx(comp,"cap"+i,34,MUTE,MED,LX+56,y-54,700,"left");cp.property("Source Text").expression='"'+caps[i]+'"';cp.property("Opacity").expression=VIS;
  var st=tx(comp,f,72,INK,HV,LX+56,y+14,820,"left");st.property("Opacity").expression=VIS;
  var sr=tx(comp,f,72,RED,HV,LX+56,y+14,820,"left");sr.name="@"+f+" red";sr.property("Opacity").expression=CNT+'('+i+'==cur&&d["'+f+'"])?linear(time,te,te+0.25,0,100):0';}
 var cu=hollow(comp,"current",30,RED,5);cu.property("Position").expression=CNT+'['+LX+',620+200*cur]';cu.property("Scale").expression=CNT+'var s=ease(time,te,te+0.25,0,125);[s,s]';}
function converge(comp){
 canvas(comp,PAPER);var ti=tx(comp,"title",64,INK,HV,MX+40,430,880,"left");lift(ti,0.15,12,0.4);
 var CNT=D+'var S=[d.s1,d.s2,d.s3,d.s4];var n=0;for(var q=0;q<4;q++)if(S[q])n++;n=Math.max(n,1);var sl=Math.min(200,760/n);function XS(i){return 480+(i-(n-1)/2)*sl;}function BZ(i,u){var a=[XS(i),820],b=[480,1350],c1=[a[0],a[1]+300],c2=[b[0],b[1]-300],v=1-u;return [v*v*v*a[0]+3*v*v*u*c1[0]+3*v*u*u*c2[0]+u*u*u*b[0],v*v*v*a[1]+3*v*v*u*c1[1]+3*v*u*u*c2[1]+u*u*u*b[1]];}';
 for(var i=0;i<4;i++){var f="s"+(i+1),t0=0.7+i*0.15,m0=1.8+i*0.1;var cv=lineShape(comp,"curve "+i,[0.74,0.76,0.8],3);cv[1].expression=CNT+'var a=[XS('+i+'),870],b=[480,1300];createPath([a,b],[[0,0],[0,-260]],[[0,260],[0,0]],false)';
  trimIn(cv[0],t0,t0+0.45);cv[0].property("Opacity").expression=D+'d["'+f+'"]?linear(time,'+(m0+0.3)+','+(m0+0.6)+',100,0):0';}
 var rs=tx(comp,"result",64,PAPER,HV,480,1350,700);var rc=block(comp,"result pill",["@result"],[52,26],BLUE,null,60);under(rc,rs);follow(rc,rs);
 var sc=rs.property("Scale");sc.setValueAtTime(1.2,[70,70]);sc.setValueAtTime(1.45,[100,100]);sc.setValueAtTime(2.5,[100,100]);sc.setValueAtTime(2.62,[112,112]);sc.setValueAtTime(2.8,[100,100]);bez(sc,80,50);fade(rs,1.2,1.3);
 for(var i=0;i<4;i++){var f="s"+(i+1),m0=1.8+i*0.1,e0=0.35+i*0.08;var t=tx(comp,f,48,INK,BOLD,0,0,200);
  t.property("Position").expression=CNT+'BZ('+i+',ease(time,'+m0+','+(m0+0.6)+',0,1))';
  t.property("Scale").expression=D+'var u=ease(time,'+m0+','+(m0+0.6)+',0,1);var r=sourceRectAtTime(time,false);var k=r.width>200?200/r.width:1;var s=100*k*(1-0.65*u);[s,s]';
  t.property("Opacity").expression=D+'d["'+f+'"]?linear(time,'+e0+','+(e0+0.2)+',0,100)*linear(time,'+(m0+0.45)+','+(m0+0.6)+',1,0):0';
  var b=block(comp,f+" chip",["@"+f],[30,16],PAPER,[LINE,2],40);under(b,t);follow(b,t);}
 var nt=tx(comp,"note",44,MUTE,MED,480,1440,900);lift(nt,2.8,10,0.4);}
function lineCarry(comp,folder){
 canvas(comp,PAPER);var rg=rigNull(comp,"rig");
 var at=tx(comp,"a_title",96,INK,HV,MX,920,880,"left");var as=tx(comp,"a_sub",38,MUTE,MED,MX,1004,880,"left");
 var ln=lineShape(comp,"carry",BLUE,6);staticPath(ln[1],[[MX,1060],[1170,1060],[1170,810],[2070,810],[2070,1310],[1170,1310],[1170,1060]]);
 var tp=ln[0].property("Contents").addProperty("ADBE Vector Filter - Trim");var e=tp.property("End");e.setValueAtTime(0.35,0);e.setValueAtTime(0.85,21);e.setValueAtTime(1.5,21);e.setValueAtTime(2.7,100);bez(e,70,50);
 var ed=dot(comp,"end dot",20,BLUE);ed.property("Position").setValue([900,1060]);
 var ph=photo(comp,folder,"image.png","@image",880,480,1620,1060,0);ph[0].property("Scale").expression='var k=Math.max(880/width,480/height)*100*linear(time,2.7,3.4,1.08,1);[k,k]';
 var bt=tx(comp,"b_title",64,INK,HV,1170,1390,880,"left");var bs=tx(comp,"b_sub",34,MUTE,MED,1170,1458,880,"left");
 var kids=[at,as,ln[0],ed,ph[0],ph[1],bt,bs];for(var i=0;i<kids.length;i++)kids[i].parent=rg;
 var rp=rg.property("Position");rp.setValueAtTime(1.5,[0,0]);rp.setValueAtTime(2.4,[-1080,0]);bez(rp,80,60);
 var es=ed.property("Scale");es.setValueAtTime(0.85,[0,0]);es.setValueAtTime(1.0,[100,100]);bez(es,85,40);var eo=ed.property("Opacity");eo.setValueAtTime(1.45,100);eo.setValueAtTime(1.55,0);
 lift(at,0.15,14,0.4);lift(as,0.3,10,0.4);fade(ph[0],2.7,3.0);lift(bt,2.9,14,0.4);lift(bs,3.05,10,0.4);}
function timelineTravel(comp){
 canvas(comp,CANVAS);var kk=tx(comp,"kicker",28,BLUE,BOLD,MX+40,330,880,"left",80);var ti=tx(comp,"title",68,INK,HV,MX+40,410,880,"left");fade(kk,0.15,0.35);lift(ti,0.2,12,0.4);
 var PT=D+'var R=String(d.points||"").split(/[;；]/),PS=[];for(var q=0;q<R.length;q++){var z=R[q].split("|");if(z.length>=2&&z[0])PS.push(z);}var n=Math.max(PS.length,1);var s=Math.min(Math.max(Math.round(d.stop||n),1),n);var te=0.6+0.6*(s-1)+0.1;';
 var rg=rigNull(comp,"rig");var kids=[];var GR=[0.78,0.79,0.82];
 var ax=lineShape(comp,"axis",GR,3);staticPath(ax[1],[[-300,1260],[540+5*760+700,1260]]);kids.push(ax[0]);
 var tk=comp.layers.addShape();tk.name="ticks";var g=tk.property("Contents").addProperty("ADBE Vector Group").property("Contents");g.addProperty("ADBE Vector Shape - Rect");g.addProperty("ADBE Vector Graphic - Fill");var c=grp(tk);c.property("ADBE Vector Shape - Rect").property("Size").setValue([2,14]);c.property("ADBE Vector Graphic - Fill").property("Color").setValue(GR);
 var rp=tk.property("Contents").addProperty("ADBE Vector Filter - Repeater");rp.property("ADBE Vector Repeater Copies").setValue(70);rp.property("ADBE Vector Repeater Transform").property("ADBE Vector Repeater Position").setValue([62,0]);tk.property("Position").setValue([-300,1260]);kids.push(tk);
 for(var i=0;i<6;i++){var x=540+i*760,DIM=PT+'PS['+i+']?('+i+'==s-1?100:linear(time,te,te+0.3,100,35)):0';
  var bg=tx(comp,"bg"+i,150,[0.87,0.88,0.9],HV,x,1070,700);bg.property("Source Text").expression=PT+'PS['+i+']?PS['+i+'][0]:""';kids.push(bg);
  var pt=tx(comp,"pt"+i,52,INK,HV,x,950,520);pt.property("Source Text").expression=PT+'PS['+i+']?(PS['+i+'][1]||""):""';pt.property("Opacity").expression=DIM;kids.push(pt);
  var pd=tx(comp,"pd"+i,34,MUTE,MED,x,1018,560);pd.property("Source Text").expression=PT+'PS['+i+']?(PS['+i+'][2]||""):""';pd.property("Opacity").expression=DIM;kids.push(pd);
  var cb=block(comp,"card "+i,["@pt"+i,"@pd"+i],[40,30],PAPER,null,18);cb.moveBefore(bg);softShadow(cb,35,50,12);follow(cb,pt);
  var dl=tx(comp,"dt"+i,36,INK,BOLD,x,1322,400);dl.property("Source Text").expression=PT+'PS['+i+']?PS['+i+'][0]:""';dl.property("Opacity").expression=PT+'PS['+i+']?('+i+'==s-1?linear(time,te,te+0.25,100,0):linear(time,te,te+0.3,100,35)):0';kids.push(dl);
  var nd=dot(comp,"node "+i,18,INK);nd.property("Position").setValue([x,1260]);nd.property("Opacity").expression=PT+'PS['+i+']?100:0';kids.push(nd);}
 var hl=hollow(comp,"stop ring",34,BLUE,6);hl.property("Position").expression=PT+'[540+(s-1)*760,1260]';hl.property("Scale").expression=PT+'var k=ease(time,te,te+0.25,0,100);[k,k]';kids.push(hl);
 var db=tx(comp,"dtb",34,BLUE,BOLD,0,0,400);db.property("Source Text").expression=PT+'PS[s-1]?PS[s-1][0]:""';db.property("Position").expression=PT+'[540+(s-1)*760,1322]';db.property("Opacity").expression=PT+'linear(time,te,te+0.25,0,100)';kids.push(db);
 for(var i=0;i<kids.length;i++)kids[i].parent=rg;
 rg.property("Position").expression=PT+'var t=ease(time,0.6,0.6+0.6*(s-1),0,1);[-(s-1)*760*t,0]';}
function sliderCompare(comp,folder){
 canvas(comp,CHAR);var hd=comp.layers.addNull();hd.name="handle";var hp=hd.property("Position");hp.setValueAtTime(0.3,[850,980]);hp.setValueAtTime(1.1,[540,980]);hp.setValueAtTime(2.6,[540,980]);hp.setValueAtTime(3.4,[150,980]);hp.setValueAtTime(4.1,[540,980]);bez(hp,75,75);
 var bf=photo(comp,folder,"before.png","@before",960,1560,540,980,0);var af=photo(comp,folder,"after.png","@after",960,1560,540,980,0);
 grp(af[1]).property("ADBE Vector Shape - Rect").property("Size").expression='var x=thisComp.layer("handle").position[0];[Math.max(1020-x,0),1560]';af[1].property("Position").expression='var x=thisComp.layer("handle").position[0];[(x+1020)/2,980]';
 fade(bf[0],0,0.3);fade(af[0],0,0.3);
 var dv=lineShape(comp,"divider",PAPER,4);dv[1].expression='var x=thisComp.layer("handle").position[0];createPath([[x,200],[x,1760]],[],[],false)';softShadow(dv[0],50,20,4);
 var kn=dot(comp,"knob",68,PAPER);kn.property("Position").expression='[thisComp.layer("handle").position[0],980]';softShadow(kn,50,30,6);
 for(var k=0;k<2;k++){var cv=lineShape(comp,"chevron "+k,INK,4);cv[1].expression='var x=thisComp.layer("handle").position[0];createPath('+(k?'[[x+9,968],[x+19,980],[x+9,992]]':'[[x-9,968],[x-19,980],[x-9,992]]')+',[],[],false)';}
 var bl=tx(comp,"before_label",34,PAPER,BOLD,120,300,400,"left");var bc=block(comp,"before chip",["@before_label"],[22,12],INK,null,10);under(bc,bl);follow(bc,bl,0.6);fade(bl,0.3,0.5);
 var al=tx(comp,"after_label",34,PAPER,BOLD,960,300,400,"left");rightAnchor(al);var ac=block(comp,"after chip",["@after_label"],[22,12],INK,null,10);under(ac,al);follow(ac,al,0.6);fade(al,1.0,1.2);}
function split6040(comp,folder){
 canvas(comp,PAPER);var ph=photo(comp,folder,"image.png","@image",1080,900,540,450,0);ph[0].property("Scale").expression='var k=Math.max(1080/width,900/height)*100*(1+0.06*Math.min(time/5,1));[k,k]';
 ph[1].property("Anchor Point").setValue([0,-450]);ph[1].property("Position").setValue([540,0]);var ms=ph[1].property("Scale");ms.setValueAtTime(0.1,[100,0]);ms.setValueAtTime(0.6,[100,100]);bez(ms,85,50);
 var ti=tx(comp,"title",76,INK,HV,MX+40,1010,900,"left");lift(ti,0.5,14,0.4);
 var tints=[[0.91,0.94,1],[1,0.92,0.91],[0.9,0.97,0.94]],cols=[BLUE,RED,TEAL];
 for(var i=0;i<3;i++){var f="p"+(i+1),y=1140+i*110,t0=0.9+i*0.45;var t=tx(comp,f,44,cols[i],BOLD,MX+68,y,860,"left");var b=block(comp,f+" chip",["@"+f],[28,14],tints[i],null,12);under(b,t);originAt(b,["@"+f],[28,14],"left");grow(b,t0,t0+0.25,[80,100]);fade(b,t0,t0+0.12);fade(t,t0+0.08,t0+0.2);}}
function beforeAfterScrub(comp,folder){
 canvas(comp,CANVAS);var hd=comp.layers.addNull();hd.name="handle";var hp=hd.property("Position");hp.setValueAtTime(0.6,[840,945]);hp.setValueAtTime(1.0,[190,945]);hp.setValueAtTime(1.4,[800,945]);hp.setValueAtTime(1.8,[320,945]);hp.setValueAtTime(2.25,[610,945]);bez(hp,60,60);
 var back=rect(comp,"frame back",960,1050,PAPER,0,null);back[0].property("Position").setValue([540,945]);softShadow(back[0],40,60,16);
 var af=photo(comp,folder,"after.png","@after",960,1050,540,945,0);
 var bf=photo(comp,folder,"before.png","@before",960,1050,540,945,0);var bg=photo(comp,folder,"after.png","@after grey",960,1050,540,945,0);
 // Screens must stay whole, so they fit inside the frame instead of filling it.
 var FIT='var k=Math.min(960/width,1050/height)*100;[k,k]';af[0].property("Scale").expression=FIT;bf[0].property("Scale").expression=FIT;bg[0].property("Scale").expression=FIT;
 bg[0].property("ADBE Effect Parade").addProperty("ADBE Tint");var bc=bg[0].property("ADBE Effect Parade").addProperty("ADBE Brightness & Contrast 2");bc.property("ADBE Brightness & Contrast 2-0001").setValue(35);bc.property("ADBE Brightness & Contrast 2-0002").setValue(-35);
 var M=[bf[1],bg[1]];for(var k=0;k<2;k++){grp(M[k]).property("ADBE Vector Shape - Rect").property("Size").expression='var x=thisComp.layer("handle").position[0];[Math.max(1020-x,0),1050]';M[k].property("Position").expression='var x=thisComp.layer("handle").position[0];[(x+1020)/2,945]';}
 bf[0].property("Opacity").expression=D+'(d._images&&d._images.indexOf("before")>=0)?100:0';bg[0].property("Opacity").expression=D+'(d._images&&d._images.indexOf("before")>=0)?0:100';
 var dv=lineShape(comp,"divider",PAPER,5);dv[1].expression='var x=thisComp.layer("handle").position[0];createPath([[x,420],[x,1470]],[],[],false)';softShadow(dv[0],50,20,4);
 var kn=dot(comp,"knob",58,PAPER);kn.property("Position").expression='[thisComp.layer("handle").position[0],945]';softShadow(kn,50,30,6);
 for(var k=0;k<2;k++){var cv=lineShape(comp,"chevron "+k,INK,4);cv[1].expression='var x=thisComp.layer("handle").position[0];createPath('+(k?'[[x+8,934],[x+17,945],[x+8,956]]':'[[x-8,934],[x-17,945],[x-8,956]]')+',[],[],false)';}
 var pill=rect(comp,"toggle",460,84,PAPER,42,[LINE,2]);pill[0].property("Position").setValue([540,330]);softShadow(pill[0],30,40,8);
 var hl=rect(comp,"toggle on",210,64,INK,32,null);hl[0].property("Position").expression='var x=thisComp.layer("handle").position[0];[linear(x,520,580,650,430),330]';
 var SIDE=[["after_label",430,'linear(x,520,580,0,100)'],["before_label",650,'linear(x,520,580,100,0)']];
 for(var k=0;k<2;k++){var ink=tx(comp,SIDE[k][0],34,INK,BOLD,SIDE[k][1],330,190);ink.property("Opacity").expression='var x=thisComp.layer("handle").position[0];100-'+SIDE[k][2];
  var wt=tx(comp,SIDE[k][0],34,PAPER,BOLD,SIDE[k][1],330,190);wt.name="@"+SIDE[k][0]+" w";wt.property("Opacity").expression='var x=thisComp.layer("handle").position[0];'+SIDE[k][2];}
 fade(back[0],0,0.3);fade(af[0],0,0.3);}

// ---- batch 3: openers, material, map, transitions, end cards ----
var THEMES={ink:CHAR,blue:BLUE,red:RED,violet:VIOLET,teal:TEAL,orange:ORANGE};
function themeSel(l,def,k){l.property("Opacity").expression=D+'var c=String(d.color||"'+def+'");if(!({ink:1,blue:1,red:1,violet:1,teal:1,orange:1})[c])c="'+def+'";(c=="'+k+'")?100:0';}
function themeSolids(comp,def){for(var k in THEMES){var s=comp.layers.addSolid(THEMES[k],"bg "+k,W,H_,1);themeSel(s,def,k);}}
function shade(c,f){return f>0?[c[0]+(1-c[0])*f,c[1]+(1-c[1])*f,c[2]+(1-c[2])*f]:[c[0]*(1+f),c[1]*(1+f),c[2]*(1+f)];}
function cursor(comp,x0,y0,x1,y1,tc){var s=comp.layers.addShape();s.name="cursor";var g=s.property("Contents").addProperty("ADBE Vector Group").property("Contents");g.addProperty("ADBE Vector Shape - Group");g.addProperty("ADBE Vector Graphic - Stroke");g.addProperty("ADBE Vector Graphic - Fill");
 var c=grp(s);var sh=new Shape();sh.vertices=[[0,0],[0,54],[13,42],[23,64],[33,60],[23,38],[40,38]];sh.closed=true;c.property("ADBE Vector Shape - Group").property("Path").setValue(sh);
 var st=c.property("ADBE Vector Graphic - Stroke");st.property("Color").setValue(PAPER);st.property("Stroke Width").setValue(4);c.property("ADBE Vector Graphic - Fill").property("Color").setValue(INK);
 var p=s.property("Position");p.setValueAtTime(tc-0.9,[x0,y0]);p.setValueAtTime(tc-0.1,[x1,y1]);bez(p,85,60);
 var sc=s.property("Scale");sc.setValueAtTime(tc,[100,100]);sc.setValueAtTime(tc+0.08,[86,86]);sc.setValueAtTime(tc+0.2,[100,100]);
 var o=s.property("Opacity");o.setValueAtTime(tc-0.9,0);o.setValueAtTime(tc-0.75,100);o.setValueAtTime(tc+0.7,100);o.setValueAtTime(tc+0.95,0);softShadow(s,40,12,4);return s;}
function press(l,tc){var sc=l.property("Scale");sc.setValueAtTime(tc,[100,100]);sc.setValueAtTime(tc+0.08,[93,93]);sc.setValueAtTime(tc+0.22,[100,100]);}
function before(l,tc,extra){l.property("Opacity").expression=(extra||'')+'time<'+tc+'?value:0';}
function after(l,tc,extra){l.property("Opacity").expression=(extra||'')+'time<'+tc+'?0:value';}

function chapterCard(comp){
 themeSolids(comp,"ink");
 var n=tx(comp,"number",300,PAPER,SONG,MX+40,800,900,"left");var ns=n.property("Scale");ns.setValueAtTime(0.2,[112,112]);ns.setValueAtTime(0.7,[100,100]);bez(ns,85,40);fade(n,0.2,0.4);
 var ti=tx(comp,"title",84,PAPER,HV,MX+40,1050,900,"left");lift(ti,0.45,16,0.45);
 var ln=rect(comp,"rule",96,6,PAPER,3,null);ln[0].property("Anchor Point").setValue([-48,0]);ln[0].property("Position").setValue([MX+40,1140]);grow(ln[0],0.7,1.0);
 var s=tx(comp,"sub",28,[0.78,0.79,0.82],MED,MX+40,1196,900,"left",200);srcE(s,'"CHAPTER "+String(d.number||"")+(d.sub?"   ·   "+d.sub:"")');fade(s,0.85,1.1);
 var cv=lineShape(comp,"flourish",PAPER,3);var sh=new Shape();sh.vertices=[[560,1760],[990,1420]];sh.inTangents=[[0,0],[-40,170]];sh.outTangents=[[300,30],[0,0]];sh.closed=false;cv[1].setValue(sh);cv[0].property("Opacity").setValue(40);trimIn(cv[0],0.5,1.4);
 var rg=ring(comp,"flourish ring",PAPER,3);rg[1].property("Size").setValue([70,70]);rg[0].property("Position").setValue([960,1470]);rg[0].property("Opacity").setValue(40);var rs=rg[0].property("Scale");rs.setValueAtTime(1.2,[0,0]);rs.setValueAtTime(1.45,[100,100]);bez(rs,85,40);
 // The card pushes in over the outgoing shot and slides away to reveal the next one, like a chapter break in the cut.
 var kids=[];for(var i=1;i<=comp.numLayers;i++)kids.push(comp.layer(i));var rig=rigNull(comp,"card rig");for(var i=0;i<kids.length;i++)kids[i].parent=rig;
 rig.property("Position").expression=D+'var e=(d._duration_ms||3000)/1000;[ease(time,0,0.35,1080,0)+ease(time,e-0.45,e-0.05,0,1080),0]';}
function chapterList(comp){
 canvas(comp,CHAR);var GR=[0.86,0.87,0.9];
 var CS=[[1,1],[-1,1],[1,-1],[-1,-1]];for(var k=0;k<4;k++){var sx=CS[k][0],sy=CS[k][1],x=sx>0?70:1010,y=sy>0?200:1720;var c=lineShape(comp,"corner "+k,PAPER,3);
  c[1].expression='var o=linear(time,0.1,0.5,26,0);var x='+x+'-('+sx+')*o,y='+y+'-('+sy+')*o;createPath([[x,y+('+sy+')*64],[x,y],[x+('+sx+')*64,y]],[],[],false)';c[0].property("Opacity").expression='linear(time,0.1,0.4,0,55)';}
 var kk=tx(comp,"kicker",28,[0.6,0.62,0.68],MED,MX+120,660,900,"left",300);kk.property("Source Text").expression='"CHAPTER"';fade(kk,0.2,0.4);
 var CNT=D+'var S=[d.c1,d.c2,d.c3,d.c4,d.c5];var n=0;for(var q=0;q<5;q++)if(S[q])n++;n=Math.max(n,1);var cur=Math.min(Math.max(Math.round(d.current||1),1),n)-1;';
 for(var i=0;i<5;i++){var y=780+i*140,t0=0.4+i*0.15,f="c"+(i+1),VIS=D+'d["'+f+'"]?linear(time,'+t0+','+(t0+0.25)+',0,100):0',RD=CNT+'('+i+'==cur&&d["'+f+'"])?linear(time,1.5,1.7,0,100):0';
  var nm=tx(comp,"num"+i,32,MUTE,MED,MX+120,y,80,"left");nm.property("Source Text").expression='"0'+(i+1)+'"';nm.property("Opacity").expression=VIS;
  var tt=tx(comp,f,58,GR,BOLD,MX+200,y,760,"left");tt.property("Opacity").expression=VIS;
  var nr=tx(comp,"num"+i,32,RED,MED,MX+120,y,80,"left");nr.name="@num"+i+" red";nr.property("Source Text").expression='"0'+(i+1)+'"';nr.property("Opacity").expression=RD;
  var tr=tx(comp,f,58,RED,BOLD,MX+200,y,760,"left");tr.name="@"+f+" red";tr.property("Opacity").expression=RD;
  var dm=filledPath(comp,"marker "+i,RED);dm[1].setValue((function(yy){var s=new Shape();s.vertices=[[MX+84,yy-10],[MX+94,yy],[MX+84,yy+10],[MX+74,yy]];s.closed=true;return s;})(y));dm[0].property("Opacity").expression=RD;}}
function titleToLabel(comp){
 canvas(comp,PAPER);var t=tx(comp,"title",96,INK,HV,0,0,692,"left");
 t.property("Scale").expression='var r=sourceRectAtTime(time,false);var f=r.width>692?692/r.width:1;var s=linear(ease(time,1.0,1.5,0,1),0,1,1,0.55);[100*f*s,100*f*s]';
 t.property("Position").expression='var r=sourceRectAtTime(time,false);var f=r.width>692?692/r.width:1;var e=ease(time,1.0,1.5,0,1);var x0=540-r.width*f/2;[x0+('+(MX+40)+'-x0)*e,960+(470-960)*e]';fade(t,0.15,0.4);
 var tints=[[0.91,0.94,1],[0.9,0.97,0.94],[1,0.96,0.86]];
 for(var i=0;i<3;i++){var f="p"+(i+1),y=680+i*170,t0=1.6+i*0.35;var br=rect(comp,f+" bar",8,78,BLUE,4,null);br[0].property("Position").setValue([MX+44,y]);br[0].property("Opacity").expression=D+'d["'+f+'"]?linear(time,'+t0+','+(t0+0.2)+',0,100):0';
  var tt=tx(comp,f,54,INK,BOLD,MX+104,y,700,"left");var cb=block(comp,f+" chip",["@"+f],[28,16],tints[i],null,12);under(cb,tt);follow(cb,tt);lift(tt,t0+0.05,14,0.35);}}
function leadWord(comp){
 // The panel is sized from the sentence's final layout and shows up while the word is still shrinking, so the word lands on it instead of on the footage.
 var Y=1240,LAY='var W1=thisComp.layer("@word").sourceRectAtTime(time,false).width,W2=thisComp.layer("@rest").sourceRectAtTime(time,false).width,G=30,TW=W1+G+W2,k=TW>700?700/TW:1,s0=Math.min(380,800/Math.max(W1,1)*100),e=ease(time,0.6,1.0,0,1);';
 var w=tx(comp,"word",120,INK,HV,0,0,5000,"left");w.property("Scale").expression=LAY+'var s=time<0.6?s0*linear(time,0.15,0.35,1.08,1):linear(e,0,1,s0,100*k);[s,s]';
 w.property("Position").expression=LAY+'var a=[472-W1*s0/200,960],b=[472-TW*k/2,'+Y+'];[a[0]+(b[0]-a[0])*e,a[1]+(b[1]-a[1])*e]';fade(w,0.15,0.25);
 var r=tx(comp,"rest",120,INK,HV,0,0,5000,"left");accent(r,"rest","accent",BLUE,0);r.property("Scale").expression=LAY+'[100*k,100*k]';r.property("Position").expression=LAY+'[472-TW*k/2+(W1+G)*k,'+Y+']';
 var an=r.property("ADBE Text Properties").property("ADBE Text Animators").addProperty("ADBE Text Animator");an.property("ADBE Text Animator Properties").addProperty("ADBE Text Opacity").setValue(0);
 var sel=an.property("ADBE Text Selectors").addProperty("ADBE Text Selector");var ss=sel.property("ADBE Text Percent Start");ss.setValueAtTime(0.95,0);ss.setValueAtTime(1.5,100);
 var su=tx(comp,"sub",38,MUTE,MED,472,Y+120,900);fade(su,1.6,1.9);
 var pn=rect(comp,"panel",10,10,PAPER,24,null);pn[0].moveToEnd();pn[0].property("Position").setValue([0,0]);softShadow(pn[0],45,60,16);
 var GEO=LAY+'var hs=thisComp.layer("@sub").sourceRectAtTime(time,false).width>0;var top='+Y+'-62*k-50,bot=(hs?'+(Y+150)+':'+Y+'+62*k)+50;';
 pn[1].property("Size").expression=GEO+'[TW*k+120,bot-top]';pn[1].property("Position").expression=GEO+'[472,(top+bot)/2]';
 pn[0].property("Opacity").expression='linear(time,0.55,0.75,0,100)';var ps=pn[0].property("Scale");pn[0].property("Anchor Point").expression=GEO+'[472,(top+bot)/2]';pn[0].property("Position").expression=GEO+'[472,(top+bot)/2]';
 ps.setValueAtTime(0.55,[94,94]);ps.setValueAtTime(0.8,[100,100]);bez(ps,85,40);exitAll(comp);}
function newsDesk(comp,folder){
 canvas(comp,CANVAS);
 var c1=card(comp,folder,"image1.png","@image1",880,700,540,700);c1.property("Scale").expression='var k=Math.min(880/width,700/height)*100*(1+0.04*clamp((time-0.6)/4,0,1));[k,k]';c1.property("Rotation").setValue(-1.5);
 var f1=comp.layer("@image1 frame");f1.property("Rotation").expression='thisComp.layer("@image1").rotation';f1.property("Opacity").expression='thisComp.layer("@image1").opacity';
 var p1=c1.property("Position");p1.setValueAtTime(0.2,[540,1040]);p1.setValueAtTime(0.6,[540,700]);bez(p1,85,40);fade(c1,0.2,0.35);
 var ul=lineShape(comp,"underline",RED,8);ul[0].parent=c1;ul[0].property("Position").setValue([0,0]);ul[0].property("Anchor Point").setValue([0,0]);
 ul[1].expression=D+'var L=thisLayer.parent;createPath([[d.line_x*L.width,d.line_y*L.height],[(d.line_x+d.line_w)*L.width,d.line_y*L.height]],[],[],false)';
 grp(ul[0]).property("ADBE Vector Graphic - Stroke").property("Stroke Width").expression='8/(thisLayer.parent.scale[0]/100)';trimIn(ul[0],1.2,1.5);ul[0].property("Opacity").expression=D+'d.line_w>0?100:0';
 var c2=card(comp,folder,"image2.png","@image2",700,520,600,1170);c2.property("Rotation").setValue(2);var f2=comp.layer("@image2 frame");f2.property("Rotation").expression='thisComp.layer("@image2").rotation';f2.property("Opacity").expression='thisComp.layer("@image2").opacity';
 var p2=c2.property("Position");p2.setValueAtTime(2.0,[1300,1170]);p2.setValueAtTime(2.45,[600,1170]);bez(p2,85,40);c2.property("Opacity").expression=D+'(d._images&&d._images.indexOf("image2")>=0)?linear(time,2.0,2.15,0,100):0';
 var so=tx(comp,"source",30,MUTE,MED,866,1468,700,"left");rightAnchor(so);fade(so,1.0,1.3);}
function layoutRelay(comp,folder){
 canvas(comp,PAPER);var S=[[530,660,880,700],[305,1215,430,330],[755,1215,430,330]];
 var F=D+'var e1=ease(time,2.1,2.5,0,1),e2=ease(time,3.5,3.9,0,1),on=linear(time,0.8,1.1,0,1);function A(i){return i==0?(1-e1):(i==1?e1*(1-e2):e2);}';
 for(var i=0;i<3;i++){var x=S[i][0],y=S[i][1],w=S[i][2],h=S[i][3],t0=0.2+i*0.12,SC=F+'var a=A('+i+')*on;[100+3*a,100+3*a]';
  var bk=rect(comp,"back "+i,w,h,PAPER,16,null);bk[0].property("Position").setValue([x,y]);softShadow(bk[0],40,50,14);bk[0].property("Scale").expression=SC;fade(bk[0],t0,t0+0.3);
  var ph=photo(comp,folder,"image"+(i+1)+".png","@image"+(i+1),w,h,x,y,16);ph[1].property("Scale").expression=SC;
  ph[0].property("Scale").expression=F+'var a=A('+i+')*on;var k=Math.max('+w+'/width,'+h+'/height)*(100+3*a);[k,k]';fade(ph[0],t0,t0+0.3);
  var bc=ph[0].property("ADBE Effect Parade").addProperty("ADBE Brightness & Contrast 2");bc.property("ADBE Brightness & Contrast 2-0001").expression=F+'-55*(1-A('+i+'))*on';
  var fr=rect(comp,"focus "+i,w+14,h+14,null,20,[BLUE,5]);fr[0].property("Position").setValue([x,y]);fr[0].property("Scale").expression=SC;fr[0].property("Opacity").expression=F+'A('+i+')*on*100';
  var cp=tx(comp,"cap"+(i+1),30,MUTE,MED,x-w/2,y+h/2+40,w,"left");cp.property("Opacity").expression=F+'(40+60*A('+i+')*on)*linear(time,'+(t0+0.3)+','+(t0+0.5)+',0,1)';}}
function gridHero(comp,folder){
 canvas(comp,PAPER);
 var G=D+'var h=Math.min(Math.max(Math.round(d.hero||1),1),4)-1;var t=ease(time,1.2,2.0,0,1)*(1-ease(time,3.6,4.3,0,1));function GR(i){return [540+(i%2?245:-245),960+(i<2?-245:245),470,470];}function HR(i){if(i==h)return [540,720,960,720];var k=i<h?i:i-1;return [540+(k-1)*320,1290,300,220];}function GEO(i){var a=GR(i),b=HR(i);return [a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t,a[2]+(b[2]-a[2])*t,a[3]+(b[3]-a[3])*t];}';
 for(var i=0;i<4;i++){var ph=photo(comp,folder,"image"+(i+1)+".png","@image"+(i+1),470,470,540,960,16);
  grp(ph[1]).property("ADBE Vector Shape - Rect").property("Size").expression=G+'var g=GEO('+i+');[g[2],g[3]]';ph[1].property("Position").expression=G+'var g=GEO('+i+');[g[0],g[1]]';
  ph[0].property("Position").expression=G+'var g=GEO('+i+');[g[0],g[1]]';ph[0].property("Scale").expression=G+'var g=GEO('+i+');var k=Math.max(g[2]/width,g[3]/height)*100;[k,k]';fade(ph[0],0.2+i*0.1,0.5+i*0.1);
  var cp=tx(comp,"cap"+(i+1),26,PAPER,BOLD,0,0,400,"left");cp.property("Position").expression=G+'var g=GEO('+i+');[g[0]-g[2]/2+34,g[1]+g[3]/2-38]';fade(cp,0.6,0.8);
  var cb=block(comp,"cap"+(i+1)+" chip",["@cap"+(i+1)],[14,8],INK,null,8);under(cb,cp);follow(cb,cp,0.55);}}
function echoBed(comp,folder){
 canvas(comp,CHAR);var it=app.project.importFile(new ImportOptions(new File(folder.fsName+"/image.png")));
 var bg=comp.layers.add(it);bg.name="@image bed";bg.property("Scale").expression='var k=Math.max(1080/width,1920/height)*125;[k,k]';bg.property("Position").setValue([540,960]);
 var bl=bg.property("ADBE Effect Parade").addProperty("ADBE Gaussian Blur 2");bl.property("ADBE Gaussian Blur 2-0001").setValue(70);try{bl.property("ADBE Gaussian Blur 2-0003").setValue(1);}catch(e){}
 var bc=bg.property("ADBE Effect Parade").addProperty("ADBE Brightness & Contrast 2");bc.property("ADBE Brightness & Contrast 2-0001").setValue(-60);fade(bg,0,0.3);
 var fg=comp.layers.add(it);fg.name="@image";fg.property("Scale").expression='var k=Math.min(820/width,900/height)*100*(1+0.03*clamp((time-0.5)/4,0,1));[k,k]';var fp=fg.property("Position");fp.setValueAtTime(0.2,[540,840]);fp.setValueAtTime(0.65,[540,760]);bez(fp,85,40);fade(fg,0.2,0.45);
 var bd=rect(comp,"border",10,10,PAPER,22,null);bd[0].moveAfter(fg);bd[0].property("Position").setValue([0,0]);var br=grp(bd[0]).property("ADBE Vector Shape - Rect");
 br.property("Size").expression='var L=thisComp.layer("@image");var k=L.scale[0]/100;[L.width*k+28,L.height*k+28]';br.property("Position").expression='thisComp.layer("@image").position';softShadow(bd[0],60,70,20);follow(bd[0],fg);
 var ti=tx(comp,"title",76,PAPER,HV,MX+40,1340,900,"left");lift(ti,0.6,16,0.45);var so=tx(comp,"source",30,[0.75,0.76,0.8],MED,MX+40,1420,900,"left");fade(so,0.85,1.1);}
function mapPin(comp,name,color){var s=comp.layers.addShape();s.name=name;var c=s.property("Contents");
 var g1=c.addProperty("ADBE Vector Group").property("Contents");g1.addProperty("ADBE Vector Shape - Ellipse");g1.addProperty("ADBE Vector Shape - Group");g1.addProperty("ADBE Vector Graphic - Fill");
 var g2=c.addProperty("ADBE Vector Group").property("Contents");g2.addProperty("ADBE Vector Shape - Ellipse");g2.addProperty("ADBE Vector Graphic - Fill");
 var A=c.property(1).property("Contents");A.property(1).property("Size").setValue([46,46]);A.property(1).property("Position").setValue([0,-48]);var sh=new Shape();sh.vertices=[[-17,-38],[17,-38],[0,0]];sh.closed=true;A.property(2).property("Path").setValue(sh);A.property(3).property("Color").setValue(color);
 var B=c.property(2).property("Contents");B.property(1).property("Size").setValue([16,16]);B.property(1).property("Position").setValue([0,-48]);B.property(2).property("Color").setValue(PAPER);softShadow(s,40,14,5);return s;}
function routePin(comp,folder){
 var it=app.project.importFile(new ImportOptions(new File(folder.fsName+"/map.png")));var m=comp.layers.add(it);m.name="@map";m.property("Scale").expression='var k=Math.max(1080/width,1920/height)*100;[k,k]';m.property("Position").setValue([540,960]);
 var PP=PL("@map");
 var LEG=[["p1","p2",0.6,1.5],["p2","p3",2.0,2.9]];
 for(var k=0;k<2;k++){var a=LEG[k][0],b=LEG[k][1];var rt=lineShape(comp,"route "+(k+1),RED,6);
  rt[1].expression=PP+'var a=P(d.'+a+'_x,d.'+a+'_y),b=P(d.'+b+'_x,d.'+b+'_y);var dx=b[0]-a[0],dy=b[1]-a[1],o=[-dy*0.22,dx*0.22];createPath([a,b],[[0,0],[-dx/3+o[0],-dy/3+o[1]]],[[dx/3+o[0],dy/3+o[1]],[0,0]],false)';
  trimIn(rt[0],LEG[k][2],LEG[k][3]);dashes(rt[0],18,12);rt[0].property("Opacity").expression=D+'d.'+b+'_name?100:0';}
 var PTS=[["p1",INK,0.3],["p2",RED,1.65],["p3",RED,3.05]];
 for(var i=0;i<3;i++){var f=PTS[i][0],t0=PTS[i][2];var pn=mapPin(comp,f+" pin",PTS[i][1]);
  pn.property("Position").expression=PP+'var p=P(d.'+f+'_x,d.'+f+'_y);var t=ease(time,'+t0+','+(t0+0.25)+',0,1);[p[0],p[1]-50*(1-t)]';
  pn.property("Scale").expression='var u=time-'+(t0+0.25)+';var q=(u>0&&u<0.14)?Math.sin(u/0.14*Math.PI):0;[100+18*q,100-18*q]';pn.property("Opacity").expression=D+'(d.'+f+'_name&&time>='+t0+')?100:0';
  var lb=tx(comp,f+"_name",34,INK,BOLD,0,0,420,"left");// Labels flip to the pin's left near the right edge so names never run under the side buttons.
  lb.property("Position").expression=PP+'var p=P(d.'+f+'_x,d.'+f+'_y);[p[0]>600?p[0]-44:p[0]+44,p[1]-48]';lb.property("Anchor Point").expression=PP+'var p=P(d.'+f+'_x,d.'+f+'_y);var r=sourceRectAtTime(time,false);p[0]>600?[r.left+r.width,r.top+r.height/2]:[r.left,r.top+r.height/2]';fade(lb,t0+0.3,t0+0.5);
  var lc=block(comp,f+" chip",["@"+f+"_name"],[18,10],PAPER,null,10);under(lc,lb);follow(lc,lb);softShadow(lc,30,30,8);}}
function shapeWipe(comp){
 // Slanted blocks stack in fast; once the top one covers the frame the lower ones drop out, so only the dark block leaves and reveals the next shot.
 var TONES={ink:[[0.84,0.85,0.87],[0.55,0.56,0.58],CHAR]};for(var k in THEMES)if(k!="ink")TONES[k]=[shade(THEMES[k],0.55),THEMES[k],shade(THEMES[k],-0.45)];
 for(var k in TONES){for(var j=0;j<3;j++){var t0=0.05+j*0.07;var s=filledPath(comp,"wipe "+k+" "+j,TONES[k][j]);
  s[1].expression=D+'var dir=String(d.direction||"left");var sk=150;var a=ease(time,'+t0+','+(t0+0.3)+',0,1),b='+(j==2?'ease(time,0.56,0.86,0,1)':'0')+';var V=(dir=="up"||dir=="down"),MR=(dir=="right"||dir=="up");var L=V?1920:1080,C=V?1080:1920,Wd=L+600;var A=-sk-20,B=L+sk+20;var r=A+(B-A)*a+(Wd+20)*b,l=r-Wd;'+
   'function M(u,c){var u2=MR?L-u:u;return V?[c,u2]:[u2,c];}createPath([M(l+sk,-40),M(r+sk,-40),M(r-sk,C+40),M(l-sk,C+40)],[],[],true)';
  s[0].property("Opacity").expression=D+'var c=String(d.color||"ink");if(!({ink:1,blue:1,red:1,violet:1,teal:1,orange:1})[c])c="ink";(c=="'+k+'"'+(j<2?'&&time<0.5':'')+')?100:0';}}}
function colorSlam(comp,folder){
 themeSolids(comp,"blue");
 var l1=tx(comp,"line1",120,PAPER,HV,MX+40,620,920,"left");var l2=tx(comp,"line2",120,PAPER,HV,MX+40,770,920,"left");var IMG=D+'var up=(d._images&&d._images.indexOf("image")>=0)?0:260;';l1.property("Position").expression=IMG+'[value[0],value[1]+up]';l2.property("Position").expression=IMG+'[value[0],value[1]+up]';
 var s1=l1.property("Scale");s1.setValueAtTime(0.05,[108,108]);s1.setValueAtTime(0.3,[100,100]);bez(s1,85,40);hold(l1.property("Opacity"),0.05,0,100);
 var s2=l2.property("Scale");s2.setValueAtTime(0.15,[108,108]);s2.setValueAtTime(0.4,[100,100]);bez(s2,85,40);hold(l2.property("Opacity"),0.15,0,100);
 var kk=tx(comp,"kicker",28,PAPER,BOLD,MX+40,880,900,"left",200);kk.property("Opacity").expression='linear(time,0.4,0.6,0,75)';kk.property("Position").expression=IMG+'[value[0],value[1]+up]';
 var rg=rigNull(comp,"card rig");var VIS=D+'(d._images&&d._images.indexOf("image")>=0)?linear(time,0.35,0.5,0,100):0';
 var bk=rect(comp,"card",900,720,PAPER,24,null);bk[0].property("Position").setValue([540,1390]);softShadow(bk[0],45,70,22);bk[0].property("Opacity").expression=VIS;
 var ph=photo(comp,folder,"image.png","@image",860,680,540,1390,14);ph[0].property("Opacity").expression=VIS;
 bk[0].parent=rg;ph[0].parent=rg;ph[1].parent=rg;var rp=rg.property("Position");rp.setValueAtTime(0.35,[0,300]);rp.setValueAtTime(0.8,[0,0]);bez(rp,85,40);}
function followButton(comp){
 var Y=1380,TC=1.4;
 var hn=tx(comp,"hint",32,INK,BOLD,540,Y-120,800);var hb=block(comp,"hint chip",["@hint"],[28,14],PAPER,null,30);under(hb,hn);follow(hb,hn);softShadow(hb,35,30,8);fade(hn,0.2,0.4);
 var lb=tx(comp,"label",50,PAPER,HV,540,Y,600);srcE(lb,'String(d.label||"关注")');var lp=block(comp,"label pill",["@label"],[60,24],RED,null,44);under(lp,lb);follow(lp,lb);softShadow(lp,35,30,8);
 var ls=lb.property("Scale");ls.setValueAtTime(0.3,[70,70]);ls.setValueAtTime(0.55,[105,105]);ls.setValueAtTime(0.7,[100,100]);press(lb,TC);fade(lb,0.3,0.4);before(lb,TC+0.1);
 var dn=tx(comp,"done",50,INK,HV,540,Y,600);srcE(dn,'String(d.done||"已关注")');var dp=block(comp,"done pill",["@done"],[60,24],[0.92,0.92,0.94],null,44);under(dp,dn);follow(dp,dn);after(dn,TC+0.1);
 var ck=dot(comp,"check dot",72,RED);ck.property("Position").expression=unionExpr(["@done"],[60,24])+'[x1+P[0]+56,(y0+y1)/2]';var cs=ck.property("Scale");cs.setValueAtTime(TC+0.2,[0,0]);cs.setValueAtTime(TC+0.4,[112,112]);cs.setValueAtTime(TC+0.5,[100,100]);
 var cm=lineShape(comp,"check mark",PAPER,6);cm[1].expression=unionExpr(["@done"],[60,24])+'var x=x1+P[0]+56,y=(y0+y1)/2;createPath([[x-15,y],[x-4,y+11],[x+16,y-11]],[],[],false)';trimIn(cm[0],TC+0.35,TC+0.55);
 cursor(comp,880,1820,560,Y+12,TC);exitAll(comp);}
function followCardX(comp,folder){
 var TC=1.6,rg=rigNull(comp,"card rig"),kids=[],DK=[0.09,0.1,0.12];
 var cd=rect(comp,"card",900,560,DK,28,null);cd[0].property("Position").setValue([540,1180]);softShadow(cd[0],50,70,22);kids.push(cd[0]);
 var bn=rect(comp,"banner",900,190,[0.11,0.45,0.85],28,null);bn[0].property("Position").setValue([540,995]);kids.push(bn[0]);
 var bs=rect(comp,"banner base",900,40,[0.11,0.45,0.85],0,null);bs[0].property("Position").setValue([540,1070]);kids.push(bs[0]);
 var ar=dot(comp,"avatar ring",156,DK);ar.property("Position").setValue([200,1090]);kids.push(ar);
 var ph=photo(comp,folder,"avatar.png","@avatar",140,140,200,1090,70);kids.push(ph[0]);kids.push(ph[1]);ph[0].property("Opacity").expression=D+'(d._images&&d._images.indexOf("avatar")>=0)?100:0';
 var av=dot(comp,"avatar blank",140,[0.3,0.32,0.36]);av.property("Position").setValue([200,1090]);av.property("Opacity").expression=D+'(d._images&&d._images.indexOf("avatar")>=0)?0:100';kids.push(av);
 var ai=tx(comp,"initial",60,PAPER,HV,200,1090,120);srcE(ai,'String(d.name||"").charAt(0)');ai.property("Opacity").expression=D+'(d._images&&d._images.indexOf("avatar")>=0)?0:100';kids.push(ai);
 var nm=tx(comp,"name",46,PAPER,HV,130,1210,560,"left");var hd=tx(comp,"handle",28,[0.55,0.57,0.62],MED,130,1262,560,"left");var bi=tx(comp,"bio",30,[0.86,0.87,0.9],MED,130,1325,720,"left");
 var st=tx(comp,"stats",28,[0.55,0.57,0.62],MED,130,1382,720,"left");srcE(st,'(d.following?d.following+" 正在关注      ":"")+(d.followers?d.followers+" 关注者":"")');kids.push(nm,hd,bi,st);
 var bt=tx(comp,"button",32,INK,HV,850,1152,300,"left");rightAnchor(bt);srcE(bt,'String(d.button||"关注")');press(bt,TC);before(bt,TC+0.1);kids.push(bt);
 var dn=tx(comp,"done",32,PAPER,HV,850,1152,300,"left");rightAnchor(dn);srcE(dn,'String(d.done||"已关注")');after(dn,TC+0.1);kids.push(dn);
 for(var i=0;i<kids.length;i++)kids[i].parent=rg;
 var bp=block(comp,"button pill",["@button"],[30,14],PAPER,null,30);under(bp,bt);follow(bp,bt);var dp=block(comp,"done pill",["@done"],[30,14],null,[[0.4,0.42,0.46],2],30);under(dp,dn);follow(dp,dn);
 var rp=rg.property("Position");rp.setValueAtTime(0.15,[0,140]);rp.setValueAtTime(0.6,[0,0]);bez(rp,85,40);
 var HAS='(d._images&&d._images.indexOf("avatar")>=0)';ph[0].property("Opacity").expression=D+'('+HAS+'?100:0)*linear(time,0.15,0.35,0,1)';av.property("Opacity").expression=D+'('+HAS+'?0:100)*linear(time,0.15,0.35,0,1)';ai.property("Opacity").expression=D+'('+HAS+'?0:100)*linear(time,0.15,0.35,0,1)';
 var FADE=[cd[0],bn[0],bs[0],ar,nm,hd,bi,st];for(var i=0;i<FADE.length;i++)fade(FADE[i],0.15,0.35);
 cursor(comp,900,1800,800,1170,TC);exitAll(comp);}
function followCardDy(comp,folder){
 var TC=1.6,rg=rigNull(comp,"card rig"),kids=[];
 var cd=rect(comp,"card",900,720,PAPER,28,null);cd[0].property("Position").setValue([540,1100]);softShadow(cd[0],45,70,22);kids.push(cd[0]);
 var tp=rect(comp,"top",900,300,[0.77,0.86,0.97],28,null);tp[0].property("Position").setValue([540,890]);kids.push(tp[0]);var tb=rect(comp,"top base",900,40,[0.77,0.86,0.97],0,null);tb[0].property("Position").setValue([540,1020]);kids.push(tb[0]);
 var ar=dot(comp,"avatar ring",166,PAPER);ar.property("Position").setValue([210,890]);kids.push(ar);
 var ph=photo(comp,folder,"avatar.png","@avatar",150,150,210,890,75);kids.push(ph[0]);kids.push(ph[1]);
 var av=dot(comp,"avatar blank",150,[0.62,0.66,0.74]);av.property("Position").setValue([210,890]);kids.push(av);
 var ai=tx(comp,"initial",64,PAPER,HV,210,890,120);srcE(ai,'String(d.name||"").charAt(0)');kids.push(ai);
 var nm=tx(comp,"name",52,INK,HV,320,860,560,"left");var ac=tx(comp,"account",28,[0.35,0.38,0.45],MED,320,922,560,"left");kids.push(nm,ac);
 var PAIRS=[["likes","获赞"],["following","关注"],["fans","粉丝"]];var prev=null;
 for(var i=0;i<3;i++){var v=tx(comp,PAIRS[i][0],38,INK,HV,130,1095,300,"left");var l=tx(comp,PAIRS[i][0]+"l",28,MUTE,MED,130,1098,200,"left");l.name="@"+PAIRS[i][0]+" label";srcE(l,'d.'+PAIRS[i][0]+'?"'+PAIRS[i][1]+'":""');
  if(prev)v.property("Position").expression='var L=thisComp.layer("'+prev+'");var r=L.sourceRectAtTime(time,false);var p=L.toComp([r.left+r.width,r.top+r.height/2]);var q=thisLayer.parent?thisLayer.parent.toWorld([0,0]):[0,0];[p[0]+(r.width>0?40:0)-q[0],1095]';
  l.property("Position").expression='var L=thisComp.layer("@'+PAIRS[i][0]+'");var r=L.sourceRectAtTime(time,false);var p=L.toComp([r.left+r.width,r.top+r.height/2]);var q=thisLayer.parent?thisLayer.parent.toWorld([0,0]):[0,0];[p[0]+(r.width>0?10:0)-q[0],1098]';
  prev="@"+PAIRS[i][0]+" label";kids.push(v,l);}
 var b1=tx(comp,"bio",32,[0.28,0.29,0.33],MED,130,1175,740,"left");var b2=tx(comp,"bio2",32,[0.28,0.29,0.33],MED,130,1225,740,"left");kids.push(b1,b2);
 var rb=rect(comp,"button",820,88,RED,44,null);rb[0].property("Position").setValue([540,1350]);press(rb[0],TC);before(rb[0],TC+0.1);kids.push(rb[0]);
 var lb=tx(comp,"button",36,PAPER,HV,540,1350,600);srcE(lb,'String(d.button||"+ 关注")');before(lb,TC+0.1);kids.push(lb);
 var gb=rect(comp,"done bg",820,88,[0.93,0.93,0.95],44,null);gb[0].property("Position").setValue([540,1350]);after(gb[0],TC+0.1);kids.push(gb[0]);
 var dn=tx(comp,"done",36,INK,BOLD,540,1350,600);srcE(dn,'String(d.done||"已关注")');after(dn,TC+0.1);kids.push(dn);
 for(var i=0;i<kids.length;i++)kids[i].parent=rg;
 var HAS='(d._images&&d._images.indexOf("avatar")>=0)';ph[0].property("Opacity").expression=D+'('+HAS+'?100:0)*linear(time,0.15,0.35,0,1)';av.property("Opacity").expression=D+'('+HAS+'?0:100)*linear(time,0.15,0.35,0,1)';ai.property("Opacity").expression=D+'('+HAS+'?0:100)*linear(time,0.15,0.35,0,1)';
 var FADE=[cd[0],tp[0],tb[0],ar,nm,ac,b1,b2];for(var i=0;i<FADE.length;i++)fade(FADE[i],0.15,0.35);
 var rp=rg.property("Position");rp.setValueAtTime(0.15,[0,140]);rp.setValueAtTime(0.6,[0,0]);bez(rp,85,40);
 cursor(comp,900,1830,560,1365,TC);exitAll(comp);}
// ---- product workbench: hero, selling points, specs, price, material, steps, trust, purchase ----
function HAS(n){return '(d._images&&d._images.indexOf("'+n+'")>=0)';}
function BEATS(d0,step){return 'var bt=String(d.beats||"").split(/[,，]/);function BT(i){var v=parseFloat(bt[i]);return isNaN(v)?'+d0+'+i*'+step+':v;}';}
function ROWS(f){return 'var RW=String(d["'+f+'"]||"").split(/[;；]/),R=[];for(var q=0;q<RW.length;q++){var z=RW[q].split("|");if(z[0]&&z[0].replace(/\\s/g,""))R.push(z);}';}
function cardFollow(name){var f=comp_layer(name+" frame");if(f)f.property("Opacity").expression='thisComp.layer("'+name+'").opacity';}
var _COMP=null;function comp_layer(n){try{return _COMP.layer(n);}catch(e){return null;}}
function checkIcon(comp,name,x,y,color,size){var c=dot(comp,name,size,color);c.property("Position").setValue([x,y]);var m=lineShape(comp,name+" mark",PAPER,Math.max(4,size/9));var s=size/44;
 staticPath(m[1],[[x-10*s,y],[x-3*s,y+8*s],[x+11*s,y-8*s]]);return [c,m[0]];}
function crossIcon(comp,name,x,y,color,size){var s=size/2.6;var a=lineShape(comp,name,color,6);var sh=new Shape();sh.vertices=[[x-s,y-s],[x+s,y+s]];sh.closed=false;a[1].setValue(sh);
 var b=lineShape(comp,name+" b",color,6);var sh2=new Shape();sh2.vertices=[[x+s,y-s],[x-s,y+s]];sh2.closed=false;b[1].setValue(sh2);return [a[0],b[0]];}
function star(comp,name,cx,cy,r,color){var s=filledPath(comp,name,color);var v=[];for(var i=0;i<10;i++){var a=-Math.PI/2+i*Math.PI/5,rr=i%2?r*0.45:r;v.push([cx+rr*Math.cos(a),cy+rr*Math.sin(a)]);}var sh=new Shape();sh.vertices=v;sh.closed=true;s[1].setValue(sh);return s[0];}

function productHero(comp,folder){_COMP=comp;
 canvas(comp,CANVAS);var glow=dot(comp,"glow",900,PAPER);glow.property("Position").setValue([W/2,690]);glow.property("Opacity").setValue(70);fade(glow,0,0.4);
 var m=card(comp,folder,"product.png","@product",820,760,W/2,690);cardFollow("@product");var mp=m.property("Position");mp.setValueAtTime(0.2,[W/2,810]);mp.setValueAtTime(0.75,[W/2,690]);bez(mp,85,40);fade(m,0.2,0.45);
 // The sweep is matted by a copy of the picture, so the light only crosses the product card.
 var sw=rect(comp,"sweep",140,1600,PAPER,0,null);sw[0].property("Rotation").setValue(18);var sp=sw[0].property("Position");sp.setValueAtTime(0.95,[W/2-700,690]);sp.setValueAtTime(1.6,[W/2+700,690]);bez(sp,60,60);sw[0].property("Opacity").setValue(55);
 var mt=comp.layers.add(m.source);mt.name="@product sweep matte";mt.moveBefore(sw[0]);mt.property("Scale").expression='thisComp.layer("@product").scale';mt.property("Position").expression='thisComp.layer("@product").position';sw[0].setTrackMatte(mt,TrackMatteType.ALPHA);
 var tg=tx(comp,"tag",32,PAPER,BOLD,W/2,1150,400);var tc=block(comp,"tag chip",["@tag"],[22,10],RED,null,10);under(tc,tg);follow(tc,tg);fade(tg,1.0,1.2);
 var nm=tx(comp,"name",84,INK,HV,W/2,1245,692);lift(nm,0.8,16,0.45);var sb=tx(comp,"sub",40,MUTE,MED,W/2,1330,692);lift(sb,1.0,10,0.4);}
function productAngles(comp,folder){_COMP=comp;
 canvas(comp,CANVAS);var SEQ=D+'var I=d._images||[],n=0;for(var q=1;q<=4;q++)if(I.indexOf("img"+q)>=0)n=q;n=Math.max(n,1);var e=(d._duration_ms||6000)/1000,seg=(e-0.6)/n;function T(i){return 0.3+i*seg;}';
 for(var i=0;i<4;i++){var nm="@img"+(i+1);var m=card(comp,folder,"img"+(i+1)+".png",nm,860,960,W/2,760);cardFollow(nm);
  m.property("Position").expression=SEQ+'var a=ease(time,T('+i+'),T('+i+')+0.4,0,1),b='+i+'<n-1?ease(time,T('+(i+1)+'),T('+(i+1)+')+0.4,0,1):0;[540+700*(1-a)-700*b,760]';
  m.property("Opacity").expression=SEQ+'('+i+'<n)?100*ease(time,T('+i+'),T('+i+')+0.3,0,1)*(1-('+i+'<n-1?ease(time,T('+(i+1)+'),T('+(i+1)+')+0.3,0,1):0)):0';
  var lb=tx(comp,"a"+(i+1),44,INK,BOLD,W/2,1330,692);lb.property("Opacity").expression='thisComp.layer("'+nm+'").opacity';
  var pd=dot(comp,"pip "+i,18,LINE);pd.property("Position").expression=SEQ+'[540+('+i+'-(n-1)/2)*44,1420]';pd.property("Opacity").expression=SEQ+'('+i+'<n)?100:0';}
 var on=dot(comp,"pip on",22,BLUE);on.property("Position").expression=SEQ+'var j=0;for(var q=0;q<n;q++)if(time>=T(q))j=q;[540+(j-(n-1)/2)*44,1420]';fade(on,0.3,0.5);}
function sellingPoints(comp,folder){_COMP=comp;
 canvas(comp,PAPER);var m=card(comp,folder,"product.png","@product",700,540,W/2,600);cardFollow("@product");m.property("Opacity").expression=D+'('+HAS("product")+')?linear(time,0.1,0.4,0,100):0';
 var UP=D+'var up=('+HAS("product")+')?0:300;';
 for(var i=0;i<3;i++){var y=1010+i*160,BTi=D+BEATS(0.5,0.5)+'var t0=BT('+i+');';
  var VIS=BTi+'d["t'+(i+1)+'"]?linear(time,t0,t0+0.25,0,100):0',POS=function(x,yy){return UP+BEATS(0.5,0.5)+'var t0=BT('+i+');['+x+','+yy+'-up+16*(1-ease(time,t0,t0+0.35,0,1))]';};
  var nd=dot(comp,"num dot "+i,72,TEAL);nd.property("Position").expression=POS(150,y);nd.property("Opacity").expression=VIS;
  var nt=tx(comp,"n"+i,36,PAPER,HV,0,0,60);nt.property("Source Text").expression='"'+(i+1)+'"';nt.property("Position").expression=POS(150,y);nt.property("Opacity").expression=VIS;
  var tt=tx(comp,"t"+(i+1),46,INK,HV,0,0,640,"left");tt.property("Position").expression=POS(214,y-22);tt.property("Opacity").expression=VIS;
  var dd=tx(comp,"d"+(i+1),32,MUTE,MED,0,0,640,"left");dd.property("Position").expression=POS(214,y+28);dd.property("Opacity").expression=VIS;
  var bk=block(comp,"row "+i,["num dot "+i,"@t"+(i+1),"@d"+(i+1)],[26,20],[0.96,0.97,0.975],null,18);bk.moveBefore(comp.layer("canvas"));follow(bk,tt);}}
function checkList(comp){_COMP=comp;
 var ti=tx(comp,"title",56,INK,HV,MX+60,1000,742,"left");lift(ti,0.25,12,0.4);
 for(var i=0;i<5;i++){var y=1090+i*80,f="i"+(i+1),A=D+BEATS(0.6,0.45)+'var t0=BT('+i+');';
  var c=checkIcon(comp,"check "+i,170,y,TEAL,44);c[0].property("Opacity").expression=A+'d["'+f+'"]?linear(time,t0,t0+0.15,0,100):0';var cs=c[0].property("Scale");c[0].property("Scale").expression=A+'var s=100*(1+0.25*Math.sin(Math.PI*clamp((time-t0)/0.25,0,1)));[s,s]';
  var tp=c[1].property("Contents").addProperty("ADBE Vector Filter - Trim");tp.property("End").expression=A+'linear(time,t0+0.08,t0+0.3,0,100)';c[1].property("Opacity").expression=A+'d["'+f+'"]?100:0';
  var it=tx(comp,f,42,INK,BOLD,214,y,660,"left");it.property("Opacity").expression=A+'d["'+f+'"]?linear(time,t0+0.05,t0+0.25,0,100):0';}
 var N=["@title","@i1","@i2","@i3","@i4","@i5","check 0"];var b=block(comp,"panel",N,[44,40],PAPER,null,24);b.moveToEnd();softShadow(b,45,60,16);originAt(b,N,[44,40],"left");grow(b,0.1,0.4,[96,96]);fade(b,0.1,0.3);exitAll(comp);}
function specTable(comp,folder){_COMP=comp;
 canvas(comp,PAPER);var ti=tx(comp,"title",60,INK,HV,MX+40,380,880,"left");lift(ti,0.15,12,0.4);
 var m=card(comp,folder,"product.png","@product",820,470,W/2,705);cardFollow("@product");m.property("Opacity").expression=D+'('+HAS("product")+')?linear(time,0.2,0.5,0,100):0';
 var G=D+ROWS("rows")+'var y0=('+HAS("product")+')?1000:600;var h=Math.round(d.highlight||0)-1;';
 for(var i=0;i<6;i++){var A=G+'var y=y0+'+i*96+',t0=0.5+'+i*0.15+',up=12*(1-ease(time,t0,t0+0.3,0,1));',VIS=G+'var t0=0.5+'+i*0.15+';R['+i+']?linear(time,t0,t0+0.25,0,100):0';
  var hb=rect(comp,"hl "+i,820,80,[0.9,0.97,0.95],14,null);hb[0].property("Position").expression=A+'[510,y+up]';hb[0].property("Opacity").expression=G+'('+i+'==h&&R['+i+'])?linear(time,1.6,1.8,0,100):0';
  var nm=tx(comp,"k"+i,40,MUTE,MED,0,0,400,"left");srcE(nm,ROWS("rows")+'R['+i+']?R['+i+'][0]:""');nm.property("Position").expression=A+'[140,y+up]';nm.property("Opacity").expression=VIS;
  for(var k=0;k<2;k++){var vl=tx(comp,"v"+i+(k?"h":""),46,k?TEAL:INK,BOLD,0,0,420,"left");rightAnchor(vl);srcE(vl,ROWS("rows")+'R['+i+']?(R['+i+'][1]||""):""');vl.property("Position").expression=A+'[880,y+up]';
   vl.property("Opacity").expression=G+'var t0=0.5+'+i*0.15+';var on=('+i+'==h)?linear(time,1.6,1.8,0,1):0;R['+i+']?linear(time,t0,t0+0.25,0,100)*('+(k?'on':'1-on')+'):0';}
  var ln=lineShape(comp,"rule "+i,LINE,2);ln[1].expression=A+'createPath([[120,y+48+up],[900,y+48+up]],[],[],false)';ln[0].property("Opacity").expression=VIS;}}
function compareTable(comp){_COMP=comp;
 canvas(comp,PAPER);var ti=tx(comp,"title",60,INK,HV,MX+40,380,880,"left");lift(ti,0.15,12,0.4);
 var XS=[560,760];var col=rect(comp,"ours column",180,10,[0.9,0.97,0.95],22,null);col[1].property("Size").expression=D+ROWS("rows")+'[200,130*Math.max(R.length,1)+120]';col[1].property("Position").expression=D+ROWS("rows")+'[560,580-60+(130*Math.max(R.length,1)+120)/2]';col[0].property("Position").setValue([0,0]);fade(col[0],0.3,0.6);
 var oh=tx(comp,"ours",44,TEAL,HV,560,580,200);srcE(oh,'String(d.ours||"本品")');fade(oh,0.3,0.5);var th=tx(comp,"other",44,MUTE,BOLD,760,580,200);fade(th,0.3,0.5);
 for(var i=0;i<6;i++){var y=700+i*130,t0=0.6+i*0.18,G=D+ROWS("rows"),VIS=G+'R['+i+']?linear(time,'+t0+','+(t0+0.25)+',0,100):0';
  var it=tx(comp,"item"+i,44,INK,BOLD,120,y,380,"left");srcE(it,ROWS("rows")+'R['+i+']?R['+i+'][0]:""');it.property("Opacity").expression=VIS;
  var ln=lineShape(comp,"rule "+i,LINE,2);staticPath(ln[1],[[110,y+65],[870,y+65]]);ln[0].property("Opacity").expression=VIS;
  for(var c=0;c<2;c++){var x=XS[c],j=c+1,V=G+'var v=R['+i+']?String(R['+i+']['+j+']||"").replace(/\\s/g,""):"";';
   var vt=tx(comp,"cell"+i+"_"+c,42,c?MUTE:INK,BOLD,x,y,190);srcE(vt,ROWS("rows")+'var v=R['+i+']?String(R['+i+']['+j+']||""):"";(/^[✓√✔✗×✘xX]$/.test(v.replace(/\\s/g,"")))?"":v');vt.property("Opacity").expression=VIS;
   var ck=checkIcon(comp,"yes "+i+"_"+c,x,y,c?MUTE:TEAL,52);var YES=V+'(/^[✓√✔]$/.test(v))?(R['+i+']?linear(time,'+t0+','+(t0+0.25)+',0,100):0):0';ck[0].property("Opacity").expression=YES;ck[1].property("Opacity").expression=YES;
   var cr=crossIcon(comp,"no "+i+"_"+c,x,y,c?RED:MUTE,46);var NO=V+'(/^[✗×✘xX]$/.test(v))?(R['+i+']?linear(time,'+t0+','+(t0+0.25)+',0,100):0):0';cr[0].property("Opacity").expression=NO;cr[1].property("Opacity").expression=NO;}}}
function dimensionMark(comp,folder){_COMP=comp;
 canvas(comp,PAPER);var m=card(comp,folder,"product.png","@product",780,700,470,740);cardFollow("@product");fade(m,0.1,0.4);
 var B=PL("@product")+'var a=P(d.bx0||0,d.by0||0),b=P(d.bx1||1,d.by1||1);var x0=a[0],y0=a[1],x1=b[0],y1=b[1];';
 var wl=lineShape(comp,"width line",INK,3);wl[1].expression=B+'var y=y1+56;createPath([[x0,y-14],[x0,y],[x1,y],[x1,y-14]],[],[],false)';trimIn(wl[0],0.7,1.2);
 var hl=lineShape(comp,"height line",INK,3);hl[1].expression=B+'var x=x1+50;createPath([[x-14,y0],[x,y0],[x,y1],[x-14,y1]],[],[],false)';trimIn(hl[0],1.0,1.5);hl[0].property("Opacity").expression=D+'d.h_label?100:0';
 var wt=tx(comp,"w_label",40,INK,HV,0,0,360);wt.property("Position").expression=B+'[(x0+x1)/2,y1+56]';var wc=block(comp,"w chip",["@w_label"],[18,8],PAPER,[INK,2],10);under(wc,wt);follow(wc,wt);fade(wt,1.15,1.35);
 var ht=tx(comp,"h_label",40,INK,HV,0,0,240);ht.property("Position").expression=B+'[x1+50,(y0+y1)/2]';var hc=block(comp,"h chip",["@h_label"],[16,8],PAPER,[INK,2],10);under(hc,ht);follow(hc,ht);fade(ht,1.45,1.65);
 var dt=tx(comp,"d_label",34,PAPER,BOLD,0,0,300);dt.property("Position").expression=B+'[(x0+x1)/2,y0-46]';var dc=block(comp,"d chip",["@d_label"],[18,8],BLUE,null,10);under(dc,dt);follow(dc,dt);fade(dt,1.7,1.9);}
function priceDrop(comp){_COMP=comp;
 var lb=tx(comp,"label",40,MUTE,MED,MX+60,1060,740,"left");lift(lb,0.3,10,0.35);
 var og=tx(comp,"original",64,MUTE,HV,MX+60,1145,740,"left");lift(og,0.4,12,0.35);
 var st=lineShape(comp,"strike",RED,7);st[1].expression=unionExpr(["@original"],[0,0])+'var y=(y0+y1)/2;createPath([[x0-10,y],[x1+10,y]],[],[],false)';trimIn(st[0],0.75,0.95);
 var pr=tx(comp,"price",190,RED,HV,MX+60,1290,740,"left");var ps=pr.property("Scale");ps.setValueAtTime(1.05,[130,130]);ps.setValueAtTime(1.3,[100,100]);bez(ps,90,40);fade(pr,1.05,1.15);
 var sv=tx(comp,"saving",36,PAPER,BOLD,MX+80,1410,600,"left");var sc=block(comp,"saving chip",["@saving"],[20,10],RED,null,10);under(sc,sv);follow(sc,sv);var ss=sv.property("Scale");ss.setValueAtTime(1.45,[70,70]);ss.setValueAtTime(1.65,[100,100]);bez(ss,90,40);fade(sv,1.45,1.55);
 var N=["@label","@original","@price","@saving"];var b=block(comp,"panel",N,[50,40],PAPER,null,24);b.moveToEnd();softShadow(b,45,60,16);originAt(b,N,[50,40],"left");grow(b,0.15,0.45,[96,96]);fade(b,0.15,0.3);exitAll(comp);}
function dealTimer(comp){_COMP=comp;
 var ic=ring(comp,"clock",RED,6);ic[1].property("Size").setValue([54,54]);ic[0].property("Position").setValue([MX+90,1200]);fade(ic[0],0.3,0.45);
 var hand=lineShape(comp,"clock hand",RED,5);hand[1].expression='var c=['+(MX+90)+',1200],a=time*4;createPath([[c[0],c[1]],[c[0]+14*Math.sin(a),c[1]-14*Math.cos(a)]],[],[],false)';fade(hand[0],0.3,0.45);
 var lb=tx(comp,"label",48,INK,HV,MX+140,1200,620,"left");lift(lb,0.35,10,0.35);var en=tx(comp,"ends",38,MUTE,MED,MX+140,1270,620,"left");lift(en,0.5,8,0.35);
 var cd=tx(comp,"countdown",84,RED,HV,MX+60,1370,700,"left");srcE(cd,'var s=Math.max(Math.round(d.countdown||0)-Math.floor(time),0);function p(v){return (v<10?"0":"")+v;}d.countdown?p(Math.floor(s/3600))+":"+p(Math.floor(s%3600/60))+":"+p(s%60):""');fade(cd,0.7,0.9);
 var N=["clock","@label","@ends","@countdown"];var b=block(comp,"panel",N,[44,36],PAPER,null,24);b.moveToEnd();softShadow(b,45,60,16);originAt(b,N,[44,36],"left");grow(b,0.15,0.45,[96,96]);fade(b,0.15,0.3);
 var pulse=ic[0].property("Scale");ic[0].property("Scale").expression='var s=100+6*Math.max(0,Math.sin(time*6.283));[s,s]';exitAll(comp);}
function layerStack(comp){_COMP=comp;
 canvas(comp,PAPER);var ti=tx(comp,"title",60,INK,HV,MX+40,380,880,"left");lift(ti,0.15,12,0.4);
 var TINT=[[0.86,0.92,1],[0.86,0.96,0.94],[1,0.95,0.82],[0.93,0.9,1]],EDGE=[BLUE,TEAL,ORANGE,VIOLET];
 for(var i=0;i<4;i++){var G=D+ROWS("layers")+'var n=Math.max(R.length,1);var sp=ease(time,0.6,1.4,0,1);var y=(820+'+i*30+')+((600+'+i*190+')-(820+'+i*30+'))*sp;',VIS=D+ROWS("layers")+'R['+i+']?linear(time,'+(0.2+i*0.08)+','+(0.4+i*0.08)+',0,100):0';
  var sh=rect(comp,"slab shade "+i,420,100,EDGE[i],20,null);sh[0].property("Position").expression=G+'[300,y+12]';sh[0].property("Opacity").expression=D+ROWS("layers")+'(R['+i+']?linear(time,'+(0.2+i*0.08)+','+(0.4+i*0.08)+',0,1):0)*45';
  var sl=rect(comp,"slab "+i,420,100,TINT[i],20,[EDGE[i],3]);sl[0].property("Position").expression=G+'[300,y]';sl[0].property("Opacity").expression=VIS;
  var lk=lineShape(comp,"leader "+i,EDGE[i],3);lk[1].expression=G+'createPath([[515,y],[548,y]],[],[],false)';lk[0].property("Opacity").expression=D+ROWS("layers")+'R['+i+']?linear(time,1.4,1.6,0,100):0';
  var nm=tx(comp,"ln"+i,40,INK,BOLD,0,0,320,"left");srcE(nm,ROWS("layers")+'R['+i+']?R['+i+'][0]:""');nm.property("Position").expression=G+'[566,y-22]';nm.property("Opacity").expression=D+ROWS("layers")+'R['+i+']?linear(time,'+(1.4+i*0.12)+','+(1.6+i*0.12)+',0,100):0';
  var ds=tx(comp,"ld"+i,30,MUTE,MED,0,0,320,"left");srcE(ds,ROWS("layers")+'R['+i+']?(R['+i+'][1]||""):""');ds.property("Position").expression=G+'[566,y+24]';ds.property("Opacity").expression='thisComp.layer("@ln'+i+'").opacity';}}
function useSteps(comp,folder){_COMP=comp;
 canvas(comp,PAPER);var ti=tx(comp,"title",60,INK,HV,MX+40,380,880,"left");lift(ti,0.15,12,0.4);
 for(var i=0;i<3;i++){var y=600+i*300,A=D+BEATS(0.5,0.8)+'var t0=BT('+i+'),sl=40*(1-ease(time,t0,t0+0.4,0,1)),im=('+HAS("img"+(i+1))+');',VIS=A+'d["s'+(i+1)+'"]?linear(time,t0,t0+0.3,0,100):0';
  var nd=dot(comp,"step dot "+i,72,BLUE);nd.property("Position").expression=A+'[150+sl,'+y+']';nd.property("Opacity").expression=VIS;
  var nt=tx(comp,"n"+i,38,PAPER,HV,0,0,60);nt.property("Source Text").expression='"'+(i+1)+'"';nt.property("Position").expression=A+'[150+sl,'+y+']';nt.property("Opacity").expression=VIS;
  var ph=photo(comp,folder,"img"+(i+1)+".png","@img"+(i+1),240,180,330,y,16);ph[0].property("Position").expression=A+'[330+sl,'+y+']';ph[1].property("Position").expression=A+'[330+sl,'+y+']';ph[0].property("Opacity").expression=A+'im?linear(time,t0,t0+0.3,0,100):0';
  var st=tx(comp,"s"+(i+1),44,INK,HV,0,0,420,"left");st.property("Position").expression=A+'[(im?480:224)+sl,'+(y-26)+']';st.property("Opacity").expression=VIS;
  var sd=tx(comp,"d"+(i+1),32,MUTE,MED,0,0,420,"left");sd.property("Position").expression=A+'[(im?480:224)+sl,'+(y+28)+']';sd.property("Opacity").expression=VIS;}}
function reviewCards(comp){_COMP=comp;
 canvas(comp,CANVAS);var ti=tx(comp,"title",56,INK,HV,MX+40,380,880,"left");lift(ti,0.15,12,0.4);var ROT=[-1.5,1,-0.6];
 for(var i=0;i<3;i++){var y=620+i*280,f="r"+(i+1),A=D+BEATS(0.6,0.9)+'var t0=BT('+i+');',VIS=A+'d["'+f+'_text"]?linear(time,t0,t0+0.25,0,100):0';
  // The rig pivots on the card's centre so its slight tilt does not swing the card across the frame.
  var rg=rigNull(comp,"review rig "+i);rg.property("Anchor Point").setValue([520,y]);rg.property("Position").setValue([520,y]);var cd=rect(comp,"review "+i,900,240,PAPER,24,null);cd[0].property("Position").setValue([520,y]);softShadow(cd[0],40,60,16);cd[0].property("Opacity").expression=VIS;
  var kids=[cd[0]];for(var s=0;s<5;s++){var e=star(comp,"star "+i+"_"+s+" off",130+s*44,y-70,18,LINE);e.property("Opacity").expression=VIS;var on=star(comp,"star "+i+"_"+s,130+s*44,y-70,18,YELLOW);on.property("Opacity").expression=A+'d["'+f+'_text"]&&'+s+'<Math.round(d["'+f+'_stars"]||5)?linear(time,t0+0.1+'+s*0.05+',t0+0.2+'+s*0.05+',0,100):0';kids.push(e,on);}
  var qt=tx(comp,f+"_text",36,INK,BOLD,110,y,800,"left");qt.property("Opacity").expression=VIS;var nm=tx(comp,f+"_name",28,MUTE,MED,110,y+68,500,"left");srcE(nm,'var s=String(d["'+f+'_name"]||"");s?"— "+s.charAt(0)+"**":""');nm.property("Opacity").expression=VIS;kids.push(qt,nm);
  for(var k=0;k<kids.length;k++)kids[k].parent=rg;rg.property("Position").expression=A+'[520,'+y+'+90*(1-ease(time,t0,t0+0.45,0,1))]';rg.property("Rotation").setValue(ROT[i]);}
 var so=tx(comp,"source",28,MUTE,MED,MX+40,1430,880,"left");fade(so,0.8,1.0);}
function certCard(comp,folder){_COMP=comp;
 canvas(comp,CANVAS);var m=card(comp,folder,"cert.png","@cert",760,680,W/2,640);cardFollow("@cert");m.property("Rotation").setValue(-1.5);var fr=comp_layer("@cert frame");if(fr)fr.property("Rotation").expression='thisComp.layer("@cert").rotation';
 var mp=m.property("Position");mp.setValueAtTime(0.1,[W/2,780]);mp.setValueAtTime(0.55,[W/2,640]);bez(mp,85,40);fade(m,0.1,0.3);
 for(var i=0;i<3;i++){var y=1110+i*90,f="k"+(i+1),t0=0.9+i*0.3,VIS=D+'d["'+f+'"]?linear(time,'+t0+','+(t0+0.2)+',0,100):0';var c=checkIcon(comp,"k check "+i,160,y,TEAL,44);c[0].property("Opacity").expression=VIS;c[1].property("Opacity").expression=VIS;
  var kt=tx(comp,f,40,INK,BOLD,210,y,660,"left");kt.property("Opacity").expression=VIS;}
 var so=tx(comp,"source",28,MUTE,MED,MX+40,1420,880,"left");fade(so,1.6,1.8);}
function buyCta(comp,folder){_COMP=comp;
 var rg=rigNull(comp,"cta rig");var cd=rect(comp,"cta card",820,230,PAPER,28,null);cd[0].property("Position").setValue([470,1300]);softShadow(cd[0],50,60,16);
 var ph=photo(comp,folder,"product.png","@product",170,170,170,1300,18);
 var nm=tx(comp,"name",40,INK,BOLD,290,1245,560,"left");var pr=tx(comp,"price",56,RED,HV,290,1310,560,"left");var ct=tx(comp,"cta",30,INK,MED,290,1372,560,"left");srcE(ct,'String(d.cta||"点下方链接看看")');
 var kids=[cd[0],ph[0],ph[1],nm,pr,ct];for(var i=0;i<kids.length;i++)kids[i].parent=rg;var rp=rg.property("Position");rp.setValueAtTime(0.15,[0,160]);rp.setValueAtTime(0.55,[0,0]);bez(rp,85,40);
 fade(cd[0],0.15,0.3);fade(ph[0],0.3,0.45);fade(nm,0.4,0.55);fade(pr,0.5,0.65);fade(ct,0.6,0.75);
 for(var k=0;k<3;k++){var ar=lineShape(comp,"arrow "+k,RED,7);ar[1].expression='var b=6*Math.sin(time*7);createPath([[180,'+(1420+k*14)+'+b],[200,'+(1436+k*14)+'+b],[220,'+(1420+k*14)+'+b]],[],[],false)';ar[0].property("Opacity").expression='time<0.9?0:(time<'+(1.0+k*0.08)+'?0:100-'+k*25+')';}
 exitAll(comp);}
function colorSwatch(comp,folder){_COMP=comp;
 canvas(comp,CANVAS);var SEQ=D+'var I=d._images||[],n=0;for(var q=1;q<=4;q++)if(I.indexOf("img"+q)>=0)n=q;n=Math.max(n,1);var e=(d._duration_ms||6000)/1000,seg=(e-0.6)/n;function T(i){return 0.4+i*seg;}function ON(i){return ease(time,T(i),T(i)+0.35,0,1)*(1-(i<n-1?ease(time,T(i+1),T(i+1)+0.35,0,1):0));}';
 for(var i=0;i<4;i++){var nm="@img"+(i+1);var m=card(comp,folder,"img"+(i+1)+".png",nm,820,860,W/2,720);cardFollow(nm);
  m.property("Opacity").expression=SEQ+'('+i+'<n)?100*ON('+i+'):0';m.property("Scale").expression=SEQ+'var k=Math.min(820/width,860/height)*100*(0.97+0.03*ease(time,T('+i+'),T('+i+')+0.5,0,1));[k,k]';
  var sw=photo(comp,folder,"img"+(i+1)+".png","swatch "+i,92,92,0,0,46);sw[1].property("Position").expression=SEQ+'[540+('+i+'-(n-1)/2)*140,1290]';sw[0].property("Position").expression=SEQ+'[540+('+i+'-(n-1)/2)*140,1290]';
  sw[0].property("Scale").expression='var k=Math.max(92/width,92/height)*100*2.2;[k,k]';sw[0].property("Opacity").expression=SEQ+'('+i+'<n)?linear(time,0.2,0.4,0,100):0';
  var cn=tx(comp,"c"+(i+1),44,INK,HV,W/2,1410,692);cn.property("Opacity").expression=SEQ+'('+i+'<n)?100*ON('+i+'):0';}
 var rgn=ring(comp,"swatch ring",BLUE,5);rgn[1].property("Size").setValue([112,112]);rgn[0].property("Position").expression=SEQ+'var x=0;for(var q=0;q<n;q++)x+=ON(q)*(540+(q-(n-1)/2)*140);[x,1290]';fade(rgn[0],0.4,0.6);}

// The playback safe area sits on top as a guide layer: visible while editing in AE, never rendered.
function guide(comp,folder){var f=new File(folder.fsName+(ASPECT=="16:9"?"/guide-16x9.png":"/guide-9x16.png"));if(!f.exists)return;var g=comp.layers.add(app.project.importFile(new ImportOptions(f)));g.name="safe area guide";g.guideLayer=true;g.property("Opacity").setValue(45);g.moveToBeginning();}
var FN={"keyword-contrast":keywordContrast,"keyword-slab":keywordSlab,"impact-line":impactLine,"outline-box-title":outlineBoxTitle,"split-rise-title":splitRiseTitle,
 "quote-card":quoteCard,"quote-hold":quoteHold,"pair-blocks":pairBlocks,"ring-mark":ringMark,"callout-label":calloutLabel,"magnifier":magnifier,"focus-dim":focusDim,
 "host-to-chip":hostToChip,"host-parallel":hostParallel,"name-plate":namePlate,"name-chevron":nameChevron,
 "value-swap":valueSwap,"count-title":countTitle,"metric-trend":metricTrend,"number-roll":numberRoll,"term-card":termCard,"pick-one":pickOne,"line-story":lineStory,"bar-grow":barGrow,
 "glass-board":glassBoard,"step-line":stepLine,"converge":converge,"line-carry":lineCarry,"timeline-travel":timelineTravel,"slider-compare":sliderCompare,"split-6040":split6040,"before-after-scrub":beforeAfterScrub,
 "chapter-card":chapterCard,"chapter-list":chapterList,"title-to-label":titleToLabel,"lead-word":leadWord,"news-desk":newsDesk,"layout-relay":layoutRelay,"grid-hero":gridHero,
 "echo-bed":echoBed,"route-pin":routePin,"shape-wipe":shapeWipe,"color-slam":colorSlam,"follow-button":followButton,"follow-card-x":followCardX,"follow-card-dy":followCardDy,
 "product-hero":productHero,"product-angles":productAngles,"selling-points":sellingPoints,"check-list":checkList,"spec-table":specTable,"compare-table":compareTable,"dimension-mark":dimensionMark,
 "price-drop":priceDrop,"deal-timer":dealTimer,"layer-stack":layerStack,"use-steps":useSteps,"review-cards":reviewCards,"cert-card":certCard,"buy-cta":buyCta,"color-swatch":colorSwatch};
var ALPHA={"keyword-contrast":1,"keyword-slab":1,"impact-line":1,"outline-box-title":1,"split-rise-title":1,"quote-hold":1,"pair-blocks":1,"host-parallel":1,"name-plate":1,"name-chevron":1,"chapter-card":1,"value-swap":1,"count-title":1,"term-card":1,"lead-word":1,"shape-wipe":1,"follow-button":1,"follow-card-x":1,"follow-card-dy":1,"check-list":1,"price-drop":1,"deal-timer":1,"buy-cta":1};

var log=[];app.beginSuppressDialogs();
for(var i=0;i<IDS.length;i++){var id=IDS[i];try{
 if(app.project)app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES);app.newProject();var folder=new Folder(STORE+"/"+id+"/"+(VERSIONS[id]||"v1"));DATA=SAMPLES[id];D='var d=/*AICS_DATA*/'+DATA+'/*AICS_END*/;';
 // Landscape builds reuse the shared helpers with the frame size and margin swapped, then call the derived <fn>L builder.
 var LAND=ASPECT=="16:9";W=LAND?1920:1080;H=LAND?1080:1920;H_=H;MX=LAND?150:84;
 var comp=app.project.items.addComp("MAIN",W,H,1,LEN,FPS);comp.bgColor=BG;if(!ALPHA[id])base(comp);
 var build=LAND?(FNL[id]?eval(FNL[id]):null):FN[id];if(LAND&&!build)throw new Error("no landscape layout");if(build)build(comp,folder);guide(comp,folder);if(ALPHA[id])alphaQueue(comp);
 if(id=="number-card")numberCard(comp);if(id=="title-card")titleCard(comp);if(id=="diagram-flow")diagramFlow(comp);if(id=="map-route")mapRoute(comp,folder);if(id=="photo-push")photoPush(comp,folder);if(id=="compare-pair")comparePair(comp,folder);
 app.project.save(new File(folder.fsName+(LAND?"/template-16x9.aepx":"/template.aepx")));log.push(id+": ok layers="+comp.numLayers);
}catch(err){log.push(id+": ERROR line "+err.line+": "+err.toString());}}
app.endSuppressDialogs(false);var f=new File(LOG);f.encoding="UTF-8";f.open("w");f.writeln(log.join("\n"));f.close();
'''


def make(store: str, ids: list[str], aspect: str = "9:16") -> str:
    root = Path(store).expanduser()
    for template_id in ids:
        folder = root / template_id / VERSIONS.get(template_id, "v1")
        folder.mkdir(parents=True, exist_ok=True)
        for name in IMAGES.get(template_id, []):
            if not (folder / name).exists():
                # Neutral placeholders stand in until real pictures are supplied at render time.
                source = {"map.png": ["-f", "lavfi", "-i", "color=c=0x0d1b2a:s=1080x1920", "-vf", "drawgrid=w=100:h=100:t=1:c=0x1f3b57"],
                          "image.png": ["-f", "lavfi", "-i", "gradients=s=1080x1920:c0=0x0b2a3a:c1=0x05080c:duration=1"]}.get(
                    name, ["-f", "lavfi", "-i", "color=c=black@0.0:s=600x800,format=rgba"])
                subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *source, "-frames:v", "1", str(folder / name)], check=True)
        key = aspect.replace(":", "x")
        shutil.copyfile(Path(__file__).resolve().parent.parent / "safe-zones" / f"{key}.png", folder / f"guide-{key}.png")
    log = root / "make_templates.log"
    jsx = (JSX.replace("__STORE__", json.dumps(str(root))).replace("__IDS__", json.dumps(ids))
              .replace("__SAMPLES__", json.dumps({key: json.dumps(SAMPLES[key], ensure_ascii=False) for key in ids}, ensure_ascii=False))
              .replace("__VERSIONS__", json.dumps(VERSIONS)).replace("__LOG__", json.dumps(str(log))).replace("__ASPECT__", json.dumps(aspect)))
    landscape = {}
    if aspect == "16:9":
        from landscape_layouts import landscape_jsx
        fn_by_id = dict(re.findall(r'"([a-z0-9-]+)":([A-Za-z0-9]+)', jsx[jsx.index("var FN={"):jsx.index("};", jsx.index("var FN={"))]))
        jsx, landscape = landscape_jsx(jsx, fn_by_id, ids)
    jsx = jsx.replace("__FNL__", json.dumps(landscape))
    script = root / "make_templates.jsx"
    script.write_text("﻿" + jsx, encoding="utf-8")
    # Building many templates takes longer than AppleScript's default two-minute event timeout.
    subprocess.run(["osascript", "-e", "with timeout of 1800 seconds", "-e", f'tell application "Adobe After Effects 2026" to DoScriptFile "{script}"',
                    "-e", "end timeout"], check=True)
    return log.read_text(encoding="utf-8")


if __name__ == "__main__":
    args = sys.argv[1:]
    aspect = "9:16"
    if "--aspect" in args:
        i = args.index("--aspect")
        aspect = args[i + 1]
        del args[i:i + 2]
    print(make(args[0], args[1:] or list(SAMPLES), aspect))
