import json
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from aidef_validation_client import AIDefenseValidationClient


load_dotenv()


EXTERNAL_API_PROVIDER_OPTIONS = {
    1: "EXTERNAL_API_PROVIDER_UNSPECIFIED",
    2: "EXTERNAL_API_PROVIDER_AZURE_OPENAI",
    3: "EXTERNAL_API_PROVIDER_OPENAI",
    4: "EXTERNAL_API_PROVIDER_ANTHROPIC",
    5: "EXTERNAL_API_PROVIDER_GEMINI",
}

PROMPT_BANK_OPTIONS = {
    1: "PROMPT_BANK_DEFAULT",
    2: "PROMPT_BANK_QUICK_SCAN",
}

SAVED_CONFIG_FILE_PREFIX = "saved_endpoint_configs"
SAVED_CONFIG_FILE_EXTENSION = ".json"


def prompt_non_empty(prompt_text: str) -> str:
    while True:
        value = input(prompt_text).strip()
        if value:
            return value
        print("Value cannot be empty. Please try again.")


def prompt_yes_no(prompt_text: str) -> bool:
    while True:
        value = input(prompt_text).strip().lower()
        if value in {"y", "yes"}:
            return True
        if value in {"n", "no"}:
            return False
        print("Please enter yes or no.")


def prompt_integer(prompt_text: str, minimum: int = 0) -> int:
    while True:
        raw_value = input(prompt_text).strip()
        try:
            value = int(raw_value)
            if value < minimum:
                print(f"Please enter a number greater than or equal to {minimum}.")
                continue
            return value
        except ValueError:
            print("Please enter a valid integer.")


def prompt_run_mode() -> str:
    while True:
        print("\nSelect validation type:")
        print("1. Single-turn")
        print("2. Multi-turn")
        choice = input("Enter 1 or 2: ").strip()

        if choice == "1":
            return "single"
        if choice == "2":
            return "multi"

        print("Invalid selection. Please enter 1 or 2.")


def prompt_external_api_provider(allow_unspecified: bool = True) -> str:
    print("\nSelect external API provider:")
    for number, provider in EXTERNAL_API_PROVIDER_OPTIONS.items():
        print(f"{number}. {provider}")

    if not allow_unspecified:
        print(
            "\nFor multi-turn validation, EXTERNAL_API_PROVIDER_UNSPECIFIED is not allowed."
        )

    while True:
        choice = input("Enter the number of the external API provider: ").strip()
        try:
            number = int(choice)
            if number in EXTERNAL_API_PROVIDER_OPTIONS:
                provider = EXTERNAL_API_PROVIDER_OPTIONS[number]
                if not allow_unspecified and provider == "EXTERNAL_API_PROVIDER_UNSPECIFIED":
                    print(
                        "Please select a provider other than EXTERNAL_API_PROVIDER_UNSPECIFIED."
                    )
                    continue
                return provider
        except ValueError:
            pass

        print("Invalid selection. Please enter one of the listed numbers.")


def prompt_prompt_bank() -> str:
    print("\nSelect prompt bank:")
    for number, prompt_bank in PROMPT_BANK_OPTIONS.items():
        print(f"{number}. {prompt_bank}")

    while True:
        choice = input("Enter the number of the prompt bank: ").strip()
        try:
            number = int(choice)
            if number in PROMPT_BANK_OPTIONS:
                return PROMPT_BANK_OPTIONS[number]
        except ValueError:
            pass

        print("Invalid selection. Please enter one of the listed numbers.")


def prompt_headers() -> List[Dict[str, str]]:
    headers: List[Dict[str, str]] = []

    has_headers = prompt_yes_no(
        "\nDoes the endpoint require headers? (yes/no): "
    )
    if not has_headers:
        return headers

    while True:
        key = prompt_non_empty("Enter header key: ")
        value = prompt_non_empty("Enter header value: ")
        headers.append({"key": key, "value": value})

        has_more = prompt_yes_no("Do you have another header to add? (yes/no): ")
        if not has_more:
            break

    return headers


