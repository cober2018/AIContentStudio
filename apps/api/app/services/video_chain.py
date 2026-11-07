"""Video made end to end by the external model over MCP; the platform keeps records and asks the user.

导演稿 (with a material request per shot) → user → materials, voiceover, DaVinci / AE → 小样 → user → 排版 → 成片 → user.
The platform calls no model here. Saves that do not change picture content (materials, voiceover, edit preparation,
duplicate merges) keep the 导演稿 the user approved; any other save is a new 导演稿 that needs approval again.
"""

from __future__ import annotations

import contextvars
import copy
import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from ..models import (
    ContentMasterRevision,
    ContentUnit,
    CreativeExecution,
    CreativeExecutionOutput,
    CreativeExecutionPackage,
    MaterialRevision,
    ProjectMaterialReference,
    SystemSetting,
    User,
)

KEY = "video_chain"
# Returned with the brief so any external model (not only one with the repo's skills) follows the same chain.
RULES = [
    "你主导整条视频；平台不调用自己的模型。三处停下等用户：导演稿、小样、成片。有意见就出下一版再停。",
    "事实：口播和画面里当事实说的话（数字、症状、研究结论、政策、参数等）只用 get_video_brief 的 facts（已冻结的事实边界）里有的；角色作品写导演稿前先用 get_fact_template 看题材模板，把要当事实说的话连出处用 submit_facts 交上去，平台核对后自动冻结；被退回的换来源或不说。事实改了要重存导演稿。"
    "fact_templates 里每个模板的 red_lines 必须守，opinion_only 列的内容只能当个人经历或观点说。",
    "导演稿：完整 video.master.v2；每个镜头 board 含 message/visual/camera/speaker/sound/notes/material_request。material_request 写清画面必须有什么、景别、时长、实拍还是图形、横竖屏。一镜一个意思，景别和运镜要有变化，同一画面不重复用。",
    "商品作品和角色作品：导演稿采用前不生成任何画面（首帧、九宫格、图生视频、切换手动 / 自动都会被拒绝）；采用后先把用户素材对应到镜头（set_shot_materials），再只给没有用户素材的镜头生成。",
    "九宫格分组：写导演稿时，要生成画面的镜头里需要同一个人物或同一个场景的，归成一组写进 consistency_groups（每组 id、shot_ids 至少 2 个、person 共用人物、setting 共用场景；一个镜头只在一组）；"
    "零散、互不相关的镜头不归组。采用后归了组的用 generate_storyboard_grid(group_id) 一组出一张九宫格，每格是该镜的首帧候选；没归组的用 generate_shot_image 单张出图，或给用户文生视频提示词。改分组就是改导演稿，要重新采用。",
    "角色作品补镜头：没有商品图，生首帧、九宫格都不带商品参考、不做商品检查，提示词按这一镜 board 的画面、运镜、人物态度写，不提商品；"
    "角色有形象照就带上，人物照形象照来；没有形象照，生成画面里不出现人物，只拍场景，拿东西只出现手部。"
    "例外：没有形象照、画面又需要出现别的人（不是角色本人）时，在那一镜 board.other_people 写是谁（如「宝宝」「医护人员的手」，1–60 字），"
    "这一镜就可以出现这个人的手、脚、身体局部或背影，不露脸、不出现正脸和侧脸，不能是角色本人，也不多出别的人；没写的镜头照旧不出现人物。自动图生视频没有商品图兜底，要先有首帧；自动生成由用户在页面上点或明确要求时才调。"
    "手动镜头把 get_shot_video_prompt 的文生视频提示词（t2v_prompt）或首帧 + 图生视频提示词交给用户，用户在网页工具生成后上传。",
    "商品作品的 product.product.info_images 是用户给的商品资料图（类别 certificate 证书、specification 参数图、dimensions 尺寸图、detail 细节图等）：证书、参数、尺寸镜头直接用对应资料图原图（set_shot_materials），不生成、不修改、不重画。",
    "导演稿采用后：先用用户新放进库的素材，其余按 素材库 → 图库搜索 → 生图 → AE 模板 补齐；每个镜头用哪条由你定；回执写明哪些是用户给的、哪些是你找的或做的。",
    "小样、排版、成片都在达芬奇（剪辑、调色、声音、导出）和 AE（标题、字幕、包装、特效）里做；ffmpeg 只用于检查和转格式。",
    "实拍原声为主、只有个别镜头要画外配音时：在那几个镜头的 board 写 dub_persona（角色名称或编号，声音就是这个角色固定的声音），只给这些镜头配音，镜头时长不动；"
    "剪辑时配音轨从 0 秒铺上（其余位置是静音），原声镜头保留素材声音；配音结果的 edit_notes 写了哪句提前进上一镜结尾，就做成声音先进、画面在本镜开头再切。",
    "口播声音：导演稿有 dialogue 声音轨就按它铺口播——每段从 material_revision_id 的 trim_start_ms–trim_end_ms 截取，放到成片 start_ms–end_ms，声音段可以跨镜头，画面仍按镜头切；"
    "声音段写了 speed_percent（用户在「配音与音乐」调的语速）就按这个倍速变速并开音调校正，和这段口播同步的实拍画面同速，保住口型；"
    "接法按 craft-resolve 的「声音轨口播衔接」。没有声音轨就用各镜头素材自己的原声。导演稿里口播要从别的素材借声音，就写进声音轨，不要只写在 board.sound 文字里。",
    "配乐只看主稿 music：有 material_revision_id 就铺这首；none 为 true 是用户明确不要配乐；空着就是还没定：按导演稿和用户意见找一首放进来（set_shot_materials 的 music），拿不准就问用户；不能自己当成不用。只有用户能选「不用配乐」。",
    "封面分两种，看开剪结果：files 写着要交 cover_vertical 的是横版封面，照后面「横版封面」那条做；没写的照这条和下面几条做。"
    "封面（可选）：封面设计（大字商品名和卖点）在达芬奇 / AE 里做进成片开头那一段，随成片一起渲染；封面图只能从渲染好的成片里截取开头 0.5 秒内的一帧（ffmpeg 抽帧要用准确换算：-vf \"scale=flags=accurate_rnd+full_chroma_int,format=rgb24\"，不加的话标 bt709 的成片截出来暗约 2 级），竖版 1080×1920 的 jpg / png，"
    "不许用 AE 或其他工具从原片另外合成。成片颜色标记统一为 sRGB（原色 bt709、传输 iec61966-2-1、矩阵 bt709）：达芬奇渲染后用 ffmpeg 只改标记不重新编码，"
    "如 -c copy -bsf:v h264_metadata=colour_primaries=1:transfer_characteristics=13:matrix_coefficients=1（H.265 用 hevc_metadata），同时设好容器的 -color_primaries bt709 -color_trc iec61966-2-1 -colorspace bt709；封面图按 sRGB 存。"
    "封面导出到开剪结果给的 cover_dir（导出/封面），用 role cover 交付，并且要在剪辑清单之前交（清单的 output_hashes 可以列上 cover）；成片通过后它就是作品封面。平台会查成片颜色标记，并把封面和成片开头 0.5 秒逐帧比色，不一致会在审阅页提示。",
    "角色封面样式：开剪结果的 cover_template（执行包 director.cover_template）有值时，封面字层必须用这个 AE 模板做：render_ae_template 的 template / version 照它，"
    "只填它列出的字段（大标题、副标题、卖点 1–3），渲染出的透明字层叠在成片开头，封面仍从渲染好的成片里截；交封面（role cover）时 metadata 带 cover_template_render（这次渲染返回的 material_revision_id）。"
    "没带或用错模板，审片页会提示。没有 cover_template 就照上面的封面做法。",
    "封面在任务通过前可以再交（同一个 role cover 再 submit_output 一次），新的一张显示在审片页，旧的留在历史里；其他交付文件交了就不能换。"
    "get_video_decision 返回 cover_redo 时，是用户只要你重做封面：按 cover_redo.note 改，重新出字层、从成片截图、再交一次 cover，不要重交小样 / 成片；新封面交上来，这条就算完成。",
    "横版封面（16:9 作品的成片任务，开剪结果写着要交 cover_vertical）：交两张。横封面：封面设计（底图 + 大标题等）盖在成片开头 0–0.5 秒，随成片一起渲染，成片时长不变，配音和字幕照常；"
    "横封面图只能从渲染好的成片开头 0.5 秒内截一帧（抽帧照上面的准确换算），1920×1080，role cover。竖封面：同一套设计改成竖版排版，1080×1440（3:4，抖音主页列表按 3:4 裁，大标题要整个落在竖封面里），"
    "role cover_vertical，单独做，不放进成片。两张都按 sRGB 存，都导出到 cover_dir，都在剪辑清单之前交，清单 output_hashes 两张都列；成片通过后两张都是作品封面。"
    "有 cover_template 时两张的字都用这个模板渲染（交每张都带 cover_template_render）：横封面的字层叠在成片开头，竖封面的叠在竖版底图上。"
    "两张在任务通过前都能再交；cover_redo 要两张都重交才算完成。平台把横封面和成片开头 0.5 秒逐帧比色，竖封面只查尺寸；缺哪张、尺寸不对、颜色不一致都会在审片页提示。"
    "开剪结果的 files 还写着要交 cover_43 时（抖音横封面 4:3），再交第三张：把 1920×1080 横封面图居中裁成 1440×1080（左右各裁 240 像素），role cover_43，不另外设计；"
    "所以这时横封面设计要把大标题和卖点都放在画面中间 1440 宽的范围里，裁完不切字。它和另外两张一样导出、交、列进 output_hashes、可重交，cover_redo 要三张都重交，平台只查它的尺寸。",
    "发布文案：成片任务里、交成片之前，用 save_publish_copy 给作品存一份通用发布文案（不按平台分，不填 channel）：角色作品按 studio.persona.publish-copy 写，商品作品按 studio.product.publish-copy 写；"
    "已经存过的，内容有变再改。用户会在交付页看和改，成品包里每个平台都带这份。",
    "素材能不能公开、能不能给模型用，只有用户能在素材详情里改；不能用 REST 或别的办法代改。开剪报 video_asset_kind_or_rights_invalid 时，把报错里说的是哪条素材、该怎么处理原样告诉用户，等用户改好再重做用到它的素材。",
    "角色片段（只在成片）：开剪结果的 persona_clips（执行包 director.persona_clips，素材 role persona_clip）有值时，收尾片段（slot outro）原样接在成片最后，"
    "进门片段（slot intro）原样放在最前面：不裁、不变速、不缩放变形；这段用片段自带的声音，配音和配乐在片段开始前收完（配乐淡出），不压在片段上；整片响度照旧。"
    "设了进门片段，封面改成从进门片段结束后 0.5 秒内截。剪辑清单写 persona_clips：[{slot, material_revision_id, start_ms, end_ms}]（成片上的起止毫秒），这几段不写进 timeline。"
    "成片时长应等于通过的小样时长加这几段。persona_note 写「本作品没有角色收尾」就什么都不加。",
    "剪辑照导演稿：画面内容要变就先存新导演稿；导演稿没写的细节和网络素材署名写进回执。",
    "文件都在项目文件夹里：准备素材（materialize_inputs）给每条素材的原始路径，直接导入达芬奇 / AE，只读，不复制；"
    "临时渲染、AE 单镜头、达芬奇 / AE 工程和剪辑清单放 work_dir（<项目>/工作/<作品>/任务N/），小样导出到 导出/小样、成片导出到 导出/成片；"
    "交付结果（submit_output）给文件的绝对路径 path，平台原地检查登记，交付后别再改或移动这个文件。work_dir 里的文件都留着，平台和你都不删。",
    "达芬奇一次只剪一部：领任务（claim_execution）回 video_edit_queue_busy 就是别的作品正在剪，过几分钟再领；剪辑中每 20 分钟内至少 report_progress 一次，30 分钟没动静会被当成中断、让给别的作品。"
    "达芬奇项目列表每个作品只留一个：开剪先删掉本作品更早任务的达芬奇项目（<作品>-<作品号>-任务N，它们的 .drp 在硬盘上），重开检查完马上删掉 -reopen 那份。",
    "复刻参考视频：brief.reference 有值或用户给了参考视频，先 analyze_reference_video / get_reference_video 拿本机拆解，按 studio.video.reference-breakdown 写整体分析、时间线和拍摄清单（save_reference_breakdown），再写导演稿："
    "结构和节奏照参考，口播换成本作品的说法，每镜写 board.source_kind；参考里的证书、医院、成分只记成需要品牌真实资料，不照抄、不生成；参考视频的原画面和水印不进成片。",
    "写人物镜头的提示词按 studio.video.prompt-direction：board.attitude 先写人物态度和对谁说，再写一两个关键反应；首帧按 拍摄方式 / 人物 / 动作与镜头 / 场景 四段写；商品图管外观、人物图管长相，提示词不重复描述包装。",
    "HLG 还原（必做）：每段实拍先用 ffprobe 看 color_transfer；是 arib-std-b67（iPhone HLG）的，项目色彩科学用 davinciYRGB（不做色彩管理），只给这些片段 SetLUT(1, \"MCP/iphone-hlg-apple-sdr.cube\")，"
    "不要再用 iphone-hlg-apple-sdr-render.cube 或 sdr-render-comp.cube（达芬奇 MCP/ 下有就删掉）。验收拿渲染出来的文件抽帧，和手机自己的显示帧（AVAssetImageGenerator）比亮度，不看达芬奇静帧。",
    "AE 数据电平（必做）：AE 导出的每个 RGB 素材（叠层、包装、字幕、整屏片尾卡、封面卡，有没有透明都算）导入后先 SetClipProperty(\"Data Level\", \"Full\")，"
    "再用 GetClipProperty(\"Data Level\") 确认是 Full，然后上时间线；留 Auto 会被当 Video 电平读：透明叠层把下面整片拉暗约 19 级，不透明的卡对比度被拉大、黑白两头削掉。普通 SDR 实拍不套补偿 LUT。AI 画面：渲染一次后抽帧和原图比，暗了才补。"
    "达芬奇里缺 HLG LUT 就先从仓库 craft_skills/craft-resolve/luts/ 拷到达芬奇 LUT 文件夹的 MCP/ 下"
    "（做法见 craft-resolve techniques/color.md「iPhone HLG 还原」「AE 叠层数据电平设 Full」）。平台交付时会逐镜头拿成片和原片同一时刻比平均亮度和亮部。",
    "素材统一（必做，粗剪后、导出小样前）：颜色只做校正和匹配——曝光、白平衡拉正，同一场景的镜头用色彩组对齐到一个参考镜头；不做风格化调色，素材正常且彼此一致就不动。"
    "声音：实拍对白逐段拉到约 −16 LUFS，只有明显底噪才轻度降噪，只有一边声道有声的修成两边；之后再按现有混音标准（整片约 −14 LUFS、真峰值 ≤ −1 dBTP）。",
    "小样、成片的回执逐镜头写明：哪些套了 HLG 还原、哪些 AE 素材设了数据电平 Full、哪些做了颜色校正（改了什么）、哪些对白段调了音量（调了多少）；没动的写没动。平台交付时会逐镜头查过曝、亮度跳变和对白音量，提示在审阅页。",
    "交小样、成片时 metadata 带 shot_sources（JSON 字符串）：每个用实拍画面的镜头一条 {\"shot_id\",\"material_revision_id\",\"source_in_ms\"}，"
    "source_in_ms 是该镜头在达芬奇时间线上那个片段的源入点（脚本读时间线片段的 GetLeftOffset / GetSourceStartFrame 换成毫秒）；平台按它在原片里取和成片同一时刻的帧比亮度，"
    "不报就只能按镜头内位置估计、可能误报。剪辑清单交上来后平台会再按清单的 trim_start_ms（和 speed_percent）重算一次。",
]
EXECUTOR = "codex-video-production"
_KEEPS_DRAFT = {"material", "edit_prep", "cover"}


