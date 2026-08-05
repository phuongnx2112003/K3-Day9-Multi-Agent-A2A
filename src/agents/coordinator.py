"""
Coordinator Agent. Owned by Member 3.
Orchestrates parallel investigation, facts merging, policy call, and verification gate.
"""
import asyncio
import time
from typing import Optional, Dict, Any
from src.contracts.messages import (
    InvestigationRequest,
    PolicyRequest,
    VerificationRequest,
    ResolutionDraft
)
from src.agents.order_seller import OrderSellerAgent
from src.agents.payment import PaymentAgent
from src.agents.delivery import DeliveryAgent
from src.agents.policy import PolicyAgent
from src.agents.verifier import VerifierAgent
from src.tracing import log_event


class CoordinatorAgent:
    def __init__(
        self,
        order_seller_agent: OrderSellerAgent,
        payment_agent: PaymentAgent,
        delivery_agent: DeliveryAgent,
        policy_agent: PolicyAgent,
        verifier_agent: VerifierAgent
    ):
        self.order_seller = order_seller_agent
        self.payment = payment_agent
        self.delivery = delivery_agent
        self.policy = policy_agent
        self.verifier = verifier_agent

    async def process_case(self, case_input: Dict[str, Any], run_id: str, trace_id: str) -> Optional[ResolutionDraft]:
        case_id = case_input["case_id"]
        order_id = case_input["customer_request"]["claimed_order_id"]
        opened_at = case_input["opened_at"]
        message = case_input["customer_request"]["message"]

        log_event(run_id, trace_id, case_id, "case_started", "coordinator", input_refs=[case_id])

        inv_req = InvestigationRequest(
            case_id=case_id,
            order_id=order_id,
            opened_at=opened_at,
            customer_request_message=message
        )

        # 1. Parallel Investigation Fan-out with per-agent logging
        t0 = time.time()
        order_seller_facts, payment_facts, delivery_facts = await asyncio.gather(
            self.order_seller.process(inv_req),
            self.payment.process(inv_req),
            self.delivery.process(inv_req)
        )
        duration_ms = int((time.time() - t0) * 1000)

        log_event(run_id, trace_id, case_id, "agent_investigated", "order_seller_agent", duration_ms=duration_ms, output_summary={"order_status": order_seller_facts.order_status, "item_total": order_seller_facts.item_total_brl})
        log_event(run_id, trace_id, case_id, "agent_investigated", "payment_agent", duration_ms=duration_ms, output_summary={"payment_total": payment_facts.payment_total_brl, "payment_count": payment_facts.payment_count})
        log_event(run_id, trace_id, case_id, "agent_investigated", "delivery_agent", duration_ms=duration_ms, output_summary={"delivered_late": delivery_facts.delivered_late})
        log_event(run_id, trace_id, case_id, "facts_merged", "coordinator")

        # 2. Policy Call
        pol_req = PolicyRequest(
            case_id=case_id,
            order_id=order_id,
            order_seller_facts=order_seller_facts,
            payment_facts=payment_facts,
            delivery_facts=delivery_facts
        )
        t_pol = time.time()
        draft = await self.policy.process(pol_req)
        pol_duration_ms = int((time.time() - t_pol) * 1000)

        log_event(
            run_id,
            trace_id,
            case_id,
            "agent_decided",
            "policy_agent",
            duration_ms=pol_duration_ms,
            output_summary={
                "primary_issue": draft.primary_issue,
                "refund": draft.recommended_refund_brl,
                "decision_source": self.policy.last_decision_source,
                "llm_error": self.policy.last_llm_error,
            },
        )

        # 3. Verification Call
        ver_req = VerificationRequest(
            case_id=case_id,
            draft=draft,
            order_seller_facts=order_seller_facts,
            payment_facts=payment_facts,
            delivery_facts=delivery_facts
        )
        t_ver = time.time()
        ver_res = await self.verifier.verify(ver_req)
        ver_duration_ms = int((time.time() - t_ver) * 1000)

        log_event(run_id, trace_id, case_id, "agent_verified", "verifier_agent", duration_ms=ver_duration_ms, status="success" if ver_res.valid else "error", output_summary={"valid": ver_res.valid, "errors": ver_res.errors, "warnings": ver_res.warnings})

        if ver_res.valid:
            log_event(run_id, trace_id, case_id, "case_completed", "coordinator", status="success")
            return draft
        else:
            log_event(run_id, trace_id, case_id, "case_failed", "coordinator", status="error", error="; ".join(ver_res.errors))
            return None
