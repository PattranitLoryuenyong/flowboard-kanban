from fastapi.testclient import TestClient
from main import app
client = TestClient(app)
def test_health():
    assert client.get('/health').json() == {'status': 'ok'}
def test_cards_require_login():
    assert client.get('/boards').status_code == 401
def test_create_requires_login():
    assert client.post('/boards', json={'title':'My board'}).status_code == 401
def test_admin_requires_login():
    assert client.get('/admin/users').status_code == 401

import pytest
import httpx
from main import session
from uuid import UUID

@pytest.fixture
def signed_in():
    async def authenticated():
        return ('https://test.invalid', {}, {'id':'00000000-0000-0000-0000-000000000001'})
    app.dependency_overrides[session]=authenticated
    yield
    app.dependency_overrides.clear()

@pytest.mark.parametrize('payload',[{'title':''},{'title':'   '},{'title':'x','status':'invalid'}])
def test_invalid_card_rejected(signed_in,payload):
    assert client.post('/boards/00000000-0000-0000-0000-000000000002/cards',json=payload).status_code==422

def test_invalid_move_rejected(signed_in):
    assert client.patch('/cards/00000000-0000-0000-0000-000000000002',json={'status':'blocked'}).status_code==422

def test_card_lifecycle(signed_in,monkeypatch):
    rows=[]
    original=httpx.AsyncClient
    def handler(request):
        import json
        if request.method=='POST':
            row=json.loads(request.content);row['id']='00000000-0000-0000-0000-000000000003';rows.append(row);return httpx.Response(201,json=[row])
        if request.method=='PATCH':
            rows[0]['status']=json.loads(request.content)['status'];return httpx.Response(200,json=rows)
        if request.method=='DELETE':
            deleted=list(rows);rows.clear();return httpx.Response(200,json=deleted)
        return httpx.Response(200,json=rows)
    monkeypatch.setattr(httpx,'AsyncClient',lambda **kw:original(transport=httpx.MockTransport(handler),**kw))
    board='00000000-0000-0000-0000-000000000002'
    created=client.post(f'/boards/{board}/cards',json={'title':'Ship assignment'})
    assert created.status_code==201
    card=created.json()['id']
    assert client.patch('/cards/'+card,json={'status':'doing'}).json()['status']=='doing'
    assert client.get(f'/boards/{board}/cards').json()[0]['title']=='Ship assignment'
    assert client.delete('/cards/'+card).status_code==204
    assert client.get(f'/boards/{board}/cards').json()==[]