def _fail(code: str, message: str, status: int = 409):
    raise HTTPException(status, {"code": code, "message": message})


def _records(db: Session) -> dict:
    row = db.get(SystemSetting, KEY)
    return dict(row.value or {}) if row else {}


def _unit_record(db: Session, unit_id: int) -> dict:
    return copy.deepcopy(_records(db).get(str(unit_id)) or {"decisions": [], "tasks": []})


def _put(db: Session, unit_id: int, record: dict) -> None:
    row = db.get(SystemSetting, KEY)
    if row is None:
        row = SystemSetting(key=KEY, value={})
        db.add(row)
    value = dict(row.value or {})
    value[str(unit_id)] = record
    row.value = value
    flag_modified(row, "value")
    db.flush()


def _latest(db: Session, unit_id: int) -> ContentMasterRevision | None:
    return db.scalar(select(ContentMasterRevision).where(ContentMasterRevision.content_unit_id == unit_id)
                     .order_by(ContentMasterRevision.revision_no.desc()).limit(1))


def _keeps_draft(master: ContentMasterRevision) -> bool:
    summary = master.edit_summary_json or {}
    return summary.get("video_chain") in _KEEPS_DRAFT or bool({"voiceover", "dedupe", "auto_handoff", "speech_speed"} & summary.keys())


