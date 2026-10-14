import hashlib
import io
import json
import zipfile

from test_series_targets import HEADERS, _authorize, _ready_source, _ready_variant_candidate

from app.models import ContentAsset
from app.services.channel_variants import _text_source_evidence_refs


def test_optional_source_disclosure_cannot_export_private_metadata(db_session):
    from app.models import FactPack, FactPackItem
    from app.services.production_packages import public_export_metadata

    pack = FactPack(name='公开内容与私有出处分开', status='frozen', checksum='a'*64); db_session.add(pack); db_session.flush()
    item = FactPackItem(fact_pack_id=pack.id, evidence_kind='author_opinion', snapshot_checksum='b'*64,
        public_use_allowed=True, snapshot_json={'statement': '可以引用的内容', 'source': {
            'title': 'private-source-title', 'author': 'private-author', 'public_disclosure_allowed': False}})
    db_session.add(item); db_session.commit()
    metadata = public_export_metadata(db_session, [], [{'fact_pack_item_id': item.id, 'snapshot_checksum': item.snapshot_checksum}])
    assert metadata['sources'] == [{'fact_pack_item_id': item.id, 'snapshot_checksum': item.snapshot_checksum}]


def test_channel_rules_read_every_modern_text_location():
    from app.services.channel_variants import _variant_visible_text

    payload = {'title': '标题', 'summary': '概要', 'tags': ['稳赚不赔标签'], 'question': {'text': '问题', 'context': '背景'},
        'blocks': [{'id': 'list', 'kind': 'list', 'items': [{'id': 'item', 'text': '稳赚不赔'}]},
                   {'id': 'code', 'kind': 'code', 'text': 'run_code()'}]}
    visible = _variant_visible_text(payload)
    assert all(value in visible for value in ('概要', '问题', '背景', '稳赚不赔', '稳赚不赔标签', '```', 'run_code()'))


def test_bilibili_frozen_render_keeps_description_and_tags():
    from app.services.channel_adapters import GraphicImageNoteAdapter

    refs = [{'slot_key': 'card', 'material_revision_id': 1, 'content_hash_snapshot': 'a'*64}]
    projection = GraphicImageNoteAdapter('bilibili').render({'title': '标题', 'description': '说明', 'tags': ['主题'],
        'cards': [{'id': 'card', 'order': 0, 'image_ref_key': 'card', 'caption': '图片说明'}]}, asset_refs=refs)
    assert projection['description'] == '说明' and projection['tags'] == ['主题']


def test_explicit_published_adapter_mismatch_fails_closed(client, db_session):
    import pytest

    from app.models import ChannelTemplateVersion
    from app.seed import seed_v1_channel_profiles
    from app.services.channel_adapters import AdapterUnavailable, capability_for

    seed_v1_channel_profiles(db_session); db_session.commit()
    profile = db_session.query(ChannelTemplateVersion).filter_by(channel='toutiao', status='published').one()
    raw = json.loads(json.dumps(profile.profile_json)); raw['content_forms']['article']['payload_schema'] = 'x.single.v1'
    profile.profile_json = raw; db_session.commit()
    with pytest.raises(AdapterUnavailable, match='profile_contract_mismatch'):
        capability_for(db_session, 'text.master.v2', 'toutiao', 'article')


def test_weibo_cover_is_exact_post_image_and_keeps_live_rights(client, db_session, tmp_path):
    from app.models import Material, MaterialRevision, ProjectMaterialReference

    persona = client.post('/api/v1/content-personas', json={'name': '微博配图'}, headers=HEADERS).json()
    project, _unit, _master = _ready_source(client, db_session, persona_id=persona['id'])
    data = b'\x89PNG\r\n\x1a\ncontract fixture'
    file = tmp_path / 'cover.png'; file.write_bytes(data)
    material = Material(title='封面', kind='image', status='active'); db_session.add(material); db_session.flush()
    revision = MaterialRevision(material_id=material.id, status='active', file_path=str(file),
        content_hash=hashlib.sha256(data).hexdigest(), mime_type='image/png', public_use_allowed=True, rights_status='cleared')
    db_session.add(revision); db_session.flush()
    db_session.add(ProjectMaterialReference(project_id=project, material_revision_id=revision.id, origin='system_library', status='active'))
    db_session.commit()
    from app.services.channel_variants import _validate_text_target_assets

    refs = [{'material_revision_id': revision.id, 'content_hash_snapshot': revision.content_hash,
        'slot_key': 'cover', 'sort_order': 0, 'role': 'post_image', 'placement': {'usage': 'post', 'image_id': 'cover'}}]
    payload = {'text': '这是观点', 'images': [{'id': 'cover', 'order': 0, 'image_ref_key': 'cover'}]}
    assert _validate_text_target_assets(db_session, project, refs, payload, 'weibo.single.v1') == [revision]
    revision.public_use_allowed = False; db_session.commit()
    import pytest
    from fastapi import HTTPException
    with pytest.raises(HTTPException):
        _validate_text_target_assets(db_session, project, refs, payload, 'weibo.single.v1')


