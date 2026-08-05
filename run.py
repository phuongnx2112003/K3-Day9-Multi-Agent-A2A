"""
Batch Runner. Owned by Member 3.
Processes EC_001.json through EC_050.json, writes verified outputs, and packages submission zip.
"""
import asyncio
import json
import uuid
import zipfile
from pathlib import Path
from src.settings import INPUT_DIR, OUTPUT_DIR, BASE_DIR
from src.tracing import init_trace_file, write_metadata, log_event
from src.data_access import DataAccessLayer
from src.agents.order_seller import OrderSellerAgent
from src.agents.payment import PaymentAgent
from src.agents.delivery import DeliveryAgent
from src.agents.policy import PolicyAgent
from src.agents.verifier import VerifierAgent
from src.agents.coordinator import CoordinatorAgent


def create_submission_zip(output_dir: Path, zip_path: Path) -> int:
    """Pack 50 EC_xxx.json files into submission zip without extra files."""
    json_files = sorted(list(output_dir.glob("EC_*.json")))
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for fpath in json_files:
            zf.write(fpath, arcname=fpath.name)
    return len(json_files)


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
    success_count = 0

    for file_path in input_files:
        trace_id = str(uuid.uuid4())
        with open(file_path, "r", encoding="utf-8") as f:
            case_input = json.load(f)

        draft = await coordinator.process_case(case_input, run_id, trace_id)
        if draft:
            output_data = draft.to_case_output().model_dump()
            target_path = OUTPUT_DIR / file_path.name
            temp_path = OUTPUT_DIR / f"{file_path.name}.tmp"
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            temp_path.replace(target_path)
            log_event(run_id, trace_id, case_input["case_id"], "output_written", "batch_runner")
            success_count += 1
        else:
            print(f"FAILED case {case_input['case_id']}")

    print(f"Batch run completed: {success_count}/{len(input_files)} cases succeeded!")

    if success_count == len(input_files):
        zip_path = BASE_DIR / "submission_output.zip"
        total_zipped = create_submission_zip(OUTPUT_DIR, zip_path)
        print(f"Successfully created submission zip at '{zip_path}' containing {total_zipped} JSON files.")

if __name__ == "__main__":
    asyncio.run(main())
