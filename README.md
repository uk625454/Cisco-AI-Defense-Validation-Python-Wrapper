# Cisco AI Defense Validation Python Wrapper

## What this wrapper does

This Python wrapper automates the full lifecycle of Cisco AI Defense validation tests for model, agent, and application endpoints. The wrapper supports single-turn scans, multi-turn scans (with optional custom goals), and also enables multi-turn scans on external endpoints with custom API formats. 

- **Core Capabilities**
  - Single-turn validation tests
  - Multi-turn validation tests
  - Multi-turn with custom goal testing
  - Interactive CLI configuration
  - Well-known API provider request / response format (OpenAI, Anthropic, Gemini, Mistral)
  - Custom API provider request / response format
  - Secure header injection
  - Parameter persistence + reuse
  - Prompt bank selection
  - Automatic test lifecycle polling
 
## AI Defense API calls used by this wrapper

This wrapper talks to the **Cisco AI Defense Management API** over HTTPS and authenticates every request with the tenant management API key in the `x-cisco-ai-defense-tenant-api-key` header. 

**Management API Reference for Validation:** https://developer.cisco.com/docs/ai-defense-management/get-ai-validation-config/

**Instructions to generate management API key:** https://developer.cisco.com/docs/ai-defense-management/authentication/

The base pattern is:

```text
https://<regional-base-url>/api/ai-defense/v1/<endpoint>
```

In this wrapper, the API client layer is `aidef_validation_client.py`, and that file makes the following Management API calls:

### 1. Start a single-turn validation

**Method:** `POST`  
**Endpoint:** `/ai-validation/start`

**Why the wrapper uses it:**
This launches a single-turn validation run against an external endpoint.

**Request format used by the wrapper:**

```json
{
  "asset_type": "EXTERNAL",
  "validation_scan_name": "My validation run",
  "model_endpoint_url_model_id": "https://target-endpoint.example.com",
  "model_request_template": "{...}",
  "model_response_json_path": "choices.0.message.content",
  "language": "LANGUAGE_EN",
  "prompt_bank": "PROMPT_BANK_DEFAULT"
}
```

**Optional fields the wrapper may also include:**

```json
{
  "headers": [{"key": "Authorization", "value": "Bearer ..."}],
  "description": "Optional description",
  "external_api_provider": "EXTERNAL_API_PROVIDER_OPENAI",
  "connector_id": "...",
  "oauth_client_id": "...",
  "oauth_client_secret": "...",
  "oauth_token_url": "...",
  "oauth_scopes": ["..."],
  "multi_turn_enabled": false,
  "additional_config": "..."
}
```

### 2. Start a multi-turn validation

**Method:** `POST`  
**Endpoint:** `/ai-validation/start/multi`

**Why the wrapper uses it:**
This launches a conversational multi-turn validation run. The wrapper uses this when the user selects multi-turn mode.

**Request format used by the wrapper:**

```json
{
  "asset_type": "EXTERNAL",
  "validation_scan_name": "My multi-turn validation run",
  "model_endpoint_url_model_id": "https://target-endpoint.example.com",
  "model_request_template": "{...}",
  "model_response_json_path": "choices.0.message.content",
  "language": "LANGUAGE_EN",
  "prompt_bank": "PROMPT_BANK_DEFAULT",
  "use_custom_goals": false
}
```

### 3. Create a custom goal

**Method:** `POST`  
**Endpoint:** `/ai-validation/custom-goals`

**Why the wrapper uses it:**
For multi-turn testing, the wrapper can create user-defined goals that tell AI Defense what behavior to try to elicit.

**Request format used by the wrapper:**

```json
{
  "name": "Goal display name",
  "goal": "Natural-language goal description"
}
```

### 4. List custom goals

**Method:** `GET`  
**Endpoint:** `/ai-validation/custom-goals`

**Why the wrapper uses it:**
Before a multi-turn run, the wrapper can show the user existing goals so they can decide whether to reuse or delete them.

### 5. Delete a custom goal

**Method:** `DELETE`  
**Endpoint:** `/ai-validation/custom-goals/{goal_id}`