def prompt_additional_headers(existing_headers: List[Dict[str, str]]) -> List[Dict[str, str]]:
    updated_headers = list(existing_headers)

    add_more = prompt_yes_no(
        "\nWould you like to add more headers to this loaded configuration? (yes/no): "
    )
    if not add_more:
        return updated_headers

    while True:
        key = prompt_non_empty("Enter additional header key: ")
        value = prompt_non_empty("Enter additional header value: ")
        updated_headers.append({"key": key, "value": value})

        has_more = prompt_yes_no("Do you have another additional header to add? (yes/no): ")
        if not has_more:
            break

    return updated_headers


def prompt_multiline_json(prompt_text: str) -> str:
    print(prompt_text)
    print("Paste JSON below. Type END on a new line when finished.\n")

    lines: List[str] = []
    while True:
        line = input()
        if line.strip() == "END":
            break
        lines.append(line)

    raw_json = "\n".join(lines).strip()

    if not raw_json:
        raise ValueError("Request body template cannot be empty.")

    if "{{prompt}}" not in raw_json:
        raise ValueError(
            "The request body template must include {{prompt}} where the validation prompt should be inserted."
        )

    try:
        parsed = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON provided: {exc}")

    return json.dumps(parsed)


def normalize_custom_goals_response(raw_response: Any) -> List[Dict[str, Any]]:
    if isinstance(raw_response, list):
        return [item for item in raw_response if isinstance(item, dict)]

    if isinstance(raw_response, dict):
        for key in ["custom_goals", "results", "data", "items"]:
            value = raw_response.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]

    return []


def extract_goal_id(goal: Dict[str, Any]) -> Optional[str]:
    for key in ["custom_goal_id", "goal_id", "id"]:
        value = goal.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return None


def extract_goal_name(goal: Dict[str, Any]) -> str:
    for key in ["name", "goal_name", "title"]:
        value = goal.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return "<no name returned>"


def extract_goal_text(goal: Dict[str, Any]) -> str:
    for key in ["goal", "goal_text", "text", "description"]:
        value = goal.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return "<no goal text returned>"


def list_existing_custom_goals(client: AIDefenseValidationClient) -> List[Dict[str, Any]]:
    print("\nRetrieving existing custom goals...")
    raw_response = client.list_custom_goals()
    custom_goals = normalize_custom_goals_response(raw_response)

    if not custom_goals:
        print("No existing custom goals were found.")
        return []

    print("\nExisting custom goals:")
    for index, goal in enumerate(custom_goals, start=1):
        goal_id = extract_goal_id(goal) or "<no id returned>"
        goal_name = extract_goal_name(goal)
        goal_text = extract_goal_text(goal)

        print(f"{index}. {goal_name}")
        print(f"   ID: {goal_id}")
        print(f"   Goal: {goal_text}")

    return custom_goals


def prompt_for_existing_goal_deletions(existing_goals: List[Dict[str, Any]]) -> List[str]:
    if not existing_goals:
        return []

    delete_existing = prompt_yes_no(
        "\nWould you like to delete any existing custom goals before starting the test? (yes/no): "
    )
    if not delete_existing:
        return []

    while True:
        raw_selection = input(
            "Enter the numbers of the custom goals to delete, separated by commas "
            "(for example: 1,3,4), or type 'all' to delete ALL existing custom goals: "
        ).strip().lower()

        if raw_selection == "all":
            goal_ids_to_delete: List[str] = []
            for goal in existing_goals:
                goal_id = extract_goal_id(goal)
                if goal_id:
                    goal_ids_to_delete.append(goal_id)
            return goal_ids_to_delete

        if not raw_selection:
            print("Please enter at least one number or 'all'.")
            continue

        try:
            selected_indexes = []
            for part in raw_selection.split(","):
                index = int(part.strip())
                if index < 1 or index > len(existing_goals):
                    raise ValueError
                selected_indexes.append(index)

            selected_indexes = sorted(set(selected_indexes))

            goal_ids_to_delete: List[str] = []
            for index in selected_indexes:
                goal_id = extract_goal_id(existing_goals[index - 1])
                if goal_id:
                    goal_ids_to_delete.append(goal_id)

            return goal_ids_to_delete

        except ValueError:
            print(
                "Invalid selection. Please enter valid goal numbers separated by commas, or type 'all'."
            )


