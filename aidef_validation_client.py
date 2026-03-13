import time
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv


load_dotenv()


class AIDefenseValidationClient:
    def __init__(
        self,
        api_key: str,
        base_url: str,
        timeout: int = 60,
    ) -> None:
        if not api_key.strip():
            raise ValueError("AIDEF_API_KEY cannot be empty.")
        if not base_url.strip():
            raise ValueError("AIDEF_BASE_URL cannot be empty.")
        if timeout <= 0:
            raise ValueError("timeout must be greater than 0.")

        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "x-cisco-ai-defense-tenant-api-key": self.api_key,
            }
        )

    def _url(self, path: str) -> str:
        return f"{self.base_url}/api/ai-defense/v1/{path.lstrip('/')}"

    def create_custom_goal(
        self,
        name: str,
        goal: str,
    ) -> Dict[str, Any]:
        payload = {
            "name": name,
            "goal": goal,
        }

        resp = self.session.post(
            self._url("ai-validation/custom-goals"),
            json=payload,
            timeout=self.timeout,
        )

        if not resp.ok:
            raise RuntimeError(
                f"Create custom goal failed: status={resp.status_code}, body={resp.text}"
            )

        return resp.json()

    def list_custom_goals(self) -> Dict[str, Any]:
        resp = self.session.get(
            self._url("ai-validation/custom-goals"),
            timeout=self.timeout,
        )

        if not resp.ok:
            raise RuntimeError(
                f"List custom goals failed: status={resp.status_code}, body={resp.text}"
            )

        return resp.json()

    def delete_custom_goal(self, goal_id: str) -> None:
        resp = self.session.delete(
            self._url(f"ai-validation/custom-goals/{goal_id}"),
            timeout=self.timeout,
        )

        if not resp.ok:
            raise RuntimeError(
                f"Delete custom goal failed: status={resp.status_code}, body={resp.text}"
            )

    def start_external_validation(
        self,
        test_name: str,
        target_endpoint: str,
        request_body_template: str,
        response_json_path: str,
        model_headers: Optional[List[Dict[str, str]]] = None,
        description: Optional[str] = None,
        language: str = "LANGUAGE_EN",
        prompt_bank: str = "PROMPT_BANK_DEFAULT",
        external_api_provider: Optional[str] = None,
        connector_id: Optional[str] = None,
        oauth_client_id: Optional[str] = None,
        oauth_client_secret: Optional[str] = None,
        oauth_token_url: Optional[str] = None,
        oauth_scopes: Optional[List[str]] = None,
        multi_turn_enabled: Optional[bool] = None,
        additional_config: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "asset_type": "EXTERNAL",
            "validation_scan_name": test_name,
            "model_endpoint_url_model_id": target_endpoint,
            "model_request_template": request_body_template,
            "model_response_json_path": response_json_path,
            "language": language,
            "prompt_bank": prompt_bank,
        }

        if model_headers:
            payload["headers"] = model_headers
        if description:
            payload["description"] = description
        if external_api_provider:
            payload["external_api_provider"] = external_api_provider
        if connector_id:
            payload["connector_id"] = connector_id
        if oauth_client_id:
            payload["oauth_client_id"] = oauth_client_id
        if oauth_client_secret:
            payload["oauth_client_secret"] = oauth_client_secret
        if oauth_token_url:
            payload["oauth_token_url"] = oauth_token_url
        if oauth_scopes:
            payload["oauth_scopes"] = oauth_scopes
        if multi_turn_enabled is not None:
            payload["multi_turn_enabled"] = multi_turn_enabled
        if additional_config:
            payload["additional_config"] = additional_config

        resp = self.session.post(
            self._url("ai-validation/start"),
            json=payload,
            timeout=self.timeout,
        )

        if not resp.ok:
            raise RuntimeError(
                f"Single-turn validation start failed: "
                f"status={resp.status_code}, body={resp.text}"
            )

        return resp.json()

    def start_multi_turn_validation(
        self,
        test_name: str,
        target_endpoint: str,
        request_body_template: str,
        response_json_path: str,
        model_headers: Optional[List[Dict[str, str]]] = None,
        description: Optional[str] = None,
        language: str = "LANGUAGE_EN",
        prompt_bank: str = "PROMPT_BANK_DEFAULT",
        use_custom_goals: bool = False,
        external_api_provider: Optional[str] = None,
        connector_id: Optional[str] = None,
        oauth_client_id: Optional[str] = None,
        oauth_client_secret: Optional[str] = None,
        oauth_token_url: Optional[str] = None,
        oauth_scopes: Optional[List[str]] = None,
        additional_config: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "asset_type": "EXTERNAL",
            "validation_scan_name": test_name,
            "model_endpoint_url_model_id": target_endpoint,
            "model_request_template": request_body_template,
            "model_response_json_path": response_json_path,
            "language": language,
            "prompt_bank": prompt_bank,
            "use_custom_goals": use_custom_goals,
        }

        if model_headers:
            payload["headers"] = model_headers
        if description:
            payload["description"] = description
        if external_api_provider:
            payload["external_api_provider"] = external_api_provider
        if connector_id:
            payload["connector_id"] = connector_id
        if oauth_client_id:
            payload["oauth_client_id"] = oauth_client_id
        if oauth_client_secret:
            payload["oauth_client_secret"] = oauth_client_secret
        if oauth_token_url:
            payload["oauth_token_url"] = oauth_token_url
        if oauth_scopes:
            payload["oauth_scopes"] = oauth_scopes
        if additional_config:
            payload["additional_config"] = additional_config

        resp = self.session.post(
            self._url("ai-validation/start/multi"),
            json=payload,
            timeout=self.timeout,
        )

        if not resp.ok:
            raise RuntimeError(
                f"Multi-turn validation start failed: "
                f"status={resp.status_code}, body={resp.text}"
            )

        return resp.json()

    def list_jobs(
        self,
        limit: int = 20,
        offset: int = 0,
        status: Optional[str] = None,
        asset_type: Optional[str] = None,
        search_string: Optional[str] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "limit": limit,
            "offset": offset,
        }
        if status:
            params["status"] = status
        if asset_type:
            params["asset_type"] = asset_type
        if search_string:
            params["search_string"] = search_string

        resp = self.session.get(
            self._url("ai-validation/jobs"),
            params=params,
            timeout=self.timeout,
        )

        if not resp.ok:
            raise RuntimeError(
                f"List jobs failed: status={resp.status_code}, body={resp.text}"
            )

        return resp.json()

    def get_results(self, task_id: str) -> Dict[str, Any]:
        resp = self.session.get(
            self._url(f"ai-validation/results/{task_id}"),
            timeout=self.timeout,
        )

        if not resp.ok:
            raise RuntimeError(
                f"Get results failed: status={resp.status_code}, body={resp.text}"
            )

        return resp.json()

    def get_config(self, task_id: str) -> Dict[str, Any]:
        resp = self.session.get(
            self._url(f"ai-validation/config/{task_id}"),
            timeout=self.timeout,
        )

        if not resp.ok:
            raise RuntimeError(
                f"Get config failed: status={resp.status_code}, body={resp.text}"
            )

        return resp.json()

    def wait_for_completion(
        self,
        task_id: str,
        poll_interval_seconds: int = 20,
        timeout_seconds: int = 7200,
    ) -> Dict[str, Any]:
        if poll_interval_seconds <= 0:
            raise ValueError("poll_interval_seconds must be greater than 0.")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than 0.")

        start = time.time()

        terminal_statuses = {
            "JOB_COMPLETED",
            "JOB_FAILED",
            "JOB_CANCELLED",
            "JOB_ABORTED",
        }

        while True:
            jobs = self.list_jobs(limit=100, offset=0)
            matching_job = None

            for item in jobs.get("jobs", []):
                job = item.get("job", {})
                if job.get("task_id") == task_id:
                    matching_job = job
                    break

            if matching_job:
                status = matching_job.get("status")
                if status in terminal_statuses:
                    return matching_job

            if time.time() - start > timeout_seconds:
                raise TimeoutError(
                    f"Timed out waiting for validation task {task_id} to complete."
                )

            time.sleep(poll_interval_seconds)