def draft_root(db: Session, master: ContentMasterRevision | None) -> ContentMasterRevision | None:
    """The 导演稿 the current version stands on: walk back past saves that kept the picture content."""
    while master is not None and master.parent_revision_id:
        parent = db.get(ContentMasterRevision, master.parent_revision_id)
        # Re-saving identical content (e.g. clicking save without edits) is not a new 导演稿.
        if parent is None or not (_keeps_draft(master) or master.payload_hash == parent.payload_hash):
            break
        master = parent
    return master


def _decision(record: dict, stage: str, target_id: int) -> dict | None:
    return next((item for item in reversed(record["decisions"]) if item["stage"] == stage and item["target_id"] == target_id), None)


def _task(db: Session, record: dict) -> tuple[dict | None, CreativeExecution | None]:
    if not record["tasks"]:
        return None, None
    task = record["tasks"][-1]
    return task, db.get(CreativeExecution, task["execution_id"])


def _cover_redo(db: Session, record: dict, execution: CreativeExecution) -> dict | None:
    """The user's open request to redo only the cover of this task, settled once every cover of the task is handed in after it."""
    from .web_video_handoff import cover_roles

    asked = record.get("cover_redo")
    if not asked or asked.get("execution_id") != execution.id or execution.state not in {"claimed", "in_progress", "blocked", "result_ready"}:
        return None
    at = datetime.fromisoformat(asked["at"]).replace(tzinfo=None)
    package = db.get(CreativeExecutionPackage, execution.package_id)
    roles = set(cover_roles(package.package_json) if package else ()) or {"cover"}
    newer = set(db.scalars(select(CreativeExecutionOutput.role_id).where(CreativeExecutionOutput.execution_id == execution.id,
                                                                         CreativeExecutionOutput.role_id.in_(roles), CreativeExecutionOutput.created_at > at)))
    return None if newer == roles else {"note": asked.get("note") or "", "at": asked["at"], "by": asked.get("by")}


def _finished(view: dict) -> dict:
    return {**view, "state": "done", "label": "已定稿", "locked": True}


# Accepting the 成片 files already locks the work; the cover written in that same approval must still get through.
_finalizing: contextvars.ContextVar[int | None] = contextvars.ContextVar("video_chain_finalizing", default=None)


def locked(db: Session, unit_id: int) -> bool:
    """An approved 成片 is final for good; changes go into a copy of the unit instead."""
    return _finalizing.get() != unit_id and bool(_state(db, unit_id).get("locked"))


def edit_progress(db: Session) -> tuple[set[int], dict[int, int]]:
    """Works whose 成片 is approved, and each other work's current edit task; earlier tasks were replaced and stay unanswered for good."""
    finished, current = set(), {}
    for key, record in _records(db).items():
        unit_id = int(key)
        if _state(db, unit_id).get("locked"):
            finished.add(unit_id)
        elif record.get("tasks"):
            current[unit_id] = record["tasks"][-1]["execution_id"]
    return finished, current


def state(db: Session, user: User, project_id: int, unit_id: int) -> dict:
    from .content_masters import owned_unit

    owned_unit(db, project_id, unit_id, user)
    return _state(db, unit_id)


