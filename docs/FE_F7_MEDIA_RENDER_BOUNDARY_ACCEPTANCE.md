# FE-F7 Media Renderer 输出 / 接受基础契约

## 范围

按已批准 F7 7.5–7.7 实施，F7 总进度仍 86/105。本批不是自动媒体 Renderer 的整体验收，没有真实已安装 renderer、普通用户 verified execution、前端接入或最终成片绑定，不全勾任务。F8 未启动。

```
已保存 current Graphic/Video v2 Master
→ 管理员明确 media-render-previews
→ exact loaded key/version/schema/forms/MIME/runtime/code
→ source/context/profile/canvas/render_input_hash + 安全有界 bytes
→ 单次有界调用 / 真实解码 / Graphic canvas 尺寸
→ actor 15分钟 preview（未入库、未 verified）
→ 明确许可/署名/权利接受
→ 提交前 current/context/runtime/profile/live rights 再验
→ 唯一 MaterialRevision（upstream）+ 项目精确引用
```

Master save、final binding 与 attestation 仍是之后的显式操作；探测不创建 Master/Candidate/CapabilityVerification，不将未知结果重试成成功。

## 文件与接口

- `apps/api/app/services/media_renderers.py`：实际加载身份、安全输入预算、当前性/权利校验、单次探测。
- `apps/api/app/services/content_harness/providers.py`：typed MediaRenderer / MediaRenderOutput。
- `apps/api/app/services/provider_media.py`：复用短期 actor cache、raw 和显式接受；仅追加 safe renderer_origin，不复制任意 metadata。
- `POST /api/v1/content-projects/{project_id}/units/{unit_id}/master-revisions/{master_id}/media-render-previews`：admin-only，extra fields forbidden。
- 已有 `/provider-media/{stage_id}/raw` 与 `/accept` 继续保持权限、短期失效和接受幂等。通用 `/provider-media/stage` 不允许 renderer kind，不能绕过入口。

来源许可/权利不能被输出升级；CC BY 必须保留 CC BY 与完整署名。Source bytes 累计最多30MB，先检查安全根目录/文件大小再读；重复图层只读/传一份 revision bytes，input hash 保留所有 placement。输出必须真解码、hash/canvas/MIME匹配，Graphic像素尺寸匹配真实 canvas；Video MP4 解码不等于已经验证时间线视觉一致性。

## 实跑证据

| 门禁 | 最终结果 |
|---|---|
| 本批新回归 | 32 tests |
| Renderer / Media acceptance 定向 | 77 passed / 1 既有 warning |
| 全后端 | 1354 passed / 2 skipped / 8 既有 warnings，53.83s |
| TypeScript / Vite / FE-P1 | PASS |
| OpenSpec 全量 strict | 30/30 PASS |
| 范围 Ruff / git diff --check | PASS |
| 独立只读 implementation review | APPROVE，本批 foundation，不代表整个 F7 |

本批先看到缺 route 的15项失败；来源权限升级/提交前撤权、错误尺寸、错误 source kind、form不匹配、CC BY丢失、读取前超限及重复 bytes 分别 RED→GREEN。MP4 用 ffmpeg 生成真实小字节，并经 ffprobe/ffmpeg 解码后接受，**这是契约 fixture，不是已安装真实自动 Video renderer 的成片证明**。异常/结果 metadata 含秘密时不进入 API/素材来源字段。运行命令：

```
cd apps/api
.venv/bin/pytest tests/test_f7_media_renderers.py tests/test_f7_media_acceptance.py tests/test_f7_renderer_capabilities.py -q --tb=line
env -u NO_PROXY -u no_proxy .venv/bin/pytest -q --tb=line
cd ../web
npm run build
```

FE-P1保持 Projects224.84/72.94kB raw/gzip、Assets258.81/82.80、Settings230.46/75.17、common Production280.03/89.09。未修改前端，未重新做浏览器全链路，不用旧浏览器报告代替本批。

## 未证明 / 待完成

真实 installed Graphic/Video renderer、Video 时间线/时长/画幅及完整视觉输出验证、媒体 scope verification、普通用户执行、UI preview/accept/final bind、自动 render attestation、真实双连接 PostgreSQL撤权并发和F7完整验收仍待完成。

本批无新表/migration、无外部账号/Provider请求、无push/deploy/生产迁移/canonical sync/archive。保留全PRD与后续F8目标，不以局部绿色结果缩小产品终态。
