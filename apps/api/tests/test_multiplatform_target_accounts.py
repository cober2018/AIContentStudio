from test_series_targets import (
    HEADERS,
    _approval_payload,
    _authorize,
    _platform_account,
    _ready_source,
)

from app.models import ChannelVariantRevision, ContentUnit
from app.seed import seed_v1_channel_profiles


def _setup(client, db):
    seed_v1_channel_profiles(db)
    db.commit()
    persona = client.post('/api/v1/content-personas', json={'name': '目标作者'}, headers=HEADERS).json()
    account = _platform_account(client, db, persona['id'], 'X A', 'x', 'target-a')
    project, unit, master = _ready_source(client, db, persona_id=persona['id'])
    base = {'source_master_revision_id': master['id'], 'expected_source_payload_hash': master['payload_hash'],
            'expected_source_context_hash': master['context_hash'], 'channel_id': 'x', 'content_form': 'single'}
    return project, unit, master, account, base


def test_target_account_preview_freezes_into_candidate(client, db_session):
    project, unit, _master, account, base = _setup(client, db_session)
    path = f'/api/v1/content-projects/{project}/units/{unit}/channel-variants'
    preview = client.post(path + '/adapt-preview', json={**base, 'target_account_id': account['id']}, headers=HEADERS)
    assert preview.status_code == 200, preview.text
    context = preview.json()['target_account']
    assert context == {'content_account_id': account['id'], 'platform_channel': 'x',
                       'platform_account_id': account['platform_account_id'], 'series_binding': None}
    key = f"x.single.account-{account['id']}"
    saved = client.post(path, json={**base, 'target_account_id': account['id'],
        'expected_target_context_hash': preview.json()['target_context_hash'], 'variant_key': key,
        'expected_revision': 0, 'idempotency_key': key, 'payload': preview.json()['payload']}, headers=HEADERS)
    assert saved.status_code == 201, saved.text
    assert saved.json()['target_account'] == context
    assert client.post(f"{path}/{saved.json()['id']}/checks", headers=HEADERS).json()['ready']
    frozen = client.post(f'/api/v1/content-projects/{project}/units/{unit}/candidates/freeze', json={
        'channel_variant_revision_id': saved.json()['id'], 'expected_payload_hash': saved.json()['payload_hash']}, headers=HEADERS)
    assert frozen.status_code == 201, frozen.text
    candidate = frozen.json()
    assert candidate['manifest']['target']['account'] == context
    approved = client.post(f"/api/v1/content-projects/{project}/units/{unit}/candidates/{candidate['id']}/approve",
        json=_approval_payload(candidate), headers=HEADERS)
    assert approved.status_code == 200, approved.text
    assert _authorize(client, project, unit, candidate, content_account_id=account['id']).status_code == 201
    assert db_session.get(ContentUnit, unit).account_id is None


def test_target_metadata_cannot_be_supplied_in_edit_summary(client, db_session):
    project, unit, _master, a, base = _setup(client, db_session)
    path = f'/api/v1/content-projects/{project}/units/{unit}/channel-variants'
    response = client.post(path, json={**base, 'variant_key': 'x.single.fake', 'expected_revision': 0,
        'idempotency_key': 'fake', 'payload': {'text': '这是观点'},
        'edit_summary': {'target_account': {'content_account_id': a['id']}}}, headers=HEADERS)
    assert response.status_code == 422, response.text
    assert not db_session.query(ChannelVariantRevision).count()


def test_rejected_variant_input_does_not_echo_value(client, db_session):
    project, unit, _master, _a, base = _setup(client, db_session)
    response = client.post(f'/api/v1/content-projects/{project}/units/{unit}/channel-variants/adapt-preview',
        json={**base, 'target_account_id': 'private-rejected-value'}, headers=HEADERS)
    assert response.status_code == 422 and 'private-rejected-value' not in response.text


def test_stage_explicit_account_clear_does_not_inherit_saved_account():
    from app.services.stage_domain_integrations import _variant_request

    request = _variant_request({'master': {'id': 1, 'payload_hash': 'a'*64, 'context_hash': 'b'*64}},
        {'channel_id': 'x', 'content_form': 'single', 'target_account_id': 0})
    assert request['target_account_id'] is None


def test_unknown_suggestion_is_not_dispatched_again(client, db_session, monkeypatch):
    from app.services import channel_variants

    project, unit, _master, _a, base = _setup(client, db_session)
    calls = []

    class Provider:
        async def generate_json(self, request):
            calls.append(request)
            raise TimeoutError('response unknown')

    monkeypatch.setattr(channel_variants, 'get_provider', lambda purpose: Provider())
    path = f'/api/v1/content-projects/{project}/units/{unit}/channel-variants/model-suggestions'
    first = client.post(path, json=base, headers=HEADERS)
    assert first.status_code == 503 and first.json()['detail']['code'] == 'variant_model_unknown'
    import pytest

    from app.models import User
    from app.services.stage_domain_integrations import StageDomainError, _model_variant

    user = db_session.query(User).filter_by(email=HEADERS['X-Studio-User']).one()
    preview = channel_variants.adapt_preview(db_session, project_id=project, unit_id=unit, user=user, payload=base)
    with pytest.raises(StageDomainError, match='variant_model_unknown_unresolved'):
        _model_variant(db_session, {'context': {'project_id': project, 'unit_id': unit}}, preview, user)
    second = client.post(path, json=base, headers=HEADERS)
    assert second.status_code == 409 and second.json()['detail']['code'] == 'variant_model_unknown_unresolved'
    assert len(calls) == 1
