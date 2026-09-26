"""End-to-end API behaviour with a fake model: explicit clauses, missing information, conflicts, caching."""

from tests.conftest import upload
from tests.fake_model import QUOTE_60, QUOTE_FAKE, explicit_answer, notice_findings


def test_upload_processes_document_and_exposes_pages(client, alice, ready_document):
    assert ready_document["processing_status"] == "READY"
    assert ready_document["page_count"] >= 3
    assert ready_document["document_type"] == "EMPLOYMENT"
    pages = client.get(f"/api/documents/{ready_document['id']}/pages", headers=alice).json()
    assert pages["page_count"] == ready_document["page_count"]
    assert pages["pages"][0]["blocks"][0]["block_id"] == "p1-b0"


def test_identical_upload_reuses_processed_document(client, alice, demo_pdf, ready_document):
    response = upload(client, alice, demo_pdf, filename="copy.pdf")
    assert response.status_code == 201
    assert response.json()["id"] == ready_document["id"]


def test_notice_exit_analysis_returns_verified_evidence_and_inconsistency(client, alice, ready_document, fake_model):
    response = client.post(f"/api/documents/{ready_document['id']}/analyze", headers=alice, json={"operation": "NOTICE_EXIT"})
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["operation"] == "NOTICE_EXIT"
    assert result["status"] == "POTENTIAL_INCONSISTENCY"

    notice = next(f for f in result["findings"] if f["label"] == "Notice Period")
    assert notice["status"] == "EXPLICITLY_STATED" and notice["value"] == "60 days"
    evidence = notice["evidence"][0]
    assert evidence["verified"] is True and evidence["id"]
    assert evidence["section"] == "8.2" and evidence["start_offset"] is not None

    severance = next(f for f in result["findings"] if f["label"] == "Severance")
    assert severance["status"] == "NOT_FOUND" and severance["evidence"] == []

    assert len(result["inconsistencies"]) == 1
    values = {v["value"]: v["evidence"] for v in result["inconsistencies"][0]["values"]}
    assert values["30 days"]["section"] == "4.1" and values["60 days"]["section"] == "8.2"
    assert "clarifying" in result["inconsistencies"][0]["description"]
    assert result["related_questions"] and result["professional_questions"]

    # Evidence is resolvable through the evidence endpoint for viewer navigation.
    fetched = client.get(f"/api/documents/{ready_document['id']}/evidence/{evidence['id']}", headers=alice).json()
    assert fetched["page_number"] == evidence["page"] and fetched["text"] == evidence["text"]


def test_analysis_results_are_cached_per_operation(client, alice, ready_document, fake_model):
    document_id = ready_document["id"]
    first = client.post(f"/api/documents/{document_id}/analyze", headers=alice, json={"operation": "NOTICE_EXIT"}).json()
    calls_after_first = fake_model.calls
    second = client.post(f"/api/documents/{document_id}/analyze", headers=alice, json={"operation": "NOTICE_EXIT"}).json()
    assert fake_model.calls == calls_after_first
    assert second["cached"] is True and second["id"] == first["id"]
    listed = client.get(f"/api/documents/{document_id}/analyses", headers=alice).json()
    assert [r["operation"] for r in listed] == ["NOTICE_EXIT"]


def test_fabricated_evidence_is_dropped_and_status_downgraded(client, alice, ready_document, fake_model):
    fake_model.queue(notice_findings(include_conflict=False, fabricated=True), notice_findings(include_conflict=False, fabricated=True))
    result = client.post(f"/api/documents/{ready_document['id']}/analyze", headers=alice, json={"operation": "NOTICE_EXIT"}).json()
    notice = next(f for f in result["findings"] if f["label"] == "Notice Period")
    assert notice["evidence"] == []
    assert notice["status"] == "PARTIALLY_DETERMINED"
    assert notice["verification_note"]
    assert result["verification_notes"]
    assert fake_model.calls >= 2  # a repair retry was attempted


def test_repair_retry_recovers_verified_evidence(client, alice, ready_document, fake_model):
    fake_model.queue(notice_findings(include_conflict=False, fabricated=True), notice_findings(include_conflict=False))
    result = client.post(f"/api/documents/{ready_document['id']}/analyze", headers=alice, json={"operation": "NOTICE_EXIT"}).json()
    notice = next(f for f in result["findings"] if f["label"] == "Notice Period")
    assert notice["status"] == "EXPLICITLY_STATED" and notice["evidence"][0]["verified"]
    assert "could NOT be located" in fake_model.prompts[-1]


def test_inconsistency_requires_both_sides_verified(client, alice, ready_document, fake_model):
    output = notice_findings()
    output.inconsistencies[0].values[0].evidence = QUOTE_FAKE
    fake_model.queue(output, output)
    result = client.post(f"/api/documents/{ready_document['id']}/analyze", headers=alice, json={"operation": "NOTICE_EXIT"}).json()
    assert result["inconsistencies"] == []
    assert result["status"] == "EXPLICITLY_STATED"