def _state(db: Session, unit_id: int) -> dict:
    record = _unit_record(db, unit_id)
    root = draft_root(db, _latest(db, unit_id))
    if root is None or (root.edit_summary_json or {}).get("video_chain") != "draft":
        return {"state": "not_started", "label": "待开始", "detail": "在接了 MCP 的第三方模型里说「做这个视频」开始：先写导演稿和素材需求"}
    view = {"draft_master_id": root.id, "draft_revision_no": root.revision_no}
    decided = _decision(record, "draft", root.id)
    if decided is None:
        return {**view, "state": "draft_review", "label": "导演稿待你看", "detail": "看分镜和素材需求；有素材就放进素材库，然后采用或写修改意见"}
    if decided["decision"] == "changes":
        return {**view, "state": "draft_changes", "label": "导演稿按你的意见修改中", "notes": decided["notes"]}
    task, execution = _task(db, record)
    if task is None or task["draft_master_id"] != root.id:
        return {**view, "state": "making", "label": "制作中", "detail": "选素材、配音，准备剪小样"}
    phase = "sample" if task["phase"] == "rough_cut" else "final"
    view.update(execution_id=execution.id, execution_state=execution.state, phase=task["phase"])
    notes = _decision(record, phase, execution.id)
    if (notes is None or notes["decision"] != "approve") and _approving(record, execution.id):
        return {**view, "state": "approving", "label": "正在通过…",
                "detail": "用户已点通过，平台正在采纳成果文件，稍后再查；这不是「待你看」，不要当成还没通过"}
    if execution.state in {"prepared", "claimed", "in_progress"}:
        return {**view, "state": "making" if phase == "sample" else "finishing", "label": "剪小样中" if phase == "sample" else "排版中"}
    if execution.state == "result_ready" and notes and notes["decision"] == "approve":
        return {**view, "state": "finishing", "label": "排版中"} if phase == "sample" else _finished(view)
    if execution.state == "result_ready":
        if notes and notes["decision"] == "changes":
            return {**view, "state": f"{phase}_changes", "label": "小样按你的意见修改中" if phase == "sample" else "成片按你的意见修改中", "notes": notes["notes"]}
        redo = _cover_redo(db, record, execution)
        if redo:
            view["cover_redo"] = redo
        return {**view, "state": f"{phase}_review", "label": "小样待你看" if phase == "sample" else "成片待你看"}
    if execution.state == "accepted":
        return {**view, "state": "finishing", "label": "排版中"} if phase == "sample" else _finished(view)
    return {**view, "state": "error", "label": "出错", "detail": execution.safe_reason or execution.state}


def cut_location(db: Session, user: User, project_id: int, unit_id: int, output_id: int):
    """The file behind the 小样 / 成片 the page plays: the library record once accepted, else where the model exported it."""
    from . import creative_executions, materials

    current = state(db, user, project_id, unit_id)
    output = db.get(CreativeExecutionOutput, output_id)
    if output is None or output.execution_id != current.get("execution_id") or output.role_id not in {"rough_cut", "final"}:
        _fail("video_chain_cut_not_found", "找不到这条片子", 404)
    if output.material_revision_id:
        revision = db.get(MaterialRevision, output.material_revision_id)
        path = materials.local_file_checked(db, revision) if revision is not None else None
        if path is not None:
            return path
    if not output.staging_key.startswith("/"):
        _fail("video_chain_cut_not_found", "片子不在项目文件夹里", 404)
    execution = db.get(CreativeExecution, output.execution_id)
    try:
        creative_executions.check_output(execution.owner_user_id, execution.id, output.staging_key, output.size_bytes, output.content_hash)
    except HTTPException as exc:
        if (exc.detail or {}).get("code") == "video_chain_output_changed":
            raise
        _fail("video_chain_cut_not_found", "片子文件不在了", 404)
    return Path(output.staging_key)


def file_as_common(db: Session, user: User, project_id: int, unit_id: int, revision_id: int) -> dict:
    """The video model judged this material generic; it moves to 通用素材库 on the Mac."""
    from . import project_folders
    from .content_masters import owned_unit

    owned_unit(db, project_id, unit_id, user, mutate=True)
    revision = db.get(MaterialRevision, revision_id)
    used = db.scalar(select(ProjectMaterialReference.id).where(ProjectMaterialReference.project_id == project_id,
                     ProjectMaterialReference.material_revision_id == revision_id, ProjectMaterialReference.status == "active"))
    if revision is None or used is None:
        _fail("video_chain_material_not_in_project", "这条素材不在本项目里", 404)
    if project_folders.is_output(revision):
        _fail("video_chain_output_not_material", "小样 / 成片是成果，不放进通用素材库", 422)
    return project_folders.to_common(db, revision)


APPROVING_STALE_SECONDS = 300


def _clear_approving(db: Session, unit_id: int) -> None:
    record = _unit_record(db, unit_id)
    if record.pop("approving", None) is not None:
        _put(db, unit_id, record)
        db.commit()


def _approving(record: dict, target_id: int) -> bool:
    marker = record.get("approving") or {}
    if marker.get("target_id") != target_id:
        return False
    try:
        started = datetime.fromisoformat(marker["at"])
    except (KeyError, ValueError):
        return False
    # A marker left behind by a restart must not hold the work in 处理中 forever.
    return (datetime.now(UTC) - started).total_seconds() < APPROVING_STALE_SECONDS


def decide(db: Session, user: User, project_id: int, unit_id: int, stage: str, decision: str, notes: list[dict]) -> dict:
    """The user's answer at one of the three stops. 通过 on 小样 / 成片 accepts that task's outputs."""
    from .content_masters import owned_unit

    owned_unit(db, project_id, unit_id, user, mutate=True)
    current = state(db, user, project_id, unit_id)
    expected = {"draft": "draft_review", "sample": "sample_review", "final": "final_review"}[stage]
    # Until the 成片 is final the user may send the 导演稿 back from any later stop.
    back_to_draft = stage == "draft" and decision == "changes" and "draft_master_id" in current and not current.get("locked")
    if current["state"] not in {expected, expected.replace("review", "changes")} and not back_to_draft:
        _fail("video_chain_not_waiting", f"现在不在等你看{ {'draft': '导演稿', 'sample': '小样', 'final': '成片'}[stage] }")
    if decision == "changes" and not any(str(item.get("note") or "").strip() for item in notes):
        _fail("video_chain_notes_required", "写一下要改哪里", 422)
    target = current["draft_master_id"] if stage == "draft" else current["execution_id"]
    if stage == "final" and decision == "approve" and current.get("cover_redo"):
        _fail("video_chain_cover_redo_pending", "封面重做中，等新封面交上来再通过")
    accepted = None
    if decision == "approve" and stage != "draft":
        # Accepting the output files takes a while; saying so first keeps the page and the model from reading 「待你看」 meanwhile.
        record = _unit_record(db, unit_id)
        record["approving"] = {"stage": stage, "target_id": target, "by": user.email, "at": datetime.now(UTC).isoformat()}
        _put(db, unit_id, record)
        db.commit()
        try:
            _accept_outputs(db, user, project_id, unit_id, target)
            accepted = True
        except HTTPException as exc:
            # Voice or timing saved after the 小样 (prep for the 成片) makes its source older than the master;
            # the approval still stands, the 小样 file is already in 导出/小样, and the 成片 is cut from the newest master.
            db.rollback()
            if stage != "sample" or (exc.detail or {}).get("code") != "creative_source_not_current":
                _clear_approving(db, unit_id)
                raise
            accepted = False
        except Exception:
            db.rollback()
            _clear_approving(db, unit_id)
            raise
    if stage == "final" and accepted:
        token = _finalizing.set(unit_id)
        try:
            _adopt_cover(db, user, project_id, unit_id, target)
        except HTTPException:
            # The cut is approved either way; a cover that cannot be written must not undo that.
            db.rollback()
        finally:
            _finalizing.reset(token)
    record = _unit_record(db, unit_id)
    record.pop("approving", None)
    record["decisions"].append({"stage": stage, "target_id": target, "decision": decision, "outputs_accepted": accepted,
                                "notes": [{"time_ms": item.get("time_ms"), "note": str(item.get("note") or "")[:2000]} for item in notes][:50],
                                "by": user.email, "at": datetime.now(UTC).isoformat()})
    _put(db, unit_id, record)
    if stage != "draft" and decision == "changes":
        from . import video_lessons

        video_lessons.record_notes(db, user, project_id, unit_id, stage, target, notes[:50])
    db.commit()
    if stage == "final" and accepted:
        from . import finished_video

        try:
            finished_video.send_to_review(db, user, project_id, unit_id, target)
        except Exception:  # noqa: BLE001 The approval stands; a candidate that cannot be frozen shows as missing in 审阅与交付.
            db.rollback()
            logging.getLogger(__name__).warning("finished video candidate not frozen: unit=%s execution=%s", unit_id, target, exc_info=True)
    if stage == "final" and decision == "approve":
        from . import project_folders

        try:
            project_folders.archive_raw(db, project_id)
        except Exception:  # noqa: BLE001 Filing the raw folder must never undo the approval; failures stay 待归档.
            db.rollback()
    return state(db, user, project_id, unit_id)


