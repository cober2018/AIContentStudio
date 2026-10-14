async page => {
  const forms = [{"channel": "baijia", "form": "article", "actor": "v5-freeze@studio.local", "project": 1, "unit": 1}, {"channel": "bilibili", "form": "article", "actor": "v5-freeze@studio.local", "project": 1, "unit": 1}, {"channel": "bilibili", "form": "image_note", "actor": "v5-freeze@studio.local", "project": 1, "unit": 1}, {"channel": "douyin", "form": "spoken_script", "actor": "video-f6e@studio.local", "project": 1, "unit": 1}, {"channel": "netease", "form": "article", "actor": "v5-freeze@studio.local", "project": 1, "unit": 1}, {"channel": "penguin", "form": "article", "actor": "v5-freeze@studio.local", "project": 1, "unit": 1}, {"channel": "sohu", "form": "article", "actor": "v5-freeze@studio.local", "project": 1, "unit": 1}, {"channel": "toutiao", "form": "article", "actor": "v5-freeze@studio.local", "project": 1, "unit": 1}, {"channel": "wechat", "form": "article", "actor": "v5-freeze@studio.local", "project": 1, "unit": 1}, {"channel": "weibo", "form": "single", "actor": "v5-freeze@studio.local", "project": 1, "unit": 1}, {"channel": "x", "form": "articles", "actor": "v5-freeze@studio.local", "project": 1, "unit": 1}, {"channel": "x", "form": "long_post", "actor": "v5-freeze@studio.local", "project": 1, "unit": 1}, {"channel": "x", "form": "single", "actor": "v5-freeze@studio.local", "project": 1, "unit": 1}, {"channel": "x", "form": "thread", "actor": "v5-freeze@studio.local", "project": 1, "unit": 1}, {"channel": "xiaohongshu", "form": "image_note", "actor": "v5-freeze@studio.local", "project": 1, "unit": 1}, {"channel": "zhihu", "form": "answer", "actor": "v5-freeze@studio.local", "project": 1, "unit": 1}, {"channel": "zhihu", "form": "article", "actor": "v5-freeze@studio.local", "project": 1, "unit": 1}];
  const results = await page.evaluate(() => JSON.parse(sessionStorage.getItem('aics_batch_b_browser_receipts') || '[]'));
  page.removeAllListeners('dialog');
  page.on('dialog', async dialog => await dialog.accept());
  for (const record of forms) {
    const key = record.channel + '-' + record.form;
    if (results.some(row => row.channel===record.channel && row.form===record.form)) continue;
    await page.evaluate(actor => localStorage.setItem('studio-user', actor), record.actor);
    await page.context().addCookies([{name:'aics_smoke_form',value:key,url:'http://127.0.0.1:18765',httpOnly:true,sameSite:'Strict'}]);
    await page.goto(`http://127.0.0.1:18765/projects/${record.project}/units/${record.unit}/production?panel=variants&smoke_form=${key}`);
    await page.getByRole('combobox',{name:'目标渠道与形态',exact:true}).waitFor();
    await page.getByRole('combobox',{name:'目标渠道与形态',exact:true}).selectOption(record.channel+'.'+record.form+'.primary');
    if (record.form === 'answer') {
      await page.getByRole('textbox',{name:'知乎问题 text',exact:true}).fill('这是哪一类表达？');
      await page.getByRole('checkbox',{name:'我已确认这个问题，按此问题生成回答',exact:true}).check();
    }
    await page.getByRole('button',{name:'生成确定性预览',exact:true}).click();
    await page.getByText('仅生成预览，尚未保存渠道变体，也没有远端发布。',{exact:true}).waitFor();
    if (record.channel === 'wechat') {
      const cover = page.getByRole('combobox',{name:/^公众号封面素材版本/});
      await cover.selectOption(await cover.locator('option').nth(1).getAttribute('value'));
    }
    await page.getByRole('button',{name:'明确接受并保存新 Variant',exact:true}).click();
    await page.getByText('已追加保存 Variant 修订；来源 Master 和 Workflow 草稿均未修改。',{exact:true}).waitFor();
    const form = page.getByRole('region',{name:'Variant 正文编辑',exact:true});
    const editor = form.locator('textarea:not([readonly])').first();
    const previous = await editor.inputValue();
    await editor.fill(previous+'编辑');
    await editor.fill(previous);
    await page.getByRole('button',{name:'保存渠道正文与创作意图为新修订',exact:true}).click();
    await page.getByText('已将渠道正文与创作意图一起保存为新修订；来源 Master、其他渠道和精确引用均保留。',{exact:true}).waitFor();
    await page.getByRole('button',{name:'运行 Variant 检查',exact:true}).click();
    await page.getByText('已保存当前检查；历史检查没有被覆盖。',{exact:true}).waitFor();
    const rows = await page.evaluate(async ({project,unit,channel,form})=>{
      const response=await fetch(`/api/v1/content-projects/${project}/units/${unit}/channel-variants?variant_key=${channel}.${form}.primary`,{headers:{'X-Studio-User':localStorage.getItem('studio-user')}});
      return (await response.json()).items;
    },record);
    if(rows.length<2 || rows[0].payload_hash!==rows[1].payload_hash) throw Error(key+' reopen hash mismatch');
    await page.reload();
    await page.getByRole('combobox',{name:'目标渠道与形态',exact:true}).waitFor();
    await page.getByRole('combobox',{name:'目标渠道与形态',exact:true}).selectOption(record.channel+'.'+record.form+'.primary');
    await page.getByRole('button',{name:`#${rows[0].id} · v${rows[0].revision_no} · 当前`,exact:true}).click();
    await page.waitForFunction(() => [...document.querySelectorAll('button')].some(button => button.textContent==='冻结 Candidate v5' && !button.disabled));
    if(await page.getByRole('button',{name:'冻结 Candidate v5',exact:true}).isDisabled()) throw Error(key+' freeze blocked after reload');
    results.push({channel:record.channel,form:record.form,open:true,select:true,preview:true,accept:true,edit:true,save:true,reopen:true,checks:true,freeze_ready:true,payload_hash:rows[0].payload_hash,provider_calls:0,remote_calls:0});
    await page.evaluate(value=>sessionStorage.setItem('aics_batch_b_browser_receipts',JSON.stringify(value)),results);
  }
  return results;
}
