"""One parameterized local chain; genuine-media runs are recorded separately from fixtures."""

import hashlib
import io
import json
import os
import sqlite3
import zipfile
from pathlib import Path

import pytest
from test_f6e_freeze_v5 import HEADERS, _approval_payload, _ready_source
from test_f6e_graphic_adaptation import _source as graphic_source
from test_f6e_video_script_adaptation import _source as video_source

from app.models import FactPack, FactPackItem, Material, MaterialRevision, ProjectMaterialReference
from app.services.multiplatform_profiles import DECLARED_TARGETS, apply_profiles, dry_run_profiles


def _real_graphic_source(client, db, tmp_path):
    source_db = sqlite3.connect('file:' + os.environ['AICS_SMOKE_SOURCE_DB'] + '?mode=ro', uri=True)
    source_db.row_factory = sqlite3.Row
    payload = json.loads(source_db.execute('select payload_json from content_master_revision where id=10').fetchone()[0])
    refs = source_db.execute('select * from content_master_asset_ref where master_revision_id=10 order by id').fetchall()
    persona = client.post('/api/v1/content-personas', json={'name': '既有图文隔离验证'}, headers=HEADERS).json()['id']
    project = client.post('/api/v1/content-projects', json={'title': '既有真实图组'}, headers=HEADERS).json()['id']
    unit = client.post(f'/api/v1/content-projects/{project}/units', json={
        'title': '既有真实图组', 'persona_id': persona, 'modality': 'graphic'}, headers=HEADERS).json()['id']
    assert client.post(f'/api/v1/content-projects/{project}/brief/revisions', json={
        'objective': '核对已有真实图组的独立渠道包', 'expected_revision': 0}, headers=HEADERS).status_code == 201
    pack = FactPack(name='真实图组意见边界', status='frozen', checksum='c'*64)
    db.add(pack); db.flush()
    db.add(FactPackItem(fact_pack_id=pack.id, evidence_kind='author_opinion', snapshot_json={'statement': '编辑观点'},
        snapshot_checksum='d'*64, public_use_allowed=True, model_use_allowed=False))
    db.commit()
    assert client.post(f'/api/v1/content-projects/{project}/fact-boundary', json={
        'fact_pack_id': pack.id, 'expected_revision': 0}, headers=HEADERS).status_code == 201
    mapping, saved_refs = {}, []
    for ref in refs:
        original = source_db.execute('select * from material_revision where id=?', (ref['material_revision_id'],)).fetchone()
        if original['id'] not in mapping:
            assert original['public_use_allowed'] and original['rights_status'] == 'cleared'
            data = (Path(os.environ['AICS_SMOKE_SOURCE_MEDIA']) / original['file_path']).read_bytes()
            assert hashlib.sha256(data).hexdigest() == original['content_hash']
            file = tmp_path / Path(original['file_path']).name; file.write_bytes(data)
            material = Material(title='复用真实媒体', kind='image', status='active'); db.add(material); db.flush()
            revision = MaterialRevision(material_id=material.id, status='active', file_path=str(file),
                content_hash=original['content_hash'], mime_type=original['mime_type'], rights_status=original['rights_status'],
                public_use_allowed=bool(original['public_use_allowed']), model_use_allowed=bool(original['model_use_allowed']),
                commercial_use_allowed=bool(original['commercial_use_allowed']), width=original['width'], height=original['height'],
                attribution_text=original['attribution_text'])
            db.add(revision); db.flush(); mapping[original['id']] = revision.id
            db.add(ProjectMaterialReference(project_id=project, material_revision_id=revision.id, origin='system_library', status='active'))
        saved_refs.append({'material_revision_id': mapping[original['id']], 'content_hash': original['content_hash'],
            'role': ref['role'], 'slot_key': ref['slot_key'], 'sort_order': ref['sort_order'], 'placement': json.loads(ref['placement_json'])})
    db.commit(); source_db.close()
    def rewrite(value):
        if isinstance(value, dict):
            return {k: mapping[v] if k == 'material_revision_id' else rewrite(v) for k, v in value.items()}
        return [rewrite(x) for x in value] if isinstance(value, list) else value
    payload = rewrite(payload)
    draft_payload = {k: v for k, v in payload.items() if k != 'render_asset_ref'}
    path = f'/api/v1/content-projects/{project}/units/{unit}/master-revisions'
    draft = client.post(path, json={'idempotency_key': 'real-graphic-draft', 'payload_schema': 'graphic.master.v2',
        'payload': draft_payload, 'asset_refs': saved_refs}, headers=HEADERS)
    assert draft.status_code == 200, draft.text
    ready = client.get(f"{path}/{draft.json()['id']}/readiness", headers=HEADERS).json()
    result = client.post(path, json={'idempotency_key': 'real-graphic', 'expected_revision': 1, 'payload_schema': 'graphic.master.v2',
        'payload': payload, 'asset_refs': saved_refs, 'render_attestation': {
            'confirmed': True, 'render_input_hash': ready['render_input_hash']}}, headers=HEADERS)
    assert result.status_code == 200, result.text
    assert client.post(f"{path}/{result.json()['id']}/checks", headers=HEADERS).status_code == 200
    return project, unit, result.json(), HEADERS