**Why the wrapper uses it:**
The wrapper can clean up existing custom goals before or after a run.

### 6. List validation jobs

**Method:** `GET`  
**Endpoint:** `/ai-validation/jobs`

**Why the wrapper uses it:**
This is the wrapper's polling source of truth. After starting a validation, the wrapper repeatedly calls this endpoint and looks for the matching `task_id` until the job reaches a terminal status.

**Query parameters the wrapper may send:**

```text
limit
offset
status
asset_type
search_string
```

### 7. Get validation config for a task

**Method:** `GET`  
**Endpoint:** `/ai-validation/config/{task_id}`

**Why the wrapper uses it:**
After a run starts or completes, the wrapper can fetch the stored config so the user can verify exactly what AI Defense accepted and saved for that task.

### 8. Get validation results for a task

**Method:** `GET`  
**Endpoint:** `/ai-validation/results/{task_id}`

**Why the wrapper uses it:**
After the validation reaches a terminal state, the wrapper calls this endpoint to retrieve the final findings for the run.

### How these API calls map to the wrapper flow

The wrapper lifecycle is:

1. Collect endpoint, request template, response path, headers, provider, and validation type from the user.
2. Call either `POST /ai-validation/start` or `POST /ai-validation/start/multi`.
3. Read the returned `task_id`.
4. Poll `GET /ai-validation/jobs` until the task reaches a terminal state.
5. Call `GET /ai-validation/config/{task_id}` to show what was submitted.
6. Call `GET /ai-validation/results/{task_id}` to retrieve the results.
7. If the user is doing a custom-goal workflow, also call the custom-goal endpoints before or after the run.

## Files in this wrapper

### `aidef_validation_client.py`
This is the API client layer. It handles calls to the Cisco AI Defense Management API, including:

- start single-turn validation
- start multi-turn validation
- create/list/delete custom goals
- list jobs
- fetch config
- fetch results
- wait for completion

### `run_validation.py`
This is the interactive entrypoint users run. It:

- asks the user what kind of validation they want
- collects endpoint details
- optionally loads or saves reusable endpoint configs
- manages custom goals for multi-turn runs
- starts the validation
- prints results

## What the user needs before running this wrapper

Before running the script, the user needs all of the following:

### 1. Python installed
A working Python 3 installation is required.

### 2. Cisco AI Defense tenant API key
The wrapper talks to the Cisco AI Defense Management API, so the user must have a valid:

- `AIDEF_API_KEY`(Instructions in Step 6 of 'Step-by-step setup' section)

### 3. Reachable target endpoint
The external endpoint being validated must be reachable by Cisco AI Defense.

Examples:
- an OpenAI-compatible endpoint
- an Anthropic-compatible endpoint
- an Azure OpenAI endpoint
- an internal agent or gateway endpoint that Cisco AI Defense can reach

### 4. Correct request body template
The user must know the JSON request format that the target endpoint expects.

If you select a well-know API provider (OpenAI, Anthropic, Gemini, Mistral) or unspecified, the template **must include**:

```text
{{prompt}}
```
If you select custom for your API provider, the template **must include**:

```text
{{true_template_prompt}}
```

This is where Cisco AI Defense inserts the attack prompt during validation.

### 5. Correct response path
The user must know the JSON path where the model or agent response is returned.

Example:

```text
choices.0.message.content
```

or:

```text
structured_response.content
```

### 6. Headers if the endpoint requires them
If the endpoint requires headers such as:

- `Authorization`
- `x-api-key`
- session tokens
- cookies
- gateway headers

the user must know those values before running the script.

### 7. Fresh session-based credentials if applicable
If the endpoint depends on browser session cookies or short-lived tokens, the user needs to be aware that these may expire quickly.

That matters because the validation may fail even if a manual curl worked earlier, if the session has expired by the time Cisco AI Defense performs the pre-flight check.

## Step-by-step setup

### Step 1: Put the files in one folder

The folder should contain at least:

- `aidef_validation_client.py`
- `run_validation.py`
- `requirements.txt`
- `.env` or `.env.example`

### Step 2: Open a terminal in that folder

Example:

