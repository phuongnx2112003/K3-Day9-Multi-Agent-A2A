"""
Message envelope and inter-agent handoff contracts.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from src.contracts.output_schema import (
    CaseOutput,
    Assessment,
    AffectedEntities,
    RootCauseAnalysis,
    CauseItem,
    ResponsibleParty,
    FinancialResolution
)


class MessageEnvelope(BaseModel):
    message_id: str
    run_id: str
    trace_id: str
    case_id: str
    order_id: str
    sender: str
    recipient: str
    message_type: str
    schema_version: str = "1.0"
    payload: Dict[str, Any] = Field(default_factory=dict)
    created_at: str


class InvestigationRequest(BaseModel):
    case_id: str
    order_id: str
    opened_at: str
    customer_request_message: str


class OrderSellerFacts(BaseModel):
    order_id: str
    order_status: str
    items: List[Dict[str, Any]] = Field(default_factory=list)
    sellers: List[Dict[str, Any]] = Field(default_factory=list)
    item_total_brl: float
    freight_total_brl: float
    seller_late_handoff: bool = False
    evidence_candidates: List[str] = Field(default_factory=list)


class PaymentFacts(BaseModel):
    order_id: str
    payment_rows: List[Dict[str, Any]] = Field(default_factory=list)
    payment_total_brl: float
    payment_count: int
    reconciled: bool = False
    evidence_candidates: List[str] = Field(default_factory=list)


class DeliveryFacts(BaseModel):
    order_id: str
    order_delivered_customer_date: Optional[str] = None
    order_estimated_delivery_date: Optional[str] = None
    order_delivered_carrier_date: Optional[str] = None
    delivered_late: bool = False
    delivered_within_estimate: bool = False
    evidence_candidates: List[str] = Field(default_factory=list)


class PolicyRequest(BaseModel):
    case_id: str
    order_id: str
    order_seller_facts: OrderSellerFacts
    payment_facts: PaymentFacts
    delivery_facts: DeliveryFacts
    policy_version: str = "EC_POLICY_V1"


class ResolutionDraft(BaseModel):
    case_id: str
    primary_issue: str
    case_status: str
    confidence: float
    order_ids: List[str]
    item_ids: List[str]
    seller_ids: List[str]
    payment_ids: List[str]
    ranked_causes: List[Dict[str, Any]]
    responsible_parties: List[Dict[str, Any]]
    evidence_ids: List[str]
    currency: str = "BRL"
    item_total_brl: float
    freight_total_brl: float
    payment_total_brl: float
    recommended_refund_brl: float
    resolution_actions: List[str]

    def to_case_output(self) -> CaseOutput:
        """Helper to convert flat ResolutionDraft to nested CaseOutput schema."""
        return CaseOutput(
            case_id=self.case_id,
            assessment=Assessment(
                primary_issue=self.primary_issue,
                case_status=self.case_status,
                confidence=self.confidence
            ),
            affected_entities=AffectedEntities(
                order_ids=self.order_ids,
                item_ids=self.item_ids,
                seller_ids=self.seller_ids,
                payment_ids=self.payment_ids
            ),
            root_cause_analysis=RootCauseAnalysis(
                ranked_causes=[CauseItem(**rc) for rc in self.ranked_causes],
                responsible_parties=[ResponsibleParty(**rp) for rp in self.responsible_parties]
            ),
            evidence_ids=self.evidence_ids,
            financial_resolution=FinancialResolution(
                currency=self.currency,
                item_total_brl=self.item_total_brl,
                freight_total_brl=self.freight_total_brl,
                payment_total_brl=self.payment_total_brl,
                recommended_refund_brl=self.recommended_refund_brl
            ),
            resolution_actions=self.resolution_actions
        )


class VerificationRequest(BaseModel):
    case_id: str
    draft: ResolutionDraft
    order_seller_facts: OrderSellerFacts
    payment_facts: PaymentFacts
    delivery_facts: DeliveryFacts


class VerificationResult(BaseModel):
    valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    verified_at: str
