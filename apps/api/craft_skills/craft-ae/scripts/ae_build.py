"""Build native After Effects compositions for a vertical explainer from a declarative spec.

Usage: python3 ae_build.py spec.json [--run]
Writes <work_root>/work/build_comps.jsx (and runs it through AE when --run is given).
The spec format is documented in ../components.md; a new film changes data, not this file.
"""
import json
import subprocess
import sys
from pathlib import Path

JSX = r'''
var SPEC=__SPEC__; var AEP=__AEP__; var LOG=__LOG__; var T=SPEC.tokens;
var cache={};
function src(path){if(!cache[path])cache[path]=app.project.importFile(new ImportOptions(new File(path)));return cache[path];}
function ease(prop){for(var k=1;k<=prop.numKeys;k++){var e=new KeyframeEase(0,80);var sp=(prop.propertyValueType==PropertyValueType.TwoD_SPATIAL||prop.propertyValueType==PropertyValueType.ThreeD_SPATIAL);var n=sp?1:(prop.value instanceof Array?prop.value.length:1);var a=[];for(var i=0;i<n;i++)a.push(e);prop.setTemporalEaseAtKey(k,a,a);}}
function txt(comp,str,size,color,font){var l=comp.layers.addText(str);var d=l.property("Source Text").value;d.resetCharStyle();d.font=font||T.font_bold;d.fontSize=size;d.fillColor=color;d.applyFill=true;d.applyStroke=false;d.justification=ParagraphJustification.CENTER_JUSTIFY;l.property("Source Text").setValue(d);var r=l.sourceRectAtTime(0,false);l.property("Anchor Point").setValue([r.left+r.width/2,r.top+r.height/2]);return l;}
function fitW(l,maxw){var r=l.sourceRectAtTime(0,false);var k=r.width>maxw?maxw/r.width*100:100;l.property("Scale").setValue([k,k]);return k;}
function rrect(comp,name,w,h,rad,color,opacity,stroke){var s=comp.layers.addShape();s.name=name;var g=s.property("Contents").addProperty("ADBE Vector Group").property("Contents");var r=g.addProperty("ADBE Vector Shape - Rect");r.property("Size").setValue([w,h]);r.property("Roundness").setValue(rad);
 if(stroke){var st=g.addProperty("ADBE Vector Graphic - Stroke");st.property("Color").setValue(color);st.property("Stroke Width").setValue(stroke);st.property("Opacity").setValue(opacity);}else{var f=g.addProperty("ADBE Vector Graphic - Fill");f.property("Color").setValue(color);f.property("Opacity").setValue(opacity);}return s;}
function fadeIn(l,t0,len){var o=l.property("Opacity");var v=o.value;o.setValueAtTime(t0,0);o.setValueAtTime(t0+(len||0.3),v);ease(o);}
function span(l,t0,t1){l.inPoint=t0;l.outPoint=t1;}
function camera(L,c,base,cx,cy){var m=c.camera||"push_in";var t0=c.t0,t1=c.t1;var sc=L.property("Scale"),p=L.property("Position");
 if(m=="push_in"){sc.setValueAtTime(t0,[base,base]);sc.setValueAtTime(t1,[base*1.08,base*1.08]);}
 else if(m=="pull_out"){sc.setValueAtTime(t0,[base*1.1,base*1.1]);sc.setValueAtTime(t1,[base,base]);}
 else if(m=="pan"){var b2=base*1.16;sc.setValue([b2,b2]);p.setValueAtTime(t0,[cx+50,cy]);p.setValueAtTime(t1,[cx-50,cy]);}
 else if(m=="follow"){var b3=base*1.12;sc.setValue([b3,b3]);p.setValueAtTime(t0,[cx-30,cy+20]);p.setValueAtTime(t1,[cx+30,cy-20]);}
 else if(m=="tilt_down"||m=="tilt_up"){var b4=base*1.14;sc.setValue([b4,b4]);var d=m=="tilt_down"?1:-1;p.setValueAtTime(t0,[cx,cy+90*d]);p.setValueAtTime(t1,[cx,cy-90*d]);}
 else if(m=="orbit"){sc.setValueAtTime(t0,[base*1.06,base*1.06]);sc.setValueAtTime(t1,[base*1.1,base*1.1]);var r=L.property("Rotation");r.setValueAtTime(t0,-1.5);r.setValueAtTime(t1,1.5);ease(r);}
 else{sc.setValue([base,base]);}
 if(sc.numKeys)ease(sc);if(p.numKeys)ease(p);}
function full(comp,c,dur){var it=src(c.file);var cw=c.crop[2]-c.crop[0],ch=c.crop[3]-c.crop[1];var ccx=(c.crop[0]+c.crop[2])/2,ccy=(c.crop[1]+c.crop[3])/2;
 var F=comp.layers.add(it);F.name="full "+c.id;if(c.video){F.startTime=c.t0-c.trim;F.audioEnabled=false;}span(F,c.t0,c.t1);F.property("Anchor Point").setValue([ccx,ccy]);F.property("Position").setValue([T.width/2,T.height/2]);
 var base=Math.max(T.width/cw,T.height/ch)*100;camera(F,c,base,T.width/2,T.height/2);fadeIn(F,c.t0,0.2);
 var G=comp.layers.addSolid(T.bg,"legibility "+c.id,T.width,T.height,1);span(G,c.t0,c.t1);var gm=G.property("ADBE Mask Parade").addProperty("ADBE Mask Atom");var e=new Shape();e.vertices=[[-100,-100],[T.width+100,-100],[T.width+100,520],[-100,520]];e.closed=true;gm.property("ADBE Mask Shape").setValue(e);gm.property("ADBE Mask Feather").setValue([0,300]);G.property("Opacity").setValue(70);
 if(c.credit){var C=txt(comp,c.credit,26,T.grey,T.font_regular);C.name="credit "+c.id;C.property("Position").setValue([T.width/2,T.caption_y-90]);span(C,c.t0,c.t1);}
 return null;}
function grade(L,g){g=g||{};var ex=L.property("Effects").addProperty("ADBE Exposure2");ex.property("ADBE Exposure2-0003").setValue(g.exposure!=null?g.exposure:-0.25);
 var ti=L.property("Effects").addProperty("ADBE Tint");ti.property(1).setValue(g.black||T.grade_black);ti.property(2).setValue(g.white||T.grade_white);ti.property(3).setValue(g.tint!=null?g.tint:T.grade_tint);}
function cine(comp,c){var it=src(c.file);var cw=c.crop[2]-c.crop[0],ch=c.crop[3]-c.crop[1];var ccx=(c.crop[0]+c.crop[2])/2,ccy=(c.crop[1]+c.crop[3])/2;
 var F=comp.layers.add(it);F.name="shot "+c.id;if(c.video){F.startTime=c.t0-c.trim;F.audioEnabled=false;}span(F,c.t0,c.t1);F.property("Anchor Point").setValue([ccx,ccy]);F.property("Position").setValue([T.width/2,T.height/2]);
 if(c.video&&c.speed){F.stretch=100/c.speed;F.startTime=c.t0-c.trim/c.speed;span(F,c.t0,c.t1);F.frameBlendingType=FrameBlendingType.FRAME_MIX;comp.frameBlending=true;}
 camera(F,c,Math.max(T.width/cw,T.height/ch)*100,T.width/2,T.height/2);grade(F,c.grade);
 if(c.fade){var o=F.property("Opacity");o.setValueAtTime(c.t0,0);o.setValueAtTime(c.t0+c.fade,100);ease(o);}
 if(c.credit){var C=txt(comp,c.credit,24,T.grey,T.font_regular);C.name="credit "+c.id;C.property("Position").setValue([T.width/2,T.credit_y]);span(C,c.t0,c.t1);C.property("Opacity").setValue(80);}}
function finish(comp,dur,s){var Z=comp.layers.addSolid([0,0,0],"bottom scrim",T.width,T.height,1);var zm=Z.property("ADBE Mask Parade").addProperty("ADBE Mask Atom");var ze=new Shape();ze.vertices=[[-200,1080],[T.width+200,1080],[T.width+200,T.height+200],[-200,T.height+200]];ze.closed=true;zm.property("ADBE Mask Shape").setValue(ze);zm.property("ADBE Mask Feather").setValue([0,420]);Z.property("Opacity").setValue(s.scrim!=null?s.scrim:58);
 var V=comp.layers.addSolid([0,0,0],"vignette",T.width,T.height,1);var vm=V.property("ADBE Mask Parade").addProperty("ADBE Mask Atom");vm.inverted=true;var e=new Shape();
 e.vertices=[[T.width/2,-120],[T.width+160,T.height/2],[T.width/2,T.height+120],[-160,T.height/2]];e.inTangents=[[-560,0],[0,-900],[560,0],[0,900]];e.outTangents=[[560,0],[0,900],[-560,0],[0,-900]];e.closed=true;vm.property("ADBE Mask Shape").setValue(e);vm.property("ADBE Mask Feather").setValue([520,520]);V.property("Opacity").setValue(s.vignette!=null?s.vignette:62);
 var A=comp.layers.addSolid([0.5,0.5,0.5],"grain",T.width,T.height,1);A.adjustmentLayer=true;var n=A.property("Effects").addProperty("ADBE Noise");n.property(1).setValue(s.grain!=null?s.grain:2.2);
}
function fadeOut(comp,dur,s){if(!s.fade_out)return;var B=comp.layers.addSolid([0,0,0],"fade out",T.width,T.height,1);var ob=B.property("Opacity");ob.setValueAtTime(dur-s.fade_out,0);ob.setValueAtTime(dur,100);ease(ob);}
function rise(l,at,len,dy){var o=l.property("Opacity");o.setValueAtTime(at,0);o.setValueAtTime(at+len,100);ease(o);var p=l.property("Position");var v=p.value;p.setValueAtTime(at,[v[0],v[1]+dy]);p.setValueAtTime(at+len,v);ease(p);}
function hline(comp,name,x,y,w,at,len,color){var L=comp.layers.addShape();L.name=name;var g=L.property("Contents").addProperty("ADBE Vector Group").property("Contents");var pth=g.addProperty("ADBE Vector Shape - Group");var sh=new Shape();sh.vertices=[[0,0],[w,0]];sh.closed=false;pth.property("Path").setValue(sh);
 var st=g.addProperty("ADBE Vector Graphic - Stroke");st.property("Color").setValue(color||T.accent);st.property("Stroke Width").setValue(2);var tr=g.addProperty("ADBE Vector Filter - Trim");var te=tr.property("End");te.setValueAtTime(at,0);te.setValueAtTime(at+len,100);ease(te);L.property("Position").setValue([x,y]);return L;}
function ltxt(comp,str,size,color,font,x,y,align){var l=comp.layers.addText(str);var d=l.property("Source Text").value;d.resetCharStyle();d.font=font;d.fontSize=size;d.fillColor=color;d.applyFill=true;d.applyStroke=false;d.tracking=size>80?-10:40;
 d.justification=align=="right"?ParagraphJustification.RIGHT_JUSTIFY:ParagraphJustification.LEFT_JUSTIFY;l.property("Source Text").setValue(d);l.property("Position").setValue([x,y]);return l;}
function quiet(comp,k,dur){
 if(k.type=="figure"){var right=k.align=="right";var x=right?T.width-T.margin:T.margin;var at=k.at;
  hline(comp,"rule "+k.value,right?x-260:x,k.y-(k.size||120)*0.95,260,at,0.7);
  var v=ltxt(comp,k.value,k.size||120,T.white,T.font_thin,x,k.y,right?"right":"left");v.name="figure "+k.value;rise(v,at+0.15,0.8,24);
  if(k.unit){var r=v.sourceRectAtTime(at+1,false);var u=ltxt(comp,k.unit,40,T.white,T.font_light,right?x:x+r.left+r.width+14,k.y,right?"right":"left");if(right){u.property("Position").setValue([x,k.y+56]);}rise(u,at+0.3,0.8,24);}
  if(k.label){var lb=ltxt(comp,k.label,34,T.label,T.font_regular,x,k.y+(k.unit&&right?110:58),right?"right":"left");rise(lb,at+0.45,0.8,16);}}
 if(k.type=="title"){var t=txt(comp,k.text,k.size||62,T.white,T.font_light);var d=t.property("Source Text").value;d.tracking=260;t.property("Source Text").setValue(d);var r=t.sourceRectAtTime(0,false);t.property("Anchor Point").setValue([r.left+r.width/2,r.top+r.height/2]);t.property("Position").setValue([T.width/2,k.y]);rise(t,k.at,1.0,18);
  if(k.sub){var su=txt(comp,k.sub,28,T.grey,T.font_regular);var ds=su.property("Source Text").value;ds.tracking=400;su.property("Source Text").setValue(ds);var rs=su.sourceRectAtTime(0,false);su.property("Anchor Point").setValue([rs.left+rs.width/2,rs.top+rs.height/2]);su.property("Position").setValue([T.width/2,k.y+80]);rise(su,k.at+0.35,1.0,12);}
  hline(comp,"title rule",T.width/2-60,k.y-70,120,k.at+0.2,0.8);}
 if(k.type=="tag"){var l=ltxt(comp,k.text,36,T.white,T.font_regular,k.x,k.y,k.align||"left");rise(l,k.at,0.6,10);hline(comp,"tag rule "+k.text,k.align=="right"?k.x-120:k.x,k.y+18,120,k.at,0.6);
  if(k.point){var P=comp.layers.addShape();var g=P.property("Contents").addProperty("ADBE Vector Group").property("Contents");var el=g.addProperty("ADBE Vector Shape - Ellipse");el.property("Size").setValue([14,14]);var f=g.addProperty("ADBE Vector Graphic - Fill");f.property("Color").setValue(T.accent);P.property("Position").setValue(k.point);rise(P,k.at,0.4,0);}}
 if(k.type=="satellite"){var S=comp.layers.addShape();S.name="satellite";var g=S.property("Contents").addProperty("ADBE Vector Group").property("Contents");var el=g.addProperty("ADBE Vector Shape - Ellipse");el.property("Size").setValue([k.size||7,k.size||7]);var f=g.addProperty("ADBE Vector Graphic - Fill");f.property("Color").setValue(k.color||[1,1,1]);
  var gl=S.property("Effects").addProperty("ADBE Glo2");gl.property("ADBE Glo2-0003").setValue(k.glow||18);gl.property("ADBE Glo2-0004").setValue(1.6);var p=S.property("Position");p.setValueAtTime(k.at,k.from);p.setValueAtTime(k.at+k.len,k.to);var o=S.property("Opacity");o.setValueAtTime(k.at,0);o.setValueAtTime(k.at+0.4,100);o.setValueAtTime(k.at+k.len-0.4,100);o.setValueAtTime(k.at+k.len,0);}
 if(k.type=="pulse"){var Q=comp.layers.addSolid(T.accent,"screen glow",T.width,T.height,1);var qm=Q.property("ADBE Mask Parade").addProperty("ADBE Mask Atom");var e=new Shape();var w=k.size[0]/2,h=k.size[1]/2;e.vertices=[[k.x-w,k.y-h],[k.x+w,k.y-h],[k.x+w,k.y+h],[k.x-w,k.y+h]];e.closed=true;qm.property("ADBE Mask Shape").setValue(e);qm.property("ADBE Mask Feather").setValue([90,90]);Q.blendingMode=BlendingMode.ADD;
  var o=Q.property("Opacity");o.setValueAtTime(k.at,0);o.setValueAtTime(k.at+0.25,55);o.setValueAtTime(k.at+1.4,18);ease(o);}
 if(k.type=="credits"){var cr=txt(comp,k.lines.join("\r"),k.size||24,T.label,T.font_regular);var dc=cr.property("Source Text").value;dc.leading=(k.size||24)*1.9;cr.property("Source Text").setValue(dc);cr.property("Position").setValue([T.width/2,k.y]);rise(cr,k.at,0.8,10);}}
function place(comp,c,mode,dur){if(mode=="cinema")return cine(comp,c);if(c.framing=="close"||c.framing=="wide")return full(comp,c,dur);var it=src(c.file);var cw=c.crop[2]-c.crop[0],ch=c.crop[3]-c.crop[1];var ccx=(c.crop[0]+c.crop[2])/2,ccy=(c.crop[1]+c.crop[3])/2;
 var B=comp.layers.add(it);B.name="bg "+c.id;if(c.video){B.startTime=c.t0-c.trim;B.audioEnabled=false;}span(B,c.t0,c.t1);B.property("Anchor Point").setValue([ccx,ccy]);B.property("Position").setValue([T.width/2,T.height/2]);var bs=Math.max(T.width/cw,T.height/ch)*115;B.property("Scale").setValue([bs,bs]);
 var gb=B.property("Effects").addProperty("ADBE Gaussian Blur 2");gb.property(1).setValue(T.bg_blur);gb.property(3).setValue(1);B.property("Opacity").setValue(mode=="bg"?70:55);
 var D=comp.layers.addSolid(T.bg,"dim "+c.id,T.width,T.height,1);span(D,c.t0,c.t1);D.property("Opacity").setValue(mode=="bg"?72:62);
 if(mode=="bg")return null;
 var s=Math.min(T.card_max_w/cw,T.card_max_h/ch);var w=cw*s,h=ch*s;var cy=T.card_cy;
 var S=rrect(comp,"shadow "+c.id,w,h,T.card_radius,[0,0,0],70);S.property("Position").setValue([T.width/2,cy+22]);var sb=S.property("Effects").addProperty("ADBE Gaussian Blur 2");sb.property(1).setValue(45);span(S,c.t0,c.t1);fadeIn(S,c.t0,0.3);
 var F=comp.layers.add(it);F.name="card "+c.id;if(c.video){F.startTime=c.t0-c.trim;F.audioEnabled=false;}span(F,c.t0,c.t1);F.property("Anchor Point").setValue([ccx,ccy]);F.property("Position").setValue([T.width/2,cy]);
 camera(F,c,s*100,T.width/2,cy);
 var M=rrect(comp,"window "+c.id,w,h,T.card_radius,[1,1,1],100);M.property("Position").setValue([T.width/2,cy]);span(M,c.t0,c.t1);var ms=M.property("Scale");ms.setValueAtTime(c.t0,[95,95]);ms.setValueAtTime(c.t0+0.35,[100,100]);ease(ms);
 M.moveBefore(F);F.setTrackMatte(M,TrackMatteType.ALPHA);fadeIn(F,c.t0,0.25);
 var E=rrect(comp,"edge "+c.id,w,h,T.card_radius,[1,1,1],14,2);E.property("Position").setValue([T.width/2,cy]);span(E,c.t0,c.t1);
 if(c.credit){var C=txt(comp,c.credit,26,T.grey,T.font_regular);C.name="credit "+c.id;C.property("Position").setValue([T.width/2,cy+h/2+44]);span(C,c.t0,c.t1);}
 return {w:w,h:h,s:s,ccx:ccx,ccy:ccy,cy:cy};}
function headline(comp,str){var H=txt(comp,str,T.headline_size,T.white,T.font_bold);H.name="headline";fitW(H,T.width-120);var p=H.property("Position");p.setValueAtTime(0.1,[T.width/2,T.headline_y+28]);p.setValueAtTime(0.55,[T.width/2,T.headline_y]);ease(p);var o=H.property("Opacity");o.setValueAtTime(0.1,0);o.setValueAtTime(0.5,100);ease(o);
 var bar=rrect(comp,"headline bar",140,8,4,T.accent,100);bar.property("Position").setValue([T.width/2,T.headline_y+78]);var bx=bar.property("Scale");bx.setValueAtTime(0.3,[0,100]);bx.setValueAtTime(0.8,[100,100]);ease(bx);}
function chip(comp,str,at,x,y,accent){var t=txt(comp,str,40,accent?T.ink:T.white,T.font_bold);t.name="chip: "+str;var r=t.sourceRectAtTime(0,false);
 var sh=rrect(comp,"chipbg: "+str,r.width+56,r.height+30,18,accent?T.accent:T.chip,accent?100:92);if(!accent){var g=sh.property("Contents").property(1).property("Contents");var st=g.addProperty("ADBE Vector Graphic - Stroke");st.property("Color").setValue(T.accent);st.property("Stroke Width").setValue(2);}
 sh.moveAfter(t);sh.parent=t;sh.property("Position").setValue([r.left+r.width/2,r.top+r.height/2]);
 var p=t.property("Position");p.setValueAtTime(at,[x,y+30]);p.setValueAtTime(at+0.4,[x,y]);ease(p);var ls=[t,sh];for(var i=0;i<2;i++){var o=ls[i].property("Opacity");o.setValueAtTime(at,0);o.setValueAtTime(at+0.3,100);ease(o);}}
function captions(comp,caps){for(var j=0;j<caps.length;j++){var c=caps[j];if(c.out-c["in"]<0.08)continue;var C=txt(comp,c.text,T.caption_size,T.white,T.font_medium);C.name="caption "+(j+1);fitW(C,T.width-140);var r=C.sourceRectAtTime(0,false);C.property("Position").setValue([T.width/2,T.caption_y]);
 var B=rrect(comp,"caption box "+(j+1),r.width+52,r.height+28,14,[0.01,0.02,0.04],70);B.moveAfter(C);B.parent=C;B.property("Position").setValue([r.left+r.width/2,r.top+r.height/2]);span(C,c["in"],c.out);span(B,c["in"],c.out);}}
function component(comp,k,dur,geo){var x=T.width/2;
 if(k.type=="keyword_stack"){for(var i=0;i<k.words.length;i++){var t=txt(comp,k.words[i],150,i==k.accent_index?T.accent:T.white,T.font_bold);t.property("Position").setValue([x,k.y0+i*k.step]);var at=(k.at||0.05)+i*(k.interval||0.38);var sc=t.property("Scale");sc.setValueAtTime(at,[60,60]);sc.setValueAtTime(at+0.22,[106,106]);sc.setValueAtTime(at+0.36,[100,100]);ease(sc);var o=t.property("Opacity");o.setValueAtTime(at,0);o.setValueAtTime(at+0.15,100);}}
 if(k.type=="statement"){for(var i=0;i<k.lines.length;i++){var L=k.lines[i];var t=txt(comp,L.text,L.size,L.accent?T.accent:T.white,T.font_bold);fitW(t,T.width-120);t.property("Position").setValue([x,L.y]);var o=t.property("Opacity");o.setValueAtTime(L.at,0);o.setValueAtTime(L.at+0.3,100);}}
 if(k.type=="struck_icon"){var L=rrect(comp,"icon frame",340,220,18,T.white,100,8);L.property("Position").setValue([x,k.y]);var base=rrect(comp,"icon base",440,22,10,T.white,100);base.property("Position").setValue([x,k.y+130]);
  var X=comp.layers.addShape();X.name="strike";var g=X.property("Contents").addProperty("ADBE Vector Group").property("Contents");var pth=g.addProperty("ADBE Vector Shape - Group");var sh=new Shape();sh.vertices=[[-260,-200],[260,200]];sh.closed=false;pth.property("Path").setValue(sh);
  var st=g.addProperty("ADBE Vector Graphic - Stroke");st.property("Color").setValue(T.alert);st.property("Stroke Width").setValue(16);st.property("Line Cap").setValue(2);var tr=g.addProperty("ADBE Vector Filter - Trim");var te=tr.property("End");te.setValueAtTime(k.strike_at,0);te.setValueAtTime(k.strike_at+0.4,100);ease(te);X.property("Position").setValue([x,k.y+40]);
  var ls=[L,base];for(var i=0;i<2;i++){var o=ls[i].property("Opacity");o.setValueAtTime(0.2,0);o.setValueAtTime(0.5,100);o.setValueAtTime(k.strike_at+0.9,100);o.setValueAtTime(k.strike_at+1.3,35);}}
 if(k.type=="phone_pair"){var PX=[x-210,x+210];for(var i=0;i<2;i++){var f=rrect(comp,"phone "+i,300,580,44,T.white,100,6);f.property("Position").setValue([PX[i],k.y]);var l=txt(comp,k.labels[i],38,T.grey,T.font_medium);l.property("Position").setValue([PX[i],k.y+350]);}
  var a=txt(comp,k.content,44,T.white,T.font_bold);a.property("Position").setValue([PX[0],k.y]);
  var dark=rrect(comp,"right dark",286,566,40,[0,0,0],100);dark.property("Position").setValue([PX[1],k.y]);var od=dark.property("Opacity");od.setValueAtTime(0,0);od.setValueAtTime(k.change_at,0);od.setValueAtTime(k.change_at+0.4,100);
  var b=txt(comp,k.content,44,T.white,T.font_bold);b.property("Position").setValue([PX[1],k.y]);var ob=b.property("Opacity");ob.setValueAtTime(k.change_at,100);ob.setValueAtTime(k.change_at+0.3,0);dark.moveBefore(b);
  var n=txt(comp,k.after,40,T.alert,T.font_bold);n.property("Position").setValue([PX[1],k.y]);var on=n.property("Opacity");on.setValueAtTime(k.change_at+0.4,0);on.setValueAtTime(k.change_at+0.7,100);n.moveBefore(dark);}
 if(k.type=="highlight_ring"&&geo){var R=comp.layers.addShape();R.name="ring";var g=R.property("Contents").addProperty("ADBE Vector Group").property("Contents");var el=g.addProperty("ADBE Vector Shape - Ellipse");el.property("Size").setValue(k.size);var st=g.addProperty("ADBE Vector Graphic - Stroke");st.property("Color").setValue(T.accent);st.property("Stroke Width").setValue(7);
  R.property("Position").setValue([x+(k.source_xy[0]-geo.ccx)*geo.s,geo.cy+(k.source_xy[1]-geo.ccy)*geo.s]);var sc=R.property("Scale");sc.setValueAtTime(k.at,[0,0]);sc.setValueAtTime(k.at+0.35,[100,100]);ease(sc);}
 if(k.type=="end_card"){var sc=comp.layers.addSolid(T.bg,"scrim",T.width,T.height,1);var os=sc.property("Opacity");os.setValueAtTime(0.2,0);os.setValueAtTime(0.7,78);
  component(comp,{type:"statement",lines:k.lines},dur,geo);
  var cr=txt(comp,k.credits.join("\r"),28,T.grey,T.font_regular);cr.property("Position").setValue([x,k.credits_y]);var oc=cr.property("Opacity");oc.setValueAtTime(k.credits_at,0);oc.setValueAtTime(k.credits_at+0.5,100);
  var bl=comp.layers.addSolid([0,0,0],"fade out",T.width,T.height,1);var ob=bl.property("Opacity");ob.setValueAtTime(dur-0.6,0);ob.setValueAtTime(dur,100);}}
var log=[];try{app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES);app.newProject();
for(var i=0;i<SPEC.comps.length;i++){var s=SPEC.comps[i];var dur=s.duration;var comp=app.project.items.addComp(s.role+" "+s.id,T.width,T.height,1,dur,T.fps);comp.bgColor=T.bg;
 comp.layers.addSolid(T.bg,"base",T.width,T.height,1);
 if(s.mode=="cinema"){for(var j=0;j<s.cuts.length;j++)cine(comp,s.cuts[j]);finish(comp,dur,s);if(s.black_from){var K=comp.layers.addSolid([0,0,0],"to black",T.width,T.height,1);var ok=K.property("Opacity");ok.setValueAtTime(s.black_from[0],0);ok.setValueAtTime(s.black_from[0]+s.black_from[1],100);ease(ok);
  for(var q=1;q<=comp.numLayers;q++){var Lq=comp.layer(q);if(Lq.name.indexOf("shot ")==0){var oq=Lq.property("Opacity");oq.setValueAtTime(s.black_from[0],100);oq.setValueAtTime(s.black_from[0]+s.black_from[1],0);ease(oq);}}}
 for(var j=0;j<(s.components||[]).length;j++)quiet(comp,s.components[j],dur);fadeOut(comp,dur,s);
  log.push(s.role+":"+comp.duration.toFixed(3)+":"+comp.frameRate+":"+comp.width+"x"+comp.height+":layers="+comp.numLayers);continue;}
 var glow=comp.layers.addSolid(T.accent,"glow",T.width,T.height,1);var gm=glow.property("ADBE Mask Parade").addProperty("ADBE Mask Atom");var e=new Shape();e.vertices=[[140,-260],[T.width-140,-260],[T.width-140,520],[140,520]];e.closed=true;gm.property("ADBE Mask Shape").setValue(e);gm.property("ADBE Mask Feather").setValue([420,420]);glow.property("Opacity").setValue(10);
 var geo=null;for(var j=0;j<s.cuts.length;j++){var g=place(comp,s.cuts[j],s.mode,dur);if(j==0)geo=g;}
 for(var j=0;j<(s.components||[]).length;j++)component(comp,s.components[j],dur,geo);
 headline(comp,s.title);
 for(var j=0;j<(s.chips||[]).length;j++){var c=s.chips[j];chip(comp,c.text,c.at,c.x,c.y,!!c.accent);}
 captions(comp,s.captions||[]);
 log.push(s.role+":"+comp.duration.toFixed(3)+":"+comp.frameRate+":"+comp.width+"x"+comp.height+":layers="+comp.numLayers);}
app.project.save(new File(AEP));}catch(err){log.push("ERROR line "+err.line+": "+err.toString());}
var f=new File(LOG);f.encoding="UTF-8";f.open("w");f.writeln(log.join("\n"));f.close();
'''