```bash
cd /path/to/your/folder
```

### Step 3: Create a virtual environment

This avoids package conflicts and avoids system Python installation issues.

```bash
python3 -m venv .venv
```

### Step 4: Activate the virtual environment

macOS / Linux:

```bash
source .venv/bin/activate
```

After activation, the terminal usually shows something like:

```text
(.venv)
```

### Step 5: Install dependencies

```bash
pip install -r requirements.txt
```

A typical `requirements.txt` should include:

```text
requests
python-dotenv
```

### Step 6: Create the `.env` file

Create a local `.env` file in the same folder.

Example:

```env
AIDEF_API_KEY=<YOUR_TENANT_MGMT_API_KEY>
AIDEF_BASE_URL=https://api.us.security.cisco.com
AIDEF_TIMEOUT=60
BEDROCK_BEARER_TOKEN=<TOKEN>
```
Instructions to create AI Defense Management API Key: https://developer.cisco.com/docs/ai-defense-management/authentication/

**IMPORTANT:** Use environment variables for sensitive headers. You can reference the variable using '$' (ex. $BEDROCK_BEARER_TOKEN) when you are prompted for the header value for a specific header key. 

### Why this is needed

- `AIDEF_API_KEY` authenticates to the Cisco AI Defense Management API
- `AIDEF_BASE_URL` tells the wrapper which AI Defense API base URL to use
- `AIDEF_TIMEOUT` controls request timeout behavior

## How to run the wrapper

From the project folder, with the virtual environment activated:

```bash
python run_validation.py
```

## What the script will ask the user

The wrapper is interactive. It will guide the user through the configuration.

### 1. Validation type

The script first asks:

- `Single-turn`
- `Multi-turn`

### 2. Validation test name

The script asks for the overall test name. This is the name that appears in Cisco AI Defense for the validation run.

### 3. Load saved endpoint configuration file (optional)

If saved config files already exist in the local folder, the script can load one. The first time you run the scrip there will be no config files to load. 

This helps avoid retyping:

- provider
- target URL
- headers
- response path
- request template

If a saved config is loaded, the script can still ask whether the user wants to add more headers.

### 4. External API provider

The script asks the user to select a provider by number.

Supported values for single-turn scans:

- `EXTERNAL_API_PROVIDER_UNSPECIFIED`
- `EXTERNAL_API_PROVIDER_AZURE_OPENAI`
- `EXTERNAL_API_PROVIDER_OPENAI`
- `EXTERNAL_API_PROVIDER_ANTHROPIC`
- `EXTERNAL_API_PROVIDER_GEMINI`

Supported values for multi-turn scans:

- `API_PROVIDER_CUSTOM`
- `EXTERNAL_API_PROVIDER_AZURE_OPENAI`
- `EXTERNAL_API_PROVIDER_OPENAI`
- `EXTERNAL_API_PROVIDER_ANTHROPIC`
- `EXTERNAL_API_PROVIDER_GEMINI`

### Important rule for multi-turn
If your endpoint API format is custom and does not align with any of the well-known provider formats presented, please select 'API_PROVIDER_CUSTOM'

### 5. Target endpoint URL

The script asks for the full URL of the target model, agent or application endpoint.

### 6. Headers

The script asks whether the endpoint requires headers.

If yes, it collects them one by one as:

