async page => {
const forms = [{"channel": "baijia", "form": "article", "actor": "v5-freeze@studio.local", "project": 1, "unit": 1, "candidate": 1}, {"channel": "bilibili", "form": "article", "actor": "v5-freeze@studio.local", "project": 1, "unit": 1, "candidate": 1}, {"channel": "bilibili", "form": "image_note", "actor": "v5-freeze@studio.local", "project": 1, "unit": 1, "candidate": 1}, {"channel": "douyin", "form": "spoken_script", "actor": "video-f6e@studio.local", "project": 1, "unit": 1, "candidate": 1}, {"channel": "netease", "form": "article", "actor": "v5-freeze@studio.local", "project": 1, "unit": 1, "candidate": 1}, {"channel": "penguin", "form": "article", "actor": "v5-freeze@studio.local", "project": 1, "unit": 1, "candidate": 1}, {"channel": "sohu", "form": "article", "actor": "v5-freeze@studio.local", "project": 1, "unit": 1, "candidate": 1}, {"channel": "toutiao", "form": "article", "actor": "v5-freeze@studio.local", "project": 1, "unit": 1, "candidate": 1}, {"channel": "wechat", "form": "article", "actor": "v5-freeze@studio.local", "project": 1, "unit": 1, "candidate": 1}, {"channel": "weibo", "form": "single", "actor": "v5-freeze@studio.local", "project": 1, "unit": 1, "candidate": 1}, {"channel": "x", "form": "articles", "actor": "v5-freeze@studio.local", "project": 1, "unit": 1, "candidate": 1}, {"channel": "x", "form": "long_post", "actor": "v5-freeze@studio.local", "project": 1, "unit": 1, "candidate": 1}, {"channel": "x", "form": "single", "actor": "v5-freeze@studio.local", "project": 1, "unit": 1, "candidate": 1}, {"channel": "x", "form": "thread", "actor": "v5-freeze@studio.local", "project": 1, "unit": 1, "candidate": 1}, {"channel": "xiaohongshu", "form": "image_note", "actor": "v5-freeze@studio.local", "project": 1, "unit": 1, "candidate": 1}, {"channel": "zhihu", "form": "answer", "actor": "v5-freeze@studio.local", "project": 1, "unit": 1, "candidate": 1}, {"channel": "zhihu", "form": "article", "actor": "v5-freeze@studio.local", "project": 1, "unit": 1, "candidate": 1}]; const results=[]; page.removeAllListeners('dialog'); page.on('dialog',async dialog=>await dialog.accept());
for(const item of forms){
 const key=item.channel+'-'+item.form;
 await page.evaluate(actor=>localStorage.setItem('studio-user',actor),item.actor);
 await page.context().addCookies([{name:'aics_smoke_form',value:key,url:'http://127.0.0.1:18765',httpOnly:true,sameSite:'Strict'}]);
 await page.goto(`http://127.0.0.1:18765/review?project=${item.project}&unit=${item.unit}&candidate=${item.candidate}&smoke_form=${key}`);
 await page.getByRole('region',{name:'冻结渠道正文',exact:true}).waitFor();
 await page.getByRole('tab',{name:'变更',exact:true}).click();
 await page.getByRole('tab',{name:'检查',exact:true}).click();
 await page.getByRole('tab',{name:'交付',exact:true}).click();
 await page.getByRole('region',{name:'本形态交付说明',exact:true}).waitFor();
 const guide=await page.getByRole('region',{name:'本形态交付说明',exact:true}).innerText();
 if(!guide.includes(item.channel+'/'+item.form))throw Error(key+' guide target mismatch');
 const promise=page.waitForEvent('download');
 await page.getByRole('button',{name:'下载成品包 ZIP',exact:true}).click();
 const download=await promise; await download.saveAs('/tmp/aics-batch-b-smoke/ui-zip/'+key+'.zip');
 results.push({channel:item.channel,form:item.form,frozen_preview:true,diff_checks:true,publish_guide:true,ui_zip:true});
 await page.evaluate(value=>sessionStorage.setItem('aics_batch_b_review_receipts',JSON.stringify(value)),results);
}
return results;
}