def test_long_post_evidence_offsets_match_joined_paragraphs(db_session):
    from types import SimpleNamespace

    master = SimpleNamespace(id=100, payload_json={'title': '标题', 'document': {
        'schema': 'studio.text.document.v1', 'blocks': [
            {'id': 'a', 'type': 'paragraph', 'content': [{'text': '第一段', 'marks': []}]},
            {'id': 'b', 'type': 'paragraph', 'content': [{'text': '第二段', 'marks': []}]}],
        'citations': [{'id': 'c', 'block_id': 'b', 'start': 0, 'end': 3, 'fact_pack_item_id': 7,
                       'selected_text_hash': hashlib.sha256('第二段'.encode()).hexdigest()}]}})
    # Exact source refs are the same shape as the persisted source; only the query is supplied here.
    ref = SimpleNamespace(fact_pack_item_id=7, snapshot_checksum='d'*64, role='claim',
        content_locator_json={'citation_id': 'c', 'block_id': 'b', 'start': 0, 'end': 3,
                              'selected_text_hash': hashlib.sha256('第二段'.encode()).hexdigest()})
    class QueryResult:
        def all(self): return [ref]
    class Session:
        def scalars(self, query): return QueryResult()
    result = _text_source_evidence_refs(Session(), master, 'x.long_post.v1')
    assert result[0]['content_locator_json'] == {'location_id': 'single', 'start': 5, 'end': 8}


def test_public_zip_has_own_hash_and_no_internal_candidate_context(client, db_session):
    persona = client.post('/api/v1/content-personas', json={'name': '安全交付'}, headers=HEADERS).json()
    project, unit, master = _ready_source(client, db_session, persona_id=persona['id'])
    candidate = _ready_variant_candidate(client, project, unit, master)
    authorized = _authorize(client, project, unit, candidate)
    assert authorized.status_code == 201, authorized.text
    response = client.get(f"/api/v1/delivery-targets/{authorized.json()['id']}/package.zip", headers=HEADERS)
    assert response.status_code == 200, response.text
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        assert {'manifest.json', 'content.md', 'sources.json', 'declarations.json', 'publish-guide.md', 'post.json'} <= set(archive.namelist())
        exported = json.loads(archive.read('manifest.json'))
        assert exported['export_schema'] == 'studio.channel-export.v1'
        assert exported['candidate'] == {'id': candidate['id'], 'hash': candidate['candidate_hash']}
        assert not {'identity', 'brief', 'evidence', 'production', 'source_master'} & set(exported)
        content_hash = exported.pop('export_hash')
        assert content_hash == hashlib.sha256(json.dumps(exported, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        for member in exported['files']:
            assert member['sha256'] == hashlib.sha256(archive.read(member['name'])).hexdigest()
    assert db_session.get(ContentAsset, candidate['id']).candidate_hash == candidate['candidate_hash']


def test_legacy_master_cover_maps_without_changing_source_refs():
    from copy import deepcopy
    from types import SimpleNamespace

    from app.services.channel_variants import _text_source_cover_refs

    master = SimpleNamespace(id=100, payload_json={'document': {'blocks': [
        {'id': 'image', 'type': 'image', 'material_revision_id': 2}]}})
    refs = [SimpleNamespace(material_revision_id=1, content_hash_snapshot='a'*64,
                            role='cover', slot_key=None, sort_order=0, placement_json={}),
            SimpleNamespace(material_revision_id=2, content_hash_snapshot='b'*64,
                            role='inline', slot_key=None, sort_order=1, placement_json={'block_id': 'image'})]
    original = deepcopy([ref.__dict__ for ref in refs])

    class QueryResult:
        def all(self): return refs

    class Session:
        def scalars(self, query): return QueryResult()

    mapped = _text_source_cover_refs(Session(), master)
    assert mapped == [
        {'material_revision_id': 1, 'content_hash_snapshot': 'a'*64, 'role': 'cover',
         'slot_key': 'cover', 'sort_order': 0, 'placement': {'usage': 'cover'}},
        {'material_revision_id': 2, 'content_hash_snapshot': 'b'*64, 'role': 'inline_image',
         'slot_key': 'image', 'sort_order': 1, 'placement': {'usage': 'inline', 'block_id': 'image'}}]
    assert [ref.__dict__ for ref in refs] == original
    refs[0].placement_json = {'usage': 'unrelated'}
    import pytest
    from fastapi import HTTPException
    with pytest.raises(HTTPException):
        _text_source_cover_refs(Session(), master)