def delete_goal_ids(
    client: AIDefenseValidationClient,
    goal_ids: List[str],
    label: str,
) -> None:
    if not goal_ids:
        print(f"\nNo {label} custom goals to delete.")
        return

    print(f"\nDeleting {label} custom goals...")
    for goal_id in goal_ids:
        try:
            client.delete_custom_goal(goal_id)
            print(f"Deleted custom goal: {goal_id}")
        except Exception as exc:
            print(f"Failed to delete custom goal {goal_id}: {exc}")


def prompt_for_new_custom_goals() -> List[Dict[str, str]]:
    custom_goals: List[Dict[str, str]] = []

    create_new_goals = prompt_yes_no(
        "\nWould you like to create new custom goals for this multi-turn validation? (yes/no): "
    )
    if not create_new_goals:
        return custom_goals

    number_of_goals = prompt_integer(
        "How many new custom goals would you like to create? ",
        minimum=1,
    )

    for index in range(number_of_goals):
        print(f"\nEntering new custom goal {index + 1} of {number_of_goals}")
        goal_name = prompt_non_empty("Enter custom goal name: ")
        goal_text = prompt_non_empty("Enter custom goal text: ")
        custom_goals.append({"name": goal_name, "goal": goal_text})

    return custom_goals


def create_custom_goals_if_needed(
    client: AIDefenseValidationClient,
    custom_goals: List[Dict[str, str]],
) -> List[str]:
    created_goal_ids: List[str] = []

    if not custom_goals:
        return created_goal_ids

    print("\nCreating new custom goals...")
    for goal in custom_goals:
        response = client.create_custom_goal(
            name=goal["name"],
            goal=goal["goal"],
        )
        print("Created custom goal:")
        print(json.dumps(response, indent=2))

        goal_id = response.get("custom_goal_id")
        if isinstance(goal_id, str) and goal_id.strip():
            created_goal_ids.append(goal_id)
        else:
            print("Warning: Could not find custom_goal_id in the create response.")

    return created_goal_ids


def discover_saved_config_files() -> List[str]:
    files: List[str] = []
    for file_name in os.listdir("."):
        if (
            file_name.startswith(SAVED_CONFIG_FILE_PREFIX)
            and file_name.endswith(SAVED_CONFIG_FILE_EXTENSION)
            and os.path.isfile(file_name)
        ):
            files.append(file_name)

    def sort_key(name: str) -> tuple[int, str]:
        if name == f"{SAVED_CONFIG_FILE_PREFIX}{SAVED_CONFIG_FILE_EXTENSION}":
            return (0, name)

        base = name.removesuffix(SAVED_CONFIG_FILE_EXTENSION)
        suffix = base.replace(f"{SAVED_CONFIG_FILE_PREFIX}_", "")
        try:
            return (int(suffix) + 1, name)
        except ValueError:
            return (999999, name)

    return sorted(files, key=sort_key)


def get_unique_config_filename() -> str:
    existing_files = discover_saved_config_files()
    base_name = f"{SAVED_CONFIG_FILE_PREFIX}{SAVED_CONFIG_FILE_EXTENSION}"

    if base_name not in existing_files:
        return base_name

    index = 1
    while True:
        candidate = f"{SAVED_CONFIG_FILE_PREFIX}_{index}{SAVED_CONFIG_FILE_EXTENSION}"
        if candidate not in existing_files:
            return candidate
        index += 1