def redo_cover(db: Session, user: User, project_id: int, unit_id: int, note: str) -> dict:
    """Sends only the cover of the 小样 / 成片 under review back; the cut itself stays waiting for the user."""
    from .content_masters import owned_unit

    owned_unit(db, project_id, unit_id, user, mutate=True)
    current = state(db, user, project_id, unit_id)
    if current["state"] not in {"sample_review", "final_review"}:
        _fail("video_chain_not_waiting", "现在不在等你看小样或成片")
    record = _unit_record(db, unit_id)
    record["cover_redo"] = {"execution_id": current["execution_id"], "note": note.strip()[:2000], "by": user.email,
                            "at": datetime.now(UTC).isoformat()}
    _put(db, unit_id, record)
    db.commit()
    return state(db, user, project_id, unit_id)


def _adopt_cover(db: Session, user: User, project_id: int, unit_id: int, execution_id: int) -> None:
    """The 成片's covers become the work's covers (a landscape work also has a vertical one); no cover leaves the old one."""
    def accepted(role_id: str):
        return db.scalar(select(CreativeExecutionOutput).where(CreativeExecutionOutput.execution_id == execution_id,
                                                               CreativeExecutionOutput.role_id == role_id, CreativeExecutionOutput.state == "accepted")
                         .order_by(CreativeExecutionOutput.attempt_no.desc()).limit(1))
    cover, vertical, four_three = accepted("cover"), accepted("cover_vertical"), accepted("cover_43")
    master = _latest(db, unit_id)
    if cover is None or cover.material_revision_id is None or master is None:
        return
    document = copy.deepcopy(master.payload_json)
    wanted = {"material_revision_id": cover.material_revision_id,
              **({"vertical_material_revision_id": vertical.material_revision_id} if vertical and vertical.material_revision_id else {}),
              **({"four_three_material_revision_id": four_three.material_revision_id} if four_three and four_three.material_revision_id else {})}
    if document.get("cover") == wanted:
        return
    document["cover"] = wanted
    _save(db, user, project_id, unit_id, document, {"video_chain": "cover", "output_id": cover.id})


def work_covers(db: Session, unit_id: int) -> dict:
    """The work's current covers for the 交付 page (a landscape work also has a 3:4 one); images are fetched by material id."""
    master = _latest(db, unit_id)
    document = (master.payload_json or {}) if master else {}

    def ref(revision_id):
        revision = db.get(MaterialRevision, revision_id) if type(revision_id) is int else None
        return {"material_id": revision.material_id, "material_revision_id": revision.id} if revision else None
    cover = document.get("cover") or {}
    return {"aspect": ":".join(str(value) for value in document.get("aspect_ratio") or [9, 16]),
            "cover": ref(cover.get("material_revision_id")), "cover_43": ref(cover.get("four_three_material_revision_id")),
            "cover_vertical": ref(cover.get("vertical_material_revision_id"))}


def _accept_outputs(db: Session, user: User, project_id: int, unit_id: int, execution_id: int) -> None:
    from . import creative_executions

    unit = db.get(ContentUnit, unit_id)
    outputs = db.scalars(select(CreativeExecutionOutput).where(CreativeExecutionOutput.execution_id == execution_id)
                         .order_by(CreativeExecutionOutput.attempt_no)).all()
    latest = {}
    for output in outputs:
        latest[(output.role_id, output.output_index)] = output
    for output in latest.values():
        if output.state != "staged":
            continue
        execution = db.get(CreativeExecution, execution_id)
        db.refresh(execution)
        # Materials are allowed by default; project files (projects, manifests) stay private as the platform requires.
        shareable = output.kind in {"video", "image", "audio"}
        rights = {"rights_status": "cleared", "public_use_allowed": shareable, "model_use_allowed": shareable}
        payload = {"expected_revision": execution.revision_no, "decision": "accept", "rights": rights,
                   "title": f"{unit.title} · {output.role_id}"[:255], "attach_to_project": output.role_id in {"rough_cut", "final", "cover", "cover_43", "cover_vertical"}}
        # One input that cannot be published must not also take away model use, or the next phase cannot build on this cut.
        fallbacks = [{"rights_status": "cleared", "public_use_allowed": False, "model_use_allowed": shareable},
                     {"rights_status": "cleared", "public_use_allowed": False, "model_use_allowed": False}]
        while True:
            try:
                creative_executions.decide_output(db, project_id, unit_id, execution_id, output.id, payload, user)
                break
            except HTTPException as exc:
                if (exc.detail or {}).get("code") != "creative_execution_rights_escalation" or not fallbacks:
                    raise
                db.rollback()
                db.refresh(execution)
                payload = {**payload, "expected_revision": execution.revision_no, "rights": fallbacks.pop(0)}


def _ensure_references(db: Session, user: User, project_id: int, revision_ids: set[int]) -> None:
    for revision_id in revision_ids:
        row = db.scalar(select(ProjectMaterialReference).where(ProjectMaterialReference.project_id == project_id,
                                                               ProjectMaterialReference.material_revision_id == revision_id))
        if row is None:
            db.add(ProjectMaterialReference(project_id=project_id, material_revision_id=revision_id, origin="system_reference",
                                            status="active", attached_by=user.email, note="视频导演稿使用"))
        elif row.status != "active":
            row.status = "active"
    db.flush()


def _save(db: Session, user: User, project_id: int, unit_id: int, document: dict, summary: dict) -> int:
    from .content_masters import dialogue_material_problems, save_revision
    from .edit_handoff import _save as save_on
    from .video_documents import _expected_media

    dialogue_problems = dialogue_material_problems(db, document)
    if dialogue_problems:
        _fail("video_chain_dialogue_material_invalid", "声音轨不对：" + "；".join(dialogue_problems), 422)
    revisions = {ref["material_revision_id"] for ref in _expected_media(document)}
    for revision_id in revisions:
        if db.get(MaterialRevision, revision_id) is None:
            _fail("video_chain_material_unknown", f"素材版本 {revision_id} 不存在", 422)
    _ensure_references(db, user, project_id, revisions)
    master = _latest(db, unit_id)
    if master is not None:
        return save_on(db, user, project_id, unit_id, master, document, {}, edit_summary=summary)
    refs = [{**ref, "content_hash": db.get(MaterialRevision, ref["material_revision_id"]).content_hash} for ref in _expected_media(document)]
    saved = save_revision(db, project_id=project_id, unit_id=unit_id, user=user, payload={
        "expected_revision": 0, "idempotency_key": f"video-chain:{uuid.uuid4().hex}", "payload_schema": "video.master.v2",
        "payload": document, "source_kind": "user_edit", "edit_summary": summary, "asset_refs": refs, "evidence_refs": []})
    return saved["id"]


