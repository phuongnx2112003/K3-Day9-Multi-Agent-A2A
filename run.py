"""
Batch Runner. Owned by Member 3.
Processes EC_001.json through EC_050.json and packages output zip.
"""
import asyncio
import json
import uuid
import zipfile
from pathlib import Path
from src.settings import INPUT_DIR, OUTPUT_DIR
from src.tracing import init_trace_file, write_metadata, log_event
from src.data_access import DataAccessLayer
from src.agents.order_seller import OrderSellerAgent
from src.agents.payment import PaymentAgent
from src.agents.delivery import DeliveryAgent
from src.agents.policy import PolicyAgent
from src.agents.verifier import VerifierAgent
from src.agents.coordinator import CoordinatorAgent


async def main():
    run_id = str(uuid.uuid4())
    init_trace_file()
    write_metadata()

    dal = DataAccessLayer()
    dal.load_data()

    order_seller = OrderSellerAgent(dal)
    payment = PaymentAgent(dal)
    delivery = DeliveryAgent(dal)
    policy = PolicyAgent()
    verifier = VerifierAgent(dal)

    coordinator = CoordinatorAgent(order_seller, payment, delivery, policy, verifier)

    input_files = sorted(list(INPUT_DIR.glob("EC_*.json")))
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Starting batch run {run_id} for {len(input_files)} cases...")

    for file_path in input_files:
        trace_id = str(uuid.uuid4())
        with open(file_path, "r", encoding="utf-8") as f:
            case_input = json.load(f)

        draft = await coordinator.process_case(case_input, run_id, trace_id)
        if draft:
            output_data = draft.model_dump()
            target_path = OUTPUT_DIR / file_path.name
            temp_path = OUTPUT_DIR / f"{file_path.name}.tmp"
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            temp_path.replace(target_path)
            log_event(run_id, trace_id, case_input["case_id"], "output_written", "batch_runner")

    print("Batch run completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
