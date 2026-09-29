from fastapi.testclient import TestClient
from src.api import app, get_access_scope, get_service
from src.models import AccessScope, Answer

class MockService:
    async def answer_query(self, request, scope):
        return Answer(
            status="grounded",
            text="Mock response",
            citations=(),
            route="direct-retrieve",
            trace_id="t1"
        )

def get_mock_scope():
    return AccessScope(tenant_id="t", principal_id="u", group_ids=frozenset(), source_policy_attributes={}, permission_epoch=1)

app.dependency_overrides[get_service] = MockService
app.dependency_overrides[get_access_scope] = get_mock_scope

client = TestClient(app)
response = client.post("/query", json={"query": "test"})
print(response.status_code)
print(response.text)