def validate_loaded_config(config: Dict[str, Any]) -> Dict[str, Any]:
    required_keys = [
        "name",
        "external_api_provider",
        "target_endpoint",
        "model_headers",
        "response_json_path",
        "request_body_template",
    ]

    missing = [key for key in required_keys if key not in config]
    if missing:
        raise ValueError(
            f"Loaded config is missing required keys: {', '.join(missing)}"
        )

    if not isinstance(config["name"], str) or not config["name"].strip():
        raise ValueError("Loaded config 'name' must be a non-empty string.")

    if (
        not isinstance(config["external_api_provider"], str)
        or not config["external_api_provider"].strip()
    ):
        raise ValueError("Loaded config 'external_api_provider' must be a non-empty string.")

    if (
        not isinstance(config["target_endpoint"], str)
        or not config["target_endpoint"].strip()
    ):
        raise ValueError("Loaded config 'target_endpoint' must be a non-empty string.")

    if (
        not isinstance(config["response_json_path"], str)
        or not config["response_json_path"].strip()
    ):
        raise ValueError("Loaded config 'response_json_path' must be a non-empty string.")

    if (
        not isinstance(config["request_body_template"], str)
        or not config["request_body_template"].strip()
    ):
        raise ValueError("Loaded config 'request_body_template' must be a non-empty string.")

    if "{{prompt}}" not in config["request_body_template"]:
        raise ValueError(
            "Loaded config 'request_body_template' must include {{prompt}}."
        )

    try:
        json.loads(config["request_body_template"])
    except json.JSONDecodeError as exc:
        raise ValueError(f"Loaded config request_body_template is invalid JSON: {exc}")

    if not isinstance(config["model_headers"], list):
        raise ValueError("Loaded config 'model_headers' must be a list.")

    for header in config["model_headers"]:
        if not isinstance(header, dict):
            raise ValueError("Each loaded header must be a dictionary.")
        if "key" not in header or "value" not in header:
            raise ValueError("Each loaded header must contain 'key' and 'value'.")
        if not isinstance(header["key"], str) or not isinstance(header["value"], str):
            raise ValueError("Loaded header 'key' and 'value' must both be strings.")

    return config


def load_saved_config_file(filename: str) -> Optional[Dict[str, Any]]:
    try:
        with open(filename, "r", encoding="utf-8") as file:
            data = json.load(file)
    except Exception:
        return None

    if isinstance(data, dict):
        configs = data.get("configs", [])
        if isinstance(configs, list) and configs:
            config = configs[0]
            if isinstance(config, dict):
                return config

    return None


def prompt_load_saved_config() -> Optional[Dict[str, Any]]:
    config_files = discover_saved_config_files()

    if not config_files:
        print("\nNo saved endpoint configuration files were found.")
        return None

    wants_load = prompt_yes_no(
        "\nWould you like to load a saved endpoint configuration file? (yes/no): "
    )
    if not wants_load:
        return None

    print("\nSaved endpoint configuration files:")
    for index, file_name in enumerate(config_files, start=1):
        print(f"{index}. {file_name}")

    while True:
        choice = input("Enter the number of the saved configuration file to load: ").strip()
        try:
            index = int(choice)
            if 1 <= index <= len(config_files):
                selected_file = config_files[index - 1]
                config = load_saved_config_file(selected_file)
                if config is None:
                    print(f"Could not load a valid config from {selected_file}.")
                    return None

                validated = validate_loaded_config(config)
                print(f"\nLoaded saved configuration file: {selected_file}")
                return validated
        except ValueError as exc:
            print(f"Invalid saved config: {exc}")
            return None

        print("Invalid selection. Please enter one of the listed numbers.")