- header key
- header value (can reference environment variable using '$' - eg. $BEDROCK_BEARER_TOKEN

Then it asks whether the user has more headers to add.

### 7. Path to model response

The script asks for the response path where the model or agent output lives in the returned JSON.

### 8. Request body JSON template

The script asks the user to paste the full JSON request body template.

The user pastes multiline JSON and finishes by typing:

```text
END
```
For single-turn scans: 

If a well-known API provider or unspecified is selected, the template must include:

```text
{{prompt}}
```
For multi-turn scans:

If a well-known API provider is selected, the template must include:

```text
{{prompt}}
```

If API_PROVIDER_CUSTOM is selected, the template must include:

```text
{{true_template_prompt}}
```

### Why this is required
Without `{{prompt}}` or `{{true_template_prompt}}`, Cisco AI Defense would have nowhere to insert the validation prompt.

## Single-turn flow

For single-turn runs, after endpoint parameters are collected, the script asks for the prompt bank.

Prompt bank options:

- `PROMPT_BANK_DEFAULT`
- `PROMPT_BANK_QUICK_SCAN`

Then, if the endpoint configuration was entered manually instead of loaded from file, the script asks whether the user wants to save it for future runs.

Then it starts the validation.

## Multi-turn flow

For multi-turn runs, a well-know provider or API_PROVIDER_CUSTOM must first be selected.

Then it asks whether the user wants to use custom goals.

### If the user says **yes** to custom goals
The script will:

1. list existing custom goals
2. ask whether the user wants to delete any existing custom goals before the test
3. allow deletion by:
   - goal numbers
   - or `all`
4. ask whether the user wants to create new custom goals
5. optionally ask whether the user wants to delete all custom goals after the test

In this custom-goal path, the script uses:

```text
PROMPT_BANK_DEFAULT
```

### If the user says **no** to custom goals
The script asks the user to select a prompt bank:

- `PROMPT_BANK_DEFAULT`
- `PROMPT_BANK_QUICK_SCAN`

Then, if the endpoint configuration was entered manually instead of loaded from file, the script asks whether the user wants to save it for future runs.

Then it starts the validation.

## Saved endpoint configuration files

The wrapper can save endpoint settings into local JSON files.

These saved files include:

- config name
- external API provider
- target endpoint
- model headers
- response path
- request body template

### Why this helps

It saves time for repeated testing against the same endpoint and avoids having to re-enter:

- long URLs
- many headers
- complex request templates

### How file naming works

The script checks the local folder for existing saved config files and creates a new unique filename automatically.

Examples:

- `saved_endpoint_configs.json`
- `saved_endpoint_configs_1.json`
- `saved_endpoint_configs_2.json`

### Why this matters

This prevents the script from overwriting an older saved configuration file.

## What the script prints after starting a validation

After a validation starts, the script prints:

- validation task ID
- final job status
- validation config
- validation results

This helps the user confirm:

- what was actually submitted
- whether the job completed
- what findings were returned

## Things the user should be aware of

### 1. Session-based headers may expire
If the endpoint uses:

- cookies
- secure session tokens
- short-lived gateway credentials

then the validation may fail later even if a manual curl worked earlier.

This usually shows up as:

- `401 Unauthorized`

### Why
Cisco AI Defense does its own pre-flight request and then the actual validation traffic. If the auth context is stale by then, the endpoint may reject the request.

### 2. The request template must match the endpoint exactly
The wrapper validates that the JSON is syntactically correct, but it does not know whether the schema is correct for the target endpoint.

### Why this matters
A valid JSON template can still fail if the endpoint expects a different structure.

### 3. The response path must be correct
If the response path is wrong, Cisco AI Defense may not be able to extract the model response correctly.

### Why this matters
That can cause pre-flight or validation issues, or produce empty results.

### 4. Saved config files may contain sensitive data
Saved endpoint config files may include:

- auth headers
- cookies
- session tokens
- internal URLs

### Why this matters
They should be treated as sensitive local files and should not be shared casually.

## Error handling built into the wrapper

The wrapper includes handling for:

- missing environment variables
- invalid timeout values
- invalid JSON request templates
- missing `{{prompt}}`
- malformed saved config files
- invalid saved header shapes
- API errors returned by Cisco AI Defense
- keyboard interrupt / manual cancellation
- timeout while polling validation completion

### Why this matters
Without these checks, users would get vague failures that are harder to debug.

## Recommended usage pattern

A good workflow for a user is:

1. validate the endpoint manually with curl first
2. confirm the correct:
   - headers
   - request body
   - response path
3. run the wrapper
4. save the endpoint config if it is likely to be reused
5. refresh session headers if the endpoint uses short-lived auth

## Final note

This wrapper is best used as a **repeatable validation launcher** for Cisco AI Defense when testing external model, agent, or application endpoints that may require:

- custom request JSON
- custom headers
- provider-specific configuration
- multi-turn testing
- custom-goal workflows