def _text_of(master: ContentMasterRevision) -> str:
    def walk(node) -> str:
        if isinstance(node, dict):
            return (node.get("text") or "") + "".join(walk(child) for child in node.get("content") or [])
        return ""

    blocks = ((master.payload_json or {}).get("document") or {}).get("blocks") or []
    return "\n".join(filter(None, (walk(block) for block in blocks)))


def brief(db: Session, user: User, project_id: int, unit_id: int) -> dict:
    from ..models import Fact, FactPackItem
    from . import craft_skills, fact_templates, product_video, project_folders, reference_video, video_lessons, voiceover
    from .persona_brief import persona_brief
    from .content_masters import owned_unit
    from .project_brief import current_brief
    from .project_evidence import current_boundary

    project, unit = owned_unit(db, project_id, unit_id, user)
    product_video.require_persona(db, unit_id)
    row = current_brief(db, project_id)
    boundary = current_boundary(db, project_id)
    facts = []
    if boundary is not None:
        # Quotes and expert opinions have no Fact row; they carry who said it in the frozen snapshot.
        facts = [statement or f"{(snapshot or {}).get('attribution')}：{(snapshot or {}).get('statement')}"
                 for statement, snapshot in db.execute(select(Fact.statement, FactPackItem.snapshot_json).select_from(FactPackItem)
                                                       .outerjoin(Fact, FactPackItem.fact_id == Fact.id)
                                                       .where(FactPackItem.fact_pack_id == boundary.fact_pack_id)
                                                       .order_by(FactPackItem.sort_order).limit(80))]
    siblings = []
    for other in db.scalars(select(ContentUnit).where(ContentUnit.project_id == project_id, ContentUnit.id != unit_id)):
        master = _latest(db, other.id)
        if master is not None and master.payload_schema.startswith("text."):
            siblings.append({"unit": other.title, "text": _text_of(master)[:8000]})
    tree = project_folders.tree(db)
    durations = dict(db.execute(select(MaterialRevision.id, MaterialRevision.duration_ms)
                                .where(MaterialRevision.id.in_([item["material_revision_id"] for item in tree["items"]]))).all())
    materials = [{**{key: item[key] for key in ("material_id", "material_revision_id", "title", "kind", "mime_type", "library", "group", "folder")},
                  "duration_ms": durations.get(item["material_revision_id"])}
                 for item in tree["items"] if item["library"] != "project" or item["project_id"] == project_id]
    master = _latest(db, unit_id)
    return {"project": {"id": project.id, "title": project.title, "objective": project.objective},
            "unit": {"id": unit.id, "title": unit.title, "channel_id": unit.channel_id},
            "brief": {key: getattr(row, key) for key in ("objective", "primary_audience", "core_message", "angle")} if row else None,
            "facts": facts, "fact_templates": fact_templates.brief_rules(db, project_id), "source_texts": siblings,
            "voice_settings": {**voiceover.settings_for(db, unit), "pronunciation_help": voiceover.PRONUNCIATION_HELP},
            "materials": materials, "state": state(db, user, project_id, unit_id),
            "current_master": {"id": master.id, "revision_no": master.revision_no, "payload": master.payload_json} if master else None,
            "review_url": f"/projects/{project_id}/units/{unit_id}/production?workstep=plan", "rules": RULES,
            "platform_skills": craft_skills.platform_skills(db, unit),
            # Product works add their category, style, material mode and image-to-video route; persona works get null.
            "product": product_video.direction(db, unit_id),
            # Who the work speaks as; null when it belongs to no persona.
            "persona": persona_brief(db, user, unit),
            # The reference video being cloned, when the user attached one; null otherwise.
            "reference": reference_video.brief_view(db, unit_id),
            # Approved lessons from earlier rework, plus this work's sent-back notes not yet turned into a lesson.
            "lessons": video_lessons.brief_view(db, user, unit_id),
            "lessons_rule": "先读 lessons.active，适用范围（scope）对得上的照做；交付回执写明这次用了哪几条经验（id）。"
                            "按退回意见（lessons.open_rework_records）改好交付后，调用 propose_lesson 把原因归纳成以后通用的做法；"
                            "和已有经验是同一个原因就用 same_as_lesson_id 挂上去，不要新建。经验要用户同意后才生效。"}


def save_draft(db: Session, user: User, project_id: int, unit_id: int, payload: dict, note: str | None) -> dict:
    from . import project_folders
    from .video_documents import VideoDocumentError, canonical_payload

    document = copy.deepcopy(payload)
    document.pop("postproduction", None)
    try:
        canonical_payload(document)
    except VideoDocumentError as exc:
        _fail("video_chain_draft_invalid", f"导演稿格式不对：{exc}", 422)
    master_id = _save(db, user, project_id, unit_id, document, {"video_chain": "draft", "note": (note or "")[:2000]})
    master = db.get(ContentMasterRevision, master_id)
    project_folders.write_director_draft(db, project_id, master.revision_no, master.payload_json)
    db.commit()
    return {"master_id": master_id, "revision_no": master.revision_no, **state(db, user, project_id, unit_id)}


def _approved_master(db: Session, user: User, project_id: int, unit_id: int) -> tuple[ContentMasterRevision, dict]:
    current = state(db, user, project_id, unit_id)
    if current["state"] in {"not_started", "draft_review", "draft_changes"}:
        _fail("video_chain_draft_not_approved", "导演稿还没被采用，先等用户在页面上采用")
    return _latest(db, unit_id), current


def set_materials(db: Session, user: User, project_id: int, unit_id: int, picks: dict[str, int], music: int | None = None,
                  silent_durations: dict[str, int] | None = None, no_music: bool = False) -> dict:
    master, _current = _approved_master(db, user, project_id, unit_id)
    document = copy.deepcopy(master.payload_json)
    shots = {shot["id"]: shot for shot in document["shots"]}
    unknown = sorted(set(picks) - shots.keys())
    if unknown:
        _fail("video_chain_shot_unknown", f"没有这些镜头：{', '.join(unknown)}", 422)
    for shot_id, revision_id in picks.items():
        revision = db.get(MaterialRevision, revision_id)
        if revision is None or revision.material.status != "active":
            _fail("video_chain_material_unknown", f"素材版本 {revision_id} 不可用", 422)
        shots[shot_id]["source_material_revision_id"] = revision_id
    for shot_id, length in (silent_durations or {}).items():
        # Only shots without a line: their length is pacing (how long the ending stays), the voice sets the rest.
        if shot_id not in shots or shots[shot_id].get("script_block_id") or not 1000 <= length <= 15000:
            _fail("video_chain_silent_shot_invalid", f"{shot_id} 不是无人声镜头，或时长不在 1–15 秒", 422)
        shots[shot_id]["duration_ms"] = length
    if music is not None:
        revision = db.get(MaterialRevision, music)
        if revision is None or revision.material.status != "active" or revision.material.kind != "audio":
            _fail("video_chain_material_unknown", f"音乐素材版本 {music} 不可用", 422)
        document["music"] = {"material_revision_id": music}
    elif no_music:
        document["music"] = {"none": True}
    master_id = _save(db, user, project_id, unit_id, document, {"video_chain": "material", "picks": picks, "music": music, "no_music": no_music, "silent_durations": silent_durations})
    db.commit()
    missing = [shot["id"] for shot in document["shots"] if not shot.get("source_material_revision_id")]
    return {"master_id": master_id, "missing_shots": missing}


