"""
End-to-end pipeline integration tests.
Tests full flow from input JSON -> DAL -> Agents -> Policy -> Verifier -> Output Schema.
"""
import json
import pytest
import uuid
from pathlib import Path
from src.settings import INPUT_DIR
from src.data_access import DataAccessLayer
from src.agents.order_seller import OrderSellerAgent
from src.agents.payment import PaymentAgent
from src.agents.delivery import DeliveryAgent
from src.agents.policy import PolicyAgent
from src.agents.verifier import VerifierAgent
from src.agents.coordinator import CoordinatorAgent


@pytest.fixture(autouse=True)
def isolate_trace(monkeypatch):
    monkeypatch.setattr("src.agents.coordinator.log_event", lambda *args, **kwargs: None)


@pytest.fixture(scope="module")
def dal():
    dal_instance = DataAccessLayer()
    dal_instance.load_data()
    return dal_instance


@pytest.fixture(scope="module")
def coordinator(dal):
    order_seller = OrderSellerAgent(dal)
    payment = PaymentAgent(dal)
    delivery = DeliveryAgent(dal)
    policy = PolicyAgent()
    verifier = VerifierAgent(dal)
    return CoordinatorAgent(order_seller, payment, delivery, policy, verifier)


@pytest.mark.asyncio
async def test_end_to_end_sample_cases(coordinator):
    sample_files = ["EC_001.json", "EC_002.json", "EC_003.json"]
    for filename in sample_files:
        fpath = INPUT_DIR / filename
        assert fpath.exists(), f"Input file {filename} not found"
        
        with open(fpath, "r", encoding="utf-8") as f:
            case_input = json.load(f)

        run_id = str(uuid.uuid4())
        trace_id = str(uuid.uuid4())

        draft = await coordinator.process_case(case_input, run_id, trace_id)
        assert draft is not None, f"Pipeline failed to process {filename}"
        
        case_output = draft.to_case_output()
        assert case_output.case_id == case_input["case_id"]
        assert case_output.assessment.case_status in ("action_required", "no_action")
        assert 0.0 <= case_output.assessment.confidence <= 1.0
        assert isinstance(case_output.financial_resolution.recommended_refund_brl, float)