@pytest.mark.parametrize(('channel', 'form'), DECLARED_TARGETS)
def test_seventeen_form_local_chain(client, db_session, tmp_path, monkeypatch, channel, form):
    from app.services import channel_variants
    from app.services.content_harness.publishers.wechat_wewrite import WechatWewritePublisher

    monkeypatch.setattr(channel_variants, 'get_provider', lambda *a: pytest.fail('local chain dispatched a provider'))
    monkeypatch.setattr(WechatWewritePublisher, 'deliver', lambda *a, **kw: pytest.fail('local chain dispatched WeChat'))
    if form == 'image_note':
        if os.environ.get('AICS_SMOKE_SOURCE_DB'):
            project, unit, master, headers = _real_graphic_source(client, db_session, tmp_path)
        else:
            project, unit, master, _image, headers = graphic_source(client, db_session, tmp_path, ready=True)
    elif form == 'spoken_script':
        project, unit, master, headers = video_source(client, db_session, ready=True)
    else:
        project, unit, master = _ready_source(client, db_session, neutral=True)
        headers = HEADERS
    plan = dry_run_profiles(db_session, sorted({x[0] for x in DECLARED_TARGETS}))
    apply_profiles(db_session, plan, expected_plan_hash=plan['plan_hash'])
    path = f'/api/v1/content-projects/{project}/units/{unit}/channel-variants'
    request = {'source_master_revision_id': master['id'], 'expected_source_payload_hash': master['payload_hash'],
        'expected_source_context_hash': master['context_hash'], 'channel_id': channel, 'content_form': form}
    if form == 'answer':
        request['question'] = {'text': '这是哪一类表达？', 'confirmed': True}
    capabilities = client.get(path + '/capabilities', headers=headers).json()
    selected = next(item for item in capabilities['items'] if (item['channel'], item['content_form']) == (channel, form))
    assert selected['capability']['executable'] and selected['form_descriptor']['schema_id']
    preview = client.post(path + '/adapt-preview', json=request, headers=headers)
    assert preview.status_code == 200, preview.text
    proposed = preview.json()
    assets = proposed['asset_refs']
    if channel == 'wechat':
        file = tmp_path / 'cover.png'
        data = Path(os.environ['AICS_SMOKE_COVER']).read_bytes() if os.environ.get('AICS_SMOKE_COVER') else b'\x89PNG\r\n\x1a\ncontract fixture'
        file.write_bytes(data)
        material = Material(title='核对封面', kind='image', status='active'); db_session.add(material); db_session.flush()
        revision = MaterialRevision(material_id=material.id, status='active', file_path=str(file), content_hash=hashlib.sha256(data).hexdigest(),
            mime_type='image/png', public_use_allowed=True, model_use_allowed=False, commercial_use_allowed=False, rights_status='cleared')
        db_session.add(revision); db_session.flush()
        db_session.add(ProjectMaterialReference(project_id=project, material_revision_id=revision.id, origin='system_library', status='active'))
        db_session.commit()
        assets = [{'material_revision_id': revision.id, 'content_hash_snapshot': revision.content_hash,
            'role': 'cover', 'slot_key': 'cover', 'sort_order': 0, 'placement': {'usage': 'cover'}}]
    body = {**{k: v for k, v in request.items() if k != 'question'}, 'variant_key': f'{channel}.{form}.smoke', 'expected_revision': 0,
        'idempotency_key': 'smoke', 'source_kind': 'deterministic_adapt', 'expected_profile_hash': proposed['profile_hash'], 'payload': proposed['payload'],
        'asset_refs': assets, 'evidence_refs': proposed['evidence_refs']}
    saved = client.post(path, json=body, headers=headers)
    assert saved.status_code == 201, saved.text
    variant = saved.json()
    reopened = client.get(f"{path}/{variant['id']}", headers=headers).json()
    assert reopened['payload_hash'] == variant['payload_hash'] and reopened['payload'] == variant['payload']
    checks = client.post(f"{path}/{variant['id']}/checks", headers=headers)
    assert checks.status_code == 200 and checks.json()['ready'], checks.text
    candidates = f'/api/v1/content-projects/{project}/units/{unit}/candidates'
    frozen = client.post(candidates + '/freeze', json={'channel_variant_revision_id': variant['id'],
        'expected_payload_hash': variant['payload_hash']}, headers=headers)
    assert frozen.status_code == 201, frozen.text
    candidate = frozen.json()
    approved = client.post(f"{candidates}/{candidate['id']}/approve", json=_approval_payload(candidate), headers=headers)
    assert approved.status_code == 200, approved.text
    authorized = client.post(f"{candidates}/{candidate['id']}/delivery-authorizations", json={
        'channel': channel, 'content_form': form, 'account_ref': f'manual-{channel}', 'authorization_version': 'smoke-v1',
        'action': 'copy_package'}, headers=headers)
    assert authorized.status_code == 201, authorized.text
    downloaded = client.get(f"/api/v1/delivery-targets/{authorized.json()['id']}/package.zip", headers=headers)
    assert downloaded.status_code == 200, downloaded.text
    with zipfile.ZipFile(io.BytesIO(downloaded.content)) as archive:
        manifest = json.loads(archive.read('manifest.json'))
        assert manifest['candidate']['hash'] == candidate['candidate_hash']
        assert {'sources.json', 'declarations.json', 'publish-guide.md', 'content.md'} <= set(archive.namelist())
        for item in manifest['files']:
            assert hashlib.sha256(archive.read(item['name'])).hexdigest() == item['sha256']
        for ref in manifest['media']:
            revision = db_session.get(MaterialRevision, ref['material_revision_id'])
            assert archive.read(ref['name']) == Path(revision.file_path).read_bytes()
    if os.environ.get('AICS_BATCH_B_UI_DB'):
        destination = Path(os.environ['AICS_BATCH_B_UI_DB']); destination.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(str(destination / f'{channel}-{form}.db')) as copy_db:
            db_session.connection().connection.driver_connection.backup(copy_db)
        (destination / f'{channel}-{form}.json').write_text(json.dumps({'project_id': project, 'unit_id': unit,
            'headers': headers, 'variant_id': variant['id'], 'candidate_id': candidate['id'], 'target_id': authorized.json()['id']}, indent=2))
    if os.environ.get('AICS_BATCH_B_RECEIPTS'):
        output = Path(os.environ['AICS_BATCH_B_RECEIPTS']); output.mkdir(parents=True, exist_ok=True)
        (output / f'{channel}-{form}.zip').write_bytes(downloaded.content)
        (output / f'{channel}-{form}.json').write_text(json.dumps({'channel': channel, 'form': form,
            'payload_hash': variant['payload_hash'], 'candidate_hash': candidate['candidate_hash'],
            'export_hash': manifest['export_hash'], 'zip_hash': hashlib.sha256(downloaded.content).hexdigest(),
            'media': manifest['media'], 'schema': variant['payload_schema'],
            'source_mode': 'existing_genuine_media_controlled_text' if os.environ.get('AICS_SMOKE_SOURCE_DB') else 'contract_fixture',
            'provider_calls': 0, 'remote_calls': 0, 'status': 'LOCAL_CHAIN_PASSED'}, ensure_ascii=False, indent=2))
