"""Author the data-driven AE template projects into the local template store.

Usage: python3 make_templates.py <store> [template-id ...]
Each template is <store>/<id>/<version>/template.aepx (XML) with its image files beside it.
Expressions read one JSON literal between /*AICS_DATA*/ and /*AICS_END*/; aerender cannot load JSON footage,
so a render rewrites that literal in a copy of the XML and never scripts the running AE.
Run it only when After Effects has no unsaved project open: it starts a new project for each template.
"""
import json
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
}
IMAGES = {"map-route": ["map.png"], "photo-push": ["image.png"], "compare-pair": ["left.png", "right.png"]}

JSX = r'''
var STORE=__STORE__; var IDS=__IDS__; var SAMPLES=__SAMPLES__; var DATA=""; var VERSIONS=__VERSIONS__; var LOG=__LOG__;
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

var log=[];
for(var i=0;i<IDS.length;i++){var id=IDS[i];try{
 app.newProject();var folder=new Folder(STORE+"/"+id+"/"+(VERSIONS[id]||"v1"));DATA=SAMPLES[id];D='var d=/*AICS_DATA*/'+DATA+'/*AICS_END*/;';
 var comp=app.project.items.addComp("MAIN",W,H,1,LEN,FPS);comp.bgColor=BG;base(comp);
 if(id=="number-card")numberCard(comp);if(id=="title-card")titleCard(comp);if(id=="diagram-flow")diagramFlow(comp);if(id=="map-route")mapRoute(comp,folder);if(id=="photo-push")photoPush(comp,folder);if(id=="compare-pair")comparePair(comp,folder);
 app.project.save(new File(folder.fsName+"/template.aepx"));log.push(id+": ok layers="+comp.numLayers);
}catch(err){log.push(id+": ERROR line "+err.line+": "+err.toString());}}
var f=new File(LOG);f.encoding="UTF-8";f.open("w");f.writeln(log.join("\n"));f.close();
'''


def make(store: str, ids: list[str]) -> str:
    root = Path(store).expanduser()
    for template_id in ids:
        folder = root / template_id / VERSIONS.get(template_id, "v1")
        folder.mkdir(parents=True, exist_ok=True)
        for name in IMAGES.get(template_id, []):
            if not (folder / name).exists():
                # Neutral placeholders stand in until real pictures are supplied at render time.
                source = {"map.png": ["-f", "lavfi", "-i", "color=c=0x0d1b2a:s=1600x1000", "-vf", "drawgrid=w=100:h=100:t=1:c=0x1f3b57"],
                          "image.png": ["-f", "lavfi", "-i", "gradients=s=1080x1920:c0=0x0b2a3a:c1=0x05080c:duration=1"]}.get(
                    name, ["-f", "lavfi", "-i", "color=c=black@0.0:s=600x800,format=rgba"])
                subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *source, "-frames:v", "1", str(folder / name)], check=True)
    log = root / "make_templates.log"
    jsx = (JSX.replace("__STORE__", json.dumps(str(root))).replace("__IDS__", json.dumps(ids))
              .replace("__SAMPLES__", json.dumps({key: json.dumps(SAMPLES[key], ensure_ascii=False) for key in ids}, ensure_ascii=False))
              .replace("__VERSIONS__", json.dumps(VERSIONS)).replace("__LOG__", json.dumps(str(log))))
    script = root / "make_templates.jsx"
    script.write_text("﻿" + jsx, encoding="utf-8")
    subprocess.run(["osascript", "-e", f'tell application "Adobe After Effects 2026" to DoScriptFile "{script}"'], check=True)
    return log.read_text(encoding="utf-8")


if __name__ == "__main__":
    print(make(sys.argv[1], sys.argv[2:] or list(SAMPLES)))