# Asked at the size the cover is used at: Grok returned 2048-side requests at another size, which the platform refuses.
STILL_SIZES = {"16:9": (1920, 1080), "9:16": (1080, 1920), "3:4": (1080, 1440), "4:3": (1440, 1080), "1:1": (1440, 1440)}
FALLBACK_PIXELS = 1024 * 1024
# Models measured to return only about one megapixel; asking them more just pays for a refused image first.
MODEL_MAX_PIXELS = {"grok-imagine-image": FALLBACK_PIXELS}


def generate_image(db: Session, user: User, project_id: int, unit_id: int, prompt: str, label: str, aspect_ratio: str | None = None) -> dict:
    """One still with the 封面生图 model, in the work's aspect unless told otherwise, at the size a cover is used at."""
    from . import model_capability_routing, model_registration, project_folders
    from .material_autofill import _Images
    from .media_dimensions import canonical_aspect_ratio

    if aspect_ratio is None:
        master = _latest(db, unit_id)
        ratio = (master.payload_json or {}).get("aspect_ratio") if master and master.payload_schema == "video.master.v2" else None
        aspect_ratio = ":".join(str(value) for value in ratio) if isinstance(ratio, list) and len(ratio) == 2 else "9:16"
    aspect_ratio = canonical_aspect_ratio(aspect_ratio)
    images = _Images(db, user, project_id, aspect_ratio=aspect_ratio)
    view = model_capability_routing.configuration_view(db)
    chosen = model_registration.uses()["cover_image"]["profile"]
    profile = view["profiles"].get(chosen) if chosen else None
    note = None
    if profile and profile["enabled"] and profile["capabilities"]["image_generation"]["declared"] and profile["capabilities"]["image_generation"]["configured"]:
        images.route = {"selected_profile": chosen, "configuration_mode": "custom",
                        "parameters": {**((images.route or {}).get("parameters") or {"items": 1, "aspect_ratio": aspect_ratio}),
                                       "items": 1, "aspect_ratio": aspect_ratio}}
    else:
        note = "封面生图没设置或不可用，沿用上一次的生图模型"
    if images.route is None:
        raise HTTPException(409, {"code": "material_autofill_no_image_model"})
    width, height = STILL_SIZES[aspect_ratio]
    ceiling = (view["policies"]["limits"].get("image_generation") or {}).get("max_pixels") or FALLBACK_PIXELS
    binding = (view["profiles"].get(images.route["selected_profile"]) or {}).get("capability_bindings", {}).get("image_generation") or {}
    model_limit = MODEL_MAX_PIXELS.get(binding.get("model_id"))
    images.route["parameters"]["pixels"] = min(width * height, ceiling, model_limit or ceiling)
    if model_limit is not None and model_limit < width * height:
        note = "；".join(filter(None, [note, f"这个模型最多出约 100 万像素，没按 {width}×{height} 出"]))
    try:
        revision_id = images.make(prompt, label)
    except HTTPException as exc:
        # A definite refusal, or an image returned at another size, is retried once smaller; an uncertain send never is.
        refused = images.task is not None and images.task["state"] in {"failed", "unavailable"}
        wrong_size = exc.detail in {"generation_output_aspect_mismatch", "generation_output_limit_exceeded"}
        if not ((refused or wrong_size) and images.route["parameters"]["pixels"] > FALLBACK_PIXELS):
            raise
        images.route["parameters"]["pixels"] = FALLBACK_PIXELS
        revision_id = images.make(prompt, label)
        note = "；".join(filter(None, [note, f"模型出不了 {width}×{height}，按 100 万像素出了"]))
    revision = db.get(MaterialRevision, revision_id)
    project_folders.store_new(db, revision, project_id, "图片/图片素材")
    from PIL import Image

    from .materials import local_file_checked

    width, height = revision.width, revision.height
    if width is None:
        path = local_file_checked(db, revision)
        if path is not None:
            with Image.open(path) as image:
                width, height = image.size
    return {"material_id": revision.material_id, "material_revision_id": revision_id, "width": width, "height": height,
            "aspect_ratio": aspect_ratio, "provider": images.task["provider_key"], "model_id": images.task["model_id"],
            **({"model_note": note} if note else {})}


def accept_candidate(db: Session, user: User, project_id: int, run_id: int, segment_id: str, candidate_id: str) -> dict:
    from . import material_matching

    return material_matching.accept(db, user, run_id, {"segment_id": segment_id, "candidate_id": candidate_id, "project_id": project_id,
                                                       "public_use_allowed": True, "model_use_allowed": True, "commercial_use_allowed": True})


def voiceover(db: Session, user: User, project_id: int, unit_id: int, lines: list[str] | None = None) -> dict:
    from . import voiceover as voice

    _approved_master(db, user, project_id, unit_id)
    result = voice.generate(db, user, project_id, unit_id, lines)
    revision = db.get(MaterialRevision, result["material_revision_id"])
    return {**{key: result[key] for key in ("material_revision_id", "master_id", "duration_ms", "has_timing")},
            "lines": (revision.metadata_json or {}).get("subtitles_srt"), **({"redub": result["redub"]} if "redub" in result else {})}