def save_endpoint_config_file(config_data: Dict[str, Any]) -> None:
    filename = get_unique_config_filename()
    payload = {"configs": [config_data]}

    with open(filename, "w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2)

    print(f"\nSaved endpoint configuration file: {filename}")


def prompt_save_current_config(
    external_api_provider: str,
    target_endpoint: str,
    model_headers: List[Dict[str, str]],
    response_json_path: str,
    request_body_template: str,
) -> None:
    should_save = prompt_yes_no(
        "\nWould you like to save these endpoint parameters for future runs? (yes/no): "
    )
    if not should_save:
        return

    config_name = prompt_non_empty("Enter a name for this saved configuration: ")

    config_data = {
        "name": config_name,
        "external_api_provider": external_api_provider,
        "target_endpoint": target_endpoint,
        "model_headers": model_headers,
        "response_json_path": response_json_path,
        "request_body_template": request_body_template,
    }

    save_endpoint_config_file(config_data)


def collect_endpoint_parameters(allow_unspecified_provider: bool) -> Dict[str, Any]:
    saved_config = prompt_load_saved_config()

    if saved_config is not None:
        external_api_provider = saved_config["external_api_provider"]

        if (
            not allow_unspecified_provider
            and external_api_provider == "EXTERNAL_API_PROVIDER_UNSPECIFIED"
        ):
            print(
                "\nThe loaded configuration uses EXTERNAL_API_PROVIDER_UNSPECIFIED, "
                "which is not allowed for this multi-turn flow."
            )
            external_api_provider = prompt_external_api_provider(
                allow_unspecified=False
            )

        target_endpoint = saved_config["target_endpoint"]
        model_headers = saved_config["model_headers"]
        response_json_path = saved_config["response_json_path"]
        request_body_template = saved_config["request_body_template"]

        if model_headers:
            model_headers = prompt_additional_headers(model_headers)
        else:
            print("\nThe loaded configuration has no headers.")
            model_headers = prompt_headers()

        return {
            "external_api_provider": external_api_provider,
            "target_endpoint": target_endpoint,
            "model_headers": model_headers,
            "response_json_path": response_json_path,
            "request_body_template": request_body_template,
            "loaded_from_saved_config": True,
        }

    external_api_provider = prompt_external_api_provider(
        allow_unspecified=allow_unspecified_provider
    )
    target_endpoint = prompt_non_empty("\nEnter target endpoint URL: ")
    model_headers = prompt_headers()
    response_json_path = prompt_non_empty("\nEnter path to model response: ")
    request_body_template = prompt_multiline_json(
        "\nEnter the request body JSON template.\n"
        "Use {{prompt}} where the validation attack prompt should be inserted."
    )

    return {
        "external_api_provider": external_api_provider,
        "target_endpoint": target_endpoint,
        "model_headers": model_headers,
        "response_json_path": response_json_path,
        "request_body_template": request_body_template,
        "loaded_from_saved_config": False,
    }


def main() -> None:
    api_key = os.environ.get("AIDEF_API_KEY", "").strip()
    base_url = os.environ.get("AIDEF_BASE_URL", "https://api.us.security.cisco.com").strip()
    timeout_raw = os.environ.get("AIDEF_TIMEOUT", "60").strip()

    if not api_key:
        raise ValueError("AIDEF_API_KEY is missing or empty in the environment.")

    try:
        timeout = int(timeout_raw)
    except ValueError as exc:
        raise ValueError("AIDEF_TIMEOUT must be a valid integer.") from exc

    client = AIDefenseValidationClient(
        api_key=api_key,
        base_url=base_url,
        timeout=timeout,
    )

    run_mode = prompt_run_mode()
    test_name = prompt_non_empty("\nEnter validation test name: ")

    if run_mode == "single":
        endpoint_parameters = collect_endpoint_parameters(
            allow_unspecified_provider=True
        )
    else:
        endpoint_parameters = collect_endpoint_parameters(
            allow_unspecified_provider=False
        )

    external_api_provider = endpoint_parameters["external_api_provider"]
    target_endpoint = endpoint_parameters["target_endpoint"]
    model_headers = endpoint_parameters["model_headers"]
    response_json_path = endpoint_parameters["response_json_path"]
    request_body_template = endpoint_parameters["request_body_template"]
    loaded_from_saved_config = endpoint_parameters["loaded_from_saved_config"]

    oauth_client_id: Optional[str] = None
    oauth_client_secret: Optional[str] = None
    oauth_token_url: Optional[str] = None
    oauth_scopes: Optional[List[str]] = None

    delete_all_custom_goals_after_test = False

    try:
        if run_mode == "single":
            prompt_bank = prompt_prompt_bank()

            if not loaded_from_saved_config:
                prompt_save_current_config(
                    external_api_provider=external_api_provider,
                    target_endpoint=target_endpoint,
                    model_headers=model_headers,
                    response_json_path=response_json_path,
                    request_body_template=request_body_template,
                )

            print("\nStarting single-turn validation...")

            start_resp = client.start_external_validation(
                test_name=test_name,
                target_endpoint=target_endpoint,
                request_body_template=request_body_template,
                response_json_path=response_json_path,
                model_headers=model_headers,
                description="External single-turn validation",
                language="LANGUAGE_EN",
                prompt_bank=prompt_bank,
                external_api_provider=external_api_provider,
                oauth_client_id=oauth_client_id,
                oauth_client_secret=oauth_client_secret,
                oauth_token_url=oauth_token_url,
                oauth_scopes=oauth_scopes,
            )

        else:
            use_custom_goals = prompt_yes_no(
                "\nWould you like to use custom goals for this multi-turn validation? (yes/no): "
            )

            if use_custom_goals:
                existing_goals = list_existing_custom_goals(client)

                goal_ids_to_delete_before_test = prompt_for_existing_goal_deletions(
                    existing_goals
                )
                delete_goal_ids(client, goal_ids_to_delete_before_test, "selected existing")

                new_custom_goals = prompt_for_new_custom_goals()
                create_custom_goals_if_needed(client, new_custom_goals)

                delete_all_custom_goals_after_test = prompt_yes_no(
                    "\nWould you like to delete ALL custom goals after the test finishes? (yes/no): "
                )

                prompt_bank = "PROMPT_BANK_DEFAULT"
            else:
                prompt_bank = prompt_prompt_bank()

            if not loaded_from_saved_config:
                prompt_save_current_config(
                    external_api_provider=external_api_provider,
                    target_endpoint=target_endpoint,
                    model_headers=model_headers,
                    response_json_path=response_json_path,
                    request_body_template=request_body_template,
                )

            print("\nStarting multi-turn validation...")

            start_resp = client.start_multi_turn_validation(
                test_name=test_name,
                target_endpoint=target_endpoint,
                request_body_template=request_body_template,
                response_json_path=response_json_path,
                model_headers=model_headers,
                description="External multi-turn validation",
                language="LANGUAGE_EN",
                prompt_bank=prompt_bank,
                use_custom_goals=use_custom_goals,
                external_api_provider=external_api_provider,
                oauth_client_id=oauth_client_id,
                oauth_client_secret=oauth_client_secret,
                oauth_token_url=oauth_token_url,
                oauth_scopes=oauth_scopes,
            )

        task_id = start_resp["task_id"]
        print(f"\nStarted validation task: {task_id}")

        final_job = client.wait_for_completion(task_id)
        print("\nFinal job status:")
        print(json.dumps(final_job, indent=2))

        config = client.get_config(task_id)
        print("\nValidation config:")
        print(json.dumps(config, indent=2))

        results = client.get_results(task_id)
        print("\nValidation results:")
        print(json.dumps(results, indent=2))

    finally:
        if delete_all_custom_goals_after_test:
            try:
                final_goals = list_existing_custom_goals(client)
                all_goal_ids = [
                    goal_id
                    for goal in final_goals
                    if (goal_id := extract_goal_id(goal))
                ]
                delete_goal_ids(client, all_goal_ids, "all")
            except Exception as exc:
                print(f"\nFailed to delete all custom goals after the test: {exc}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except ValueError as exc:
        print(f"\nConfiguration error: {exc}")
    except RuntimeError as exc:
        print(f"\nRuntime error: {exc}")
    except Exception as exc:
        print(f"\nUnexpected error: {exc}")