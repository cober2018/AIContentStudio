"""Report text and key shapes that leave the 9:16 playback safe area.

Usage: python3 check_safe_area.py <store> [template-id ...] [--aspect 9:16|16:9]
Opens each built template in After Effects with its sample content, samples several moments,
and lists every visible text or shape layer whose box crosses the safe area in ../safe-zones/.
Full-bleed layers (backgrounds, wipes, mattes, the exit adjustment) are not key content and are skipped.
Text and small shapes (labels, pills, pins, markers) must clear the right-hand button column too; large shapes
(cards, panels, picture frames) only need to stay inside the outer bounds, since the buttons then cover an edge, not content.
Boxes that cross the frame edge are entering or leaving and are not judged at that moment.
"""
import json
import subprocess
import sys
from pathlib import Path

# 16:9 has no button column, so its button band starts below the safe area.
SAFES = {"9:16": {"left": 59, "top": 268, "right": 1016, "bottom": 1482, "button_right": 886, "button_top": 769},
         "16:9": {"left": 91, "top": 190, "right": 1828, "bottom": 959, "button_right": 1828, "button_top": 9999}}
FILES = {"9:16": "template.aepx", "16:9": "template-16x9.aepx"}
SKIP = ("canvas", "bg ", "glow", "grey out", "dim", "wipe ", "matte", "exit", "safe area guide", "ripple", "frame back", "border",
        "card rig", "host rig", "rig", "handle", "flourish", "corner ", "axis", "ticks", "grid ", "baseline", "rail", "route ", "carry", "cursor")

JSX = r'''
var STORE=__STORE__,IDS=__IDS__,SKIP=__SKIP__,LOG=__LOG__,S=__SAFE__,FILE=__FILE__;var out=[];app.beginSuppressDialogs();
function skip(n){for(var i=0;i<SKIP.length;i++)if(n.indexOf(SKIP[i])==0)return true;return false;}
function v(p,t){return p.valueAtTime(t,false);}
function toComp(l,pt,t){var c=pt;var L=l;while(L){var a=v(L.transform.anchorPoint,t),p=v(L.transform.position,t),s=v(L.transform.scale,t),r=v(L.transform.rotation,t)*Math.PI/180;
 var x=(c[0]-a[0])*s[0]/100,y=(c[1]-a[1])*s[1]/100;c=[p[0]+x*Math.cos(r)-y*Math.sin(r),p[1]+x*Math.sin(r)+y*Math.cos(r)];L=L.parent;}return c;}
function visible(l,t){var L=l;while(L){if(v(L.transform.opacity,t)<5)return false;L=L.parent;}return l.enabled&&!l.guideLayer&&l.activeAtTime(t);}
for(var i=0;i<IDS.length;i++){var id=IDS[i];try{
 if(app.project)app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES);var f=new File(STORE+"/"+id+"/v1/"+FILE);if(!f.exists){out.push(id+"\tmissing");continue;}
 app.open(f);var comp=null;for(var k=1;k<=app.project.numItems;k++){var it=app.project.item(k);if(it instanceof CompItem&&it.name=="MAIN")comp=it;}
 var seen={};for(var tt=0.4;tt<=6.01;tt+=0.4){for(var j=1;j<=comp.numLayers;j++){var l=comp.layer(j);if(skip(l.name)||l.isTrackMatte)continue;
  if(!(l instanceof TextLayer)&&!(l instanceof ShapeLayer))continue;if(!visible(l,tt))continue;
  var r=l.sourceRectAtTime(tt,false);if(r.width<1||r.height<1)continue;
  var P=[toComp(l,[r.left,r.top],tt),toComp(l,[r.left+r.width,r.top],tt),toComp(l,[r.left,r.top+r.height],tt),toComp(l,[r.left+r.width,r.top+r.height],tt)];
  var x0=1e9,y0=1e9,x1=-1e9,y1=-1e9;for(var q=0;q<4;q++){x0=Math.min(x0,P[q][0]);y0=Math.min(y0,P[q][1]);x1=Math.max(x1,P[q][0]);y1=Math.max(y1,P[q][1]);}
  if(x1-x0<1||y1-y0<1||x0<2||y0<2||x1>comp.width-2||y1>comp.height-2)continue;
  var big=!(l instanceof TextLayer)&&(x1-x0)*(y1-y0)>40000;var right=(!big&&y1>S.button_top&&y0<S.bottom)?S.button_right:S.right;var bad=[];
  if(x0<S.left-1)bad.push("left "+Math.round(S.left-x0));if(y0<S.top-1)bad.push("top "+Math.round(S.top-y0));if(x1>right+1)bad.push("right "+Math.round(x1-right));if(y1>S.bottom+1)bad.push("bottom "+Math.round(y1-S.bottom));
  if(bad.length){var key=l.name+"|"+bad.join(",").replace(/[0-9]+/g,"");if(!seen[key]){seen[key]=1;out.push(id+"\t"+l.name+"\t"+tt.toFixed(1)+"s\t"+bad.join(", ")+"\t["+[Math.round(x0),Math.round(y0),Math.round(x1),Math.round(y1)].join(",")+"]");}}}}
 out.push(id+"\tchecked");
}catch(e){out.push(id+"\tERROR "+e.line+" "+e.toString());}}
if(app.project)app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES);app.endSuppressDialogs(false);var o=new File(LOG);o.encoding="UTF-8";o.open("w");o.writeln(out.join("\n"));o.close();
'''


def check(store: str, ids: list[str], aspect: str = "9:16") -> str:
    root = Path(store).expanduser()
    ids = ids or sorted(p.name for p in root.iterdir() if (p / "v1" / FILES[aspect]).exists())
    log = root / "check_safe_area.log"
    jsx = (JSX.replace("__STORE__", json.dumps(str(root))).replace("__IDS__", json.dumps(ids)).replace("__SKIP__", json.dumps(SKIP))
           .replace("__LOG__", json.dumps(str(log))).replace("__SAFE__", json.dumps(SAFES[aspect])).replace("__FILE__", json.dumps(FILES[aspect])))
    script = root / "check_safe_area.jsx"
    script.write_text("﻿" + jsx, encoding="utf-8")
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
    print(check(args[0], args[1:], aspect))