def prepare_edit(db: Session, user: User, project_id: int, unit_id: int, phase: str, ae_shot_ids: list[str],
                 alpha_shot_ids: list[str], notes: str | None) -> dict:
    """Records the DaVinci / AE split and opens the edit task: 小样 (rough_cut) first, 成片 (final) after 小样 is approved."""
    from . import project_folders
    from .edit_handoff import _postproduction
    from .web_video_handoff import prepare_edit as open_task

    master, current = _approved_master(db, user, project_id, unit_id)
    # A 成片 sent back (final_changes) is redone as a new task on top of the same approved 小样.
    if phase == "final" and current["state"] not in {"finishing", "final_changes"}:
        _fail("video_chain_sample_not_approved", "小样还没通过，等用户在页面上通过小样")
    document = copy.deepcopy(master.payload_json)
    if not document.get("music"):
        _fail("video_chain_music_undecided", "配乐还没定：先选一首放进主稿（set_shot_materials 的 music），或请用户在「配音与音乐」里点「不用配乐」，再开剪")
    shots = {shot["id"] for shot in document["shots"]}
    if set(ae_shot_ids) - shots or set(alpha_shot_ids) - set(ae_shot_ids):
        _fail("video_chain_shot_unknown", "AE 镜头必须是导演稿里的镜头", 422)
    post = _postproduction(document, dict.fromkeys(ae_shot_ids, "ae"))
    for comp in post["ae_compositions"]:
        comp["alpha_required"] = comp["shot_id"] in alpha_shot_ids
    if phase == "final":
        post["phase"] = "final"
        record = _unit_record(db, unit_id)
        sample = next((cut for task in reversed(record["tasks"]) if task["phase"] == "rough_cut"
                       for cut in [_accepted_cut(db, task["execution_id"])] if cut is not None), None)
        if sample is not None:
            post.update(parent_output_id=sample.id, parent_output_hash=sample.content_hash, parent_material_revision_id=sample.material_revision_id)
    if document.get("postproduction") != post:
        document["postproduction"] = post
        _save(db, user, project_id, unit_id, document, {"video_chain": "edit_prep", "phase": phase, "notes": (notes or "")[:2000]})
    master = _latest(db, unit_id)
    record = _unit_record(db, unit_id)
    # After the user sends a 小样 / 成片 back, an unchanged master would hand back that same task; the latest
    # send-back of this phase makes the key new, and stays the same on retries so a retry reuses the new task.
    stage = "sample" if phase == "rough_cut" else "final"
    sent_back = next((item["target_id"] for item in reversed(record["decisions"]) if item["stage"] == stage and item["decision"] == "changes"), None)
    key = f"chain-{master.id}-{phase}" + (f"-after-{sent_back}" if sent_back else "")
    clips = persona_clips(db, user, project_id, unit_id, master.payload_json) if phase == "final" else []
    result = open_task(db, project_id, unit_id, {"source_master_revision_id": master.id, "idempotency_key": key, "persona_clips": clips}, user)
    execution_id = result["execution"]["id"]
    if not record["tasks"] or record["tasks"][-1]["execution_id"] != execution_id:
        record["tasks"].append({"phase": phase, "execution_id": execution_id, "draft_master_id": current["draft_master_id"],
                                "master_id": master.id, "at": datetime.now(UTC).isoformat()})
        _put(db, unit_id, record)
    db.commit()
    archive = project_folders.archive_master(db, project_id, master.payload_json) if phase == "rough_cut" else None
    work = project_folders.work_dir(db, project_id, unit_id, execution_id)
    export = project_folders.export_dir(db, project_id, phase)
    cover = project_folders.export_dir(db, project_id, "cover")
    cover.mkdir(parents=True, exist_ok=True)
    db.commit()
    package = db.get(CreativeExecutionPackage, db.get(CreativeExecution, execution_id).package_id)
    from .web_video_handoff import separate_covers

    separate = bool(package and separate_covers(package.package_json))
    from .web_video_handoff import cover_roles

    four_three = bool(package and "cover_43" in cover_roles(package.package_json))
    return {"execution_id": execution_id, "master_id": master.id, "phase": phase,
            "cover_template": ((package.package_json if package else {}).get("director") or {}).get("cover_template"),
            **({"persona_clips": ((package.package_json if package else {}).get("director") or {}).get("persona_clips") or [],
                "persona_note": _persona_note(((package.package_json if package else {}).get("director") or {}).get("persona_clips") or [])} if phase == "final" else {}),
            "archive": {"moved": len(archive["moved"]), "pending": archive["pending"]} if archive else None,
            "work_dir": str(work), "export_dir": str(export), "cover_dir": str(cover),
            "files": f"素材用 materialize_inputs 给的原始路径（只读）；{'小样' if phase == 'rough_cut' else '成片'}导出到 {export}/，"
                     + ("横版封面：横封面设计盖在成片开头 0–0.5 秒随成片渲染，横封面图 role cover 1920×1080 从渲染好的成片开头 0.5 秒内截一帧；"
                        "竖封面 role cover_vertical 1080×1440（3:4）用同一套设计单独做、不放进成片；jpg / png 按 sRGB 存，"
                        + ("再交抖音横封面 role cover_43 1440×1080：把横封面图居中裁出（左右各裁 240 像素），所以横封面的大标题和卖点放在中间 1440 宽里；" if four_three else "")
                        + f"封面都导出到 {cover}/，都在剪辑清单之前交，清单 output_hashes 都列；"
                        if separate else f"可选的封面图（role cover，jpg / png，从渲染好的成片开头 0.5 秒内截一帧，不另外合成）导出到 {cover}/；")
                     + f"其他交付文件和临时渲染放 {work}/；submit_output 传文件的绝对路径 path。"}


PERSONA_SLOTS = (("intro", "intro_clip", "进门"), ("outro", "outro_clip", "收尾"))


def persona_clips(db: Session, user: User, project_id: int, unit_id: int, document: dict) -> list[dict]:
    """The work's persona clips in the work's aspect, attached to the project so the 成片 task may hand them to the model."""
    from .content_identity import current_revision

    unit = db.get(ContentUnit, unit_id)
    revision = current_revision(db, "persona", unit.persona_id) if unit and unit.persona_id else None
    profile = (revision.profile_json or {}) if revision else {}
    aspect = ":".join(str(value) for value in document.get("aspect_ratio") or [9, 16])
    clips = []
    for slot, key, label in PERSONA_SLOTS:
        clip = db.get(MaterialRevision, ((profile.get(key) or {}).get(aspect)) or 0)
        if clip is None:
            continue
        if db.scalar(select(ProjectMaterialReference.id).where(ProjectMaterialReference.project_id == project_id,
                     ProjectMaterialReference.material_revision_id == clip.id, ProjectMaterialReference.status == "active").limit(1)) is None:
            db.add(ProjectMaterialReference(project_id=project_id, material_revision_id=clip.id, origin="system_reference", status="active",
                                            attached_by=user.email, note=f"角色{label}片段"))
            db.flush()
        clips.append({"slot": slot, "material_revision_id": clip.id, "content_hash": clip.content_hash, "duration_ms": clip.duration_ms,
                      "title": clip.material.title})
    return clips


def _persona_note(clips: list[dict]) -> str:
    if not clips:
        return "本作品没有角色收尾"
    names = dict((slot, label) for slot, _key, label in PERSONA_SLOTS)
    return "；".join(f"加角色{names[clip['slot']]} {clip['duration_ms'] / 1000:.1f} 秒（{clip['title']}，素材 {clip['material_revision_id']}）" for clip in clips)


def _accepted_cut(db: Session, execution_id: int) -> CreativeExecutionOutput | None:
    output = db.scalar(select(CreativeExecutionOutput).where(CreativeExecutionOutput.execution_id == execution_id,
                                                             CreativeExecutionOutput.role_id == "rough_cut",
                                                             CreativeExecutionOutput.state == "accepted")
                       .order_by(CreativeExecutionOutput.attempt_no.desc()).limit(1))
    # None when the 小样 was approved without accepting its files (the master moved on after it).
    return output if output is not None and output.material_revision_id is not None else None


def decisions(db: Session, user: User, project_id: int, unit_id: int) -> dict:
    from .content_masters import owned_unit

    owned_unit(db, project_id, unit_id, user)
    record = _unit_record(db, unit_id)
    return {**state(db, user, project_id, unit_id), "decisions": record["decisions"][-10:], "tasks": record["tasks"][-5:]}

