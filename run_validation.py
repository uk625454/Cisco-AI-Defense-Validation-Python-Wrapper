import json
import os

from dotenv import load_dotenv

from aidef_validation_client import AIDefenseValidationClient


load_dotenv()


def main() -> None:
    api_key = os.environ["AIDEF_API_KEY"]
    base_url = os.environ.get("AIDEF_BASE_URL", "https://api.us.security.cisco.com")
    timeout = int(os.environ.get("AIDEF_TIMEOUT", "60"))

    client = AIDefenseValidationClient(
        api_key=api_key,
        base_url=base_url,
        timeout=timeout,
    )

    model_headers = []

    request_body_template = json.dumps(
       {
    "model": "olmo-2-0425-1b-instruct",
    "messages": [
      {
        "role": "user",
        "content": "{{prompt}}"
      }
    ],
    "max_tokens": 512,
    "temperature": 0.7
       }
    )

    response_json_path = ""

    start_resp = client.start_external_validation(
        test_name="",
        target_endpoint="",
        request_body_template=request_body_template,
        response_json_path=response_json_path,
        model_headers=model_headers,
        description="",
        language="LANGUAGE_EN",
        prompt_bank="PROMPT_BANK_DEFAULT",
    )

    task_id = start_resp["task_id"]
    print(f"Started validation task: {task_id}")

    final_job = client.wait_for_completion(task_id)
    print("Final job status:")
    print(json.dumps(final_job, indent=2))

    config = client.get_config(task_id)
    print("Validation config:")
    print(json.dumps(config, indent=2))

    results = client.get_results(task_id)
    print("Validation results:")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()