"use strict";

const fs = require("node:fs");
const { chromium } = require(process.argv[2]);

async function main() {
  const data = JSON.parse(fs.readFileSync(0, "utf8"));
  const browser = await chromium.launch({ executablePath: process.argv[3], headless: true, chromiumSandbox: true,
    args: ["--disable-background-networking", "--disable-component-update", "--disable-sync", "--disable-extensions",
      "--proxy-server=http://127.0.0.1:9", "--proxy-bypass-list=<-loopback>", "--host-resolver-rules=MAP * ~NOTFOUND",
      "--force-webrtc-ip-handling-policy=disable_non_proxied_udp", "--force-color-profile=srgb"] });
  try {
    const page = await browser.newPage({ viewport: { width: data.canvas.width, height: data.canvas.height },
      deviceScaleFactor: 1, serviceWorkers: "block", locale: "en-US", timezoneId: "UTC", colorScheme: "light", reducedMotion: "reduce" });
    await page.route("**/*", route => route.abort());
    await page.setContent('<!doctype html><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; img-src data:; font-src data:; style-src \'unsafe-inline\'"><body></body>');
    await page.evaluate(async ({ canvas, assets, font }) => {
      const face = new FontFace("StudioConfigured", `url(data:font/ttf;base64,${font})`);
      await face.load();
      document.fonts.add(face);
      Object.assign(document.body.style, { margin: "0", padding: "0", overflow: "hidden", background: "transparent" });
      const root = document.createElement("div");
      Object.assign(root.style, { position: "relative", width: `${canvas.width}px`, height: `${canvas.height}px`,
        overflow: "hidden", backgroundColor: canvas.background.color });
      document.body.append(root);
      for (const layer of canvas.layers) {
        if (!layer.visible) continue;
        const box = document.createElement("div");
        Object.assign(box.style, { position: "absolute", left: `${layer.x}px`, top: `${layer.y}px`,
          width: `${layer.width}px`, height: `${layer.height}px`, overflow: "hidden", boxSizing: "border-box",
          transform: `rotate(${layer.rotation}deg)`, transformOrigin: "center", opacity: String(layer.opacity) });
        root.append(box);
        if (layer.type === "text") {
          Object.assign(box.style, { whiteSpace: "pre-wrap", overflowWrap: "anywhere", fontFamily: "StudioConfigured",
            lineHeight: "normal", textAlign: layer.runs[0].style.align });
          for (const run of layer.runs) {
            const span = document.createElement("span");
            span.textContent = run.text;
            Object.assign(span.style, { fontFamily: "StudioConfigured", fontSynthesis: "none", fontSize: `${run.style.font_size}px`,
              color: run.style.color, fontWeight: String(run.style.weight), fontStyle: run.style.italic ? "italic" : "normal" });
            box.append(span);
          }
        } else if (layer.type === "shape") {
          if (layer.shape === "line") {
            const line = document.createElement("div");
            Object.assign(line.style, { position: "absolute", width: "100%", top: "50%",
              borderTop: `${layer.stroke_width}px solid ${layer.stroke || layer.fill}` });
            box.append(line);
          } else {
            Object.assign(box.style, { backgroundColor: layer.fill, borderRadius: layer.shape === "ellipse" ? "50%" : "0",
              border: `${layer.stroke_width}px solid ${layer.stroke || "transparent"}` });
          }
        } else {
          const source = assets[layer.material_revision_id];
          const image = new Image();
          image.src = `data:${source.mime};base64,${source.content}`;
          await image.decode();
          const crop = layer.crop || { x: 0, y: 0, width: 1, height: 1 };
          const cropped = document.createElement("canvas");
          cropped.width = Math.max(1, Math.round(image.naturalWidth * crop.width));
          cropped.height = Math.max(1, Math.round(image.naturalHeight * crop.height));
          cropped.getContext("2d").drawImage(image, image.naturalWidth * crop.x, image.naturalHeight * crop.y,
            image.naturalWidth * crop.width, image.naturalHeight * crop.height, 0, 0, cropped.width, cropped.height);
          const fitted = new Image();
          fitted.src = cropped.toDataURL("image/png");
          await fitted.decode();
          Object.assign(fitted.style, { display: "block", width: "100%", height: "100%", objectFit: layer.fit,
            objectPosition: `${(layer.focal?.x ?? .5) * 100}% ${(layer.focal?.y ?? .5) * 100}%` });
          box.append(fitted);
        }
      }
      await document.fonts.ready;
    }, data);
    await page.screenshot({ path: process.argv[4], type: "png", omitBackground: true, animations: "disabled" });
  } finally {
    await browser.close();
  }
}

main().catch(() => { process.exitCode = 1; });
