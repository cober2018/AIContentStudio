async page => {
 page.removeAllListeners('dialog'); page.on('dialog',async dialog=>await dialog.accept()); const forms=[{"channel": "baijia", "form": "article", "unit": 4}, {"channel": "bilibili", "form": "article", "unit": 4}, {"channel": "bilibili", "form": "image_note", "unit": 5}, {"channel": "douyin", "form": "spoken_script", "unit": 6}, {"channel": "netease", "form": "article", "unit": 4}, {"channel": "penguin", "form": "article", "unit": 4}, {"channel": "sohu", "form": "article", "unit": 4}, {"channel": "toutiao", "form": "article", "unit": 4}, {"channel": "wechat", "form": "article", "unit": 4}, {"channel": "weibo", "form": "single", "unit": 4}, {"channel": "x", "form": "articles", "unit": 4}, {"channel": "x", "form": "long_post", "unit": 4}, {"channel": "x", "form": "single", "unit": 4}, {"channel": "x", "form": "thread", "unit": 4}, {"channel": "xiaohongshu", "form": "image_note", "unit": 5}, {"channel": "zhihu", "form": "answer", "unit": 4}, {"channel": "zhihu", "form": "article", "unit": 4}]; const results=[];
 await page.evaluate(()=>localStorage.setItem('studio-user','admin@studio.local'));
 for(const r of forms){
  await page.goto(`http://127.0.0.1:18766/projects/2/units/${r.unit}/production?panel=variants`);
  const select=page.getByRole('combobox',{name:'目标渠道与形态',exact:true}); await select.waitFor();
  await select.selectOption(r.channel+'.'+r.form+'.primary');
  if(r.form==='answer'){ await page.getByRole('textbox',{name:'知乎问题 text',exact:true}).fill('本地功能验收问题：为什么小步修改更便于复查？'); await page.getByRole('checkbox',{name:'我已确认这个问题，按此问题生成回答',exact:true}).check(); }
  const pending=page.waitForResponse(x=>x.url().endsWith('/adapt-preview') && x.request().method()==='POST');
  await page.getByRole('button',{name:'生成确定性预览',exact:true}).click();
  const response=await pending; const body=await response.json();
  if(response.status()!==200){ results.push({...r,selected:true,preview:false,blocked_reason:body.detail?.code,detail:body.detail?.reason,provider_calls:0,remote_calls:0}); continue; }
  await page.getByText('仅生成预览，尚未保存渠道变体，也没有远端发布。',{exact:true}).waitFor();
  results.push({...r,selected:true,preview:true,payload_schema:body.payload_schema,profile_id:body.profile_version_id,profile_hash:body.profile_hash,provider_calls:0,remote_calls:0});
 }
 await page.evaluate(v=>sessionStorage.setItem('formal17',JSON.stringify(v)),results); return {count:results.length,results};
}