DEFAULT_TOKENS = {
    "width": 1080, "height": 1920, "fps": 30, "bg": [0.035, 0.047, 0.067], "accent": [0.31, 0.89, 0.69],
    "chip": [0.06, 0.12, 0.2], "ink": [0.05, 0.09, 0.16], "white": [1, 1, 1], "grey": [0.62, 0.66, 0.72], "alert": [1, 0.38, 0.38],
    "font_bold": "PingFangSC-Semibold", "font_medium": "PingFangSC-Medium", "font_regular": "PingFangSC-Regular",
    "card_cy": 900, "card_max_w": 980, "card_max_h": 1060, "card_radius": 34, "push": 1.04, "bg_blur": 70,
    "headline_y": 330, "headline_size": 74, "caption_y": 1420, "caption_size": 48,
    # cinema mode: one grade for every shot, thin type, no cards
    "font_light": "PingFangSC-Light", "font_thin": "PingFangSC-Thin", "margin": 110, "credit_y": 1460,
    "label": [0.82, 0.87, 0.92], "grade_black": [0.01, 0.035, 0.07], "grade_white": [0.86, 0.95, 1.0], "grade_tint": 32,
}


def build(spec_path: str, run: bool = False) -> Path:
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    work_root = Path(spec["work_root"])
    spec["tokens"] = {**DEFAULT_TOKENS, **spec.get("tokens", {})}
    jsx = (JSX.replace("__SPEC__", json.dumps({"tokens": spec["tokens"], "comps": spec["comps"]}, ensure_ascii=False))
              .replace("__AEP__", json.dumps(str(work_root / "ae" / spec.get("project_name", "film.aep"))))
              .replace("__LOG__", json.dumps(str(work_root / "work" / "ae_build.log"))))
    (work_root / "ae").mkdir(parents=True, exist_ok=True)
    out = work_root / "work" / "build_comps.jsx"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("﻿" + jsx, encoding="utf-8")
    if run:
        app = spec.get("ae_app", "Adobe After Effects 2026")
        subprocess.run(["osascript", "-e", f'tell application "{app}" to DoScriptFile "{out}"'], check=True)
    return out


if __name__ == "__main__":
    print(build(sys.argv[1], run="--run" in sys.argv[2:]))