def test_concerns_operation_returns_review_items(client, alice, ready_document):
    result = client.post(f"/api/documents/{ready_document['id']}/analyze", headers=alice, json={"operation": "CONCERNS"}).json()
    kinds = {c["kind"] for c in result["concerns"]}
    assert {"POTENTIAL_INCONSISTENCY", "POTENTIAL_CONCERN"} <= kinds
    assert all(e["verified"] for c in result["concerns"] for e in c["evidence"])


def test_question_without_supporting_clause_is_not_determined(client, alice, ready_document):
    response = client.post(
        f"/api/documents/{ready_document['id']}/questions",
        headers=alice,
        json={"question": "What happens to my stock options if I resign?"},
    )
    assert response.status_code == 200, response.text
    answer = response.json()
    assert answer["status"] == "NOT_FOUND"
    assert answer["title"] == "Cannot be determined from this document"
    assert answer["answer"] is None and answer["evidence"] == []
    assert "stock-option" in answer["what_i_found"]
    assert answer["professional_questions"]
    conversation = client.get(f"/api/documents/{ready_document['id']}/conversations/{answer['conversation_id']}", headers=alice).json()
    assert [m["role"] for m in conversation["messages"]] == ["user", "assistant"]


def test_explicit_question_returns_verified_evidence(client, alice, ready_document, fake_model):
    fake_model.queue(explicit_answer())
    answer = client.post(f"/api/documents/{ready_document['id']}/questions", headers=alice, json={"question": "What is the notice period?"}).json()
    assert answer["status"] == "EXPLICITLY_STATED" and answer["answer"] == "60 days"
    assert answer["evidence"][0]["verified"] and answer["evidence"][0]["text"] == QUOTE_60.text


def test_invalid_operation_rejected(client, alice, ready_document):
    response = client.post(f"/api/documents/{ready_document['id']}/analyze", headers=alice, json={"operation": "DROP TABLE"})
    assert response.status_code == 422
    assert client.post(f"/api/documents/{ready_document['id']}/analyze", headers=alice, json={"operation": "DOCUMENT_QA"}).status_code == 422


def test_lawyer_questions_are_grounded(client, alice, ready_document):
    response = client.post(f"/api/documents/{ready_document['id']}/lawyer-questions", headers=alice, json={})
    assert response.status_code == 200, response.text
    questions = response.json()["questions"]
    assert questions[0]["text"] == "Which notice period applies?"
    assert len(questions[0]["evidence"]) == 2 and all(e["verified"] for e in questions[0]["evidence"])


def test_lawyer_questions_are_built_from_the_document_when_gemini_is_down(client, alice, ready_document):
    from app.api.deps import ServiceContainer
    from app.services.gemini_service import ModelUnavailableError, StructuredModel

    class Down(StructuredModel):
        def generate(self, prompt, schema, *, conversational=False):
            raise ModelUnavailableError("capacity", code=503)

    services = client.app.state.services
    client.app.state.services = ServiceContainer(storage=services.storage, processing=services.processing, model=Down())
    response = client.post(f"/api/documents/{ready_document['id']}/lawyer-questions", headers=alice, json={"force": True})
    assert response.status_code == 200, response.text
    questions = response.json()["questions"]
    assert len(questions) >= 3
    assert any("notice" in item["text"].lower() for item in questions)
    assert any(item["evidence"] and all(quote["verified"] for quote in item["evidence"]) for item in questions)


def test_comparison_between_two_owned_documents(client, alice, bob, demo_pdf, demo_txt, ready_document):
    second = upload(client, alice, demo_txt, filename="revised.txt", mime="text/plain").json()
    response = client.post("/api/comparisons", headers=alice, json={"original_document_id": ready_document["id"], "updated_document_id": second["id"]})
    assert response.status_code == 201, response.text
    comparison = response.json()
    assert comparison["rows"][0]["change"] == "CHANGED"
    assert comparison["rows"][0]["original_evidence"][0]["verified"]
    assert client.get(f"/api/comparisons/{comparison['id']}", headers=alice).status_code == 200
    assert client.get(f"/api/comparisons/{comparison['id']}", headers=bob).status_code == 404
    denied = client.post("/api/comparisons", headers=bob, json={"original_document_id": ready_document["id"], "updated_document_id": second["id"]})
    assert denied.status_code == 404


def test_rate_limit_applies_to_expensive_endpoints(client, alice, ready_document, monkeypatch):
    from app.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "rate_limit_per_minute", 2)
    url = f"/api/documents/{ready_document['id']}/questions"
    statuses = [client.post(url, headers=alice, json={"question": "What is the notice period?"}).status_code for _ in range(3)]
    assert statuses[:2] == [200, 200] and statuses[2] == 429


def test_delete_removes_document(client, alice, ready_document):
    assert client.delete(f"/api/documents/{ready_document['id']}", headers=alice).status_code == 204
    assert client.get(f"/api/documents/{ready_document['id']}", headers=alice).status_code == 404
