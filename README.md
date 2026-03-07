# Cisco-AI-Defense-Validation-Python-Wrapper

## Overview

This folder contains a Python-based wrapper that allows you to **start and monitor a Cisco AI Defense validation run** against an **EXTERNAL model endpoint** directly from **Visual Studio Code**.

Instead of launching validation manually through the AI Defense dashboard UI, this wrapper enables you to:

- start a validation scan programmatically
- target an external application / agent / model endpoint
- optionally include HTTP headers required by the endpoint
- wait for the validation job to finish
- retrieve:
  - job status
  - validation configuration
  - validation results

The wrapper interacts with the **Cisco AI Defense Management API**.

---

# What This Folder Does

When you run the script, the following workflow occurs:

1. Load configuration from `.env`
2. Authenticate with the **Cisco AI Defense Management API**
3. Start a validation run using:

POST /api/ai-defense/v1/ai-validation/start

4. Receive a `task_id`
5. Poll validation jobs until the job completes
6. Retrieve:
   - validation job details
   - validation configuration
   - validation results

Everything is printed to the **VS Code terminal**.

---

# Files in This Folder

The folder should already contain the following files:

aidef_validation_client.py  
run_validation.py  
requirements.txt  
.env  
README.md  

## aidef_validation_client.py

This file contains the **API client** that communicates with Cisco AI Defense.

Responsibilities:

- authenticate to the Management API
- start validation runs
- list validation jobs
- retrieve validation configuration
- retrieve validation results
- poll until validation completes

This file **usually does not need to be modified**.

---

## run_validation.py

This is the **script you execute**.

Responsibilities:

- load environment variables
- configure validation parameters
- define request body template
- define response extraction path
- optionally define endpoint headers
- start the validation
- print results

This is the file where **customer-specific values are configured**.

---

## .env

This file stores environment variables such as:

- Cisco AI Defense API key
- Management API base URL
- timeout values

---

## requirements.txt

Lists the Python packages required to run the wrapper.

---

# Visual Studio Code Setup

# Step 1 — Open the folder in VS Code

Open Visual Studio Code.

Click:

File → Open Folder

Select the folder that contains the files.

---

# Step 2 — Open the VS Code Terminal

### Method 1 — Keyboard shortcut

Mac:

Control + `

Windows/Linux:

Ctrl + `

---

### Method 2 — Menu

Click:

Terminal → New Terminal

---

### Method 3 — Command Palette

Open the Command Palette:

Mac:

Cmd + Shift + P

Windows/Linux:

Ctrl + Shift + P

Then type:

Terminal: Create New Terminal

Press **Enter**.

When the terminal opens, it appears at the bottom of VS Code.

---

# Step 3 — Confirm the Terminal is in the Project Folder

Run:

ls

You should see:

aidef_validation_client.py  
run_validation.py  
requirements.txt  
.env  
README.md  

---

# Step 4 — Create a Python Virtual Environment

Run:

python -m venv .venv

If your system requires python3:

python3 -m venv .venv

---

# Step 5 — Activate the Virtual Environment

## macOS / Linux

source .venv/bin/activate

## Windows PowerShell

.venv\Scripts\Activate.ps1

## Windows Command Prompt

.venv\Scripts\activate

Your terminal prompt should now include:

(.venv)

---

# Step 6 — Install Dependencies

Install required Python packages:

pip install -r requirements.txt

Contents of requirements.txt:

requests  
python-dotenv

---

# Step 7 — Select the Python Interpreter in VS Code

Open Command Palette:

Cmd + Shift + P  
or  
Ctrl + Shift + P

Search for:

Python: Select Interpreter

Select the interpreter inside:

.venv

Example:

.venv/bin/python  
or  
.venv\Scripts\python.exe

---

# Step 8 — Configure the `.env` File

Open `.env` and update the values.

IMPORTANT - Instructions on how to generate Management API Key - https://developer.cisco.com/docs/ai-defense-management/authentication/

Example:

AIDEF_API_KEY=<CUSTOMER_AI_DEFENSE__MGMT_API_KEY>  
AIDEF_BASE_URL=https://api.us.security.cisco.com  
AIDEF_TIMEOUT=60

Update:

- **AIDEF_API_KEY** → Customer Cisco AI Defense Management API key 

---

# Step 9 — Configure `run_validation.py`

This file contains the **customer-specific configuration**.

## Replace Target Endpoint

Find:

target_endpoint=""

Replace with the **target endpoint URL**.

Example:

target_endpoint="https://customer-ai-api.company.com/v1/chat/completions"

---

## Configure Request Body Template

Find:

request_body_template = json.dumps(<Request Body Template>)

Update to match the **API request body format**.

Important rule:

{{prompt}}

must appear where the **user input should go**.

---

## Configure Response JSON Path

Find:

response_json_path = ""

Update to match where the **model output appears in the response JSON**.

Examples:

OpenAI-style:

"choices.0.message.content"

Custom wrapper:

"structured_response.content"

---

## Configure Test Name

Find:

test_name=""

Example replacement:

test_name="External Validation"

---

## Configure Description

Find:

description=""

Replace with:

description="Customer validation run triggered via Python wrapper"

---

# Optional: Configure Headers

The script includes this section:

model_headers = []

This means **no headers are sent to the model endpoint**.

---

# Example — Adding Headers

If the endpoint requires authentication headers:

model_headers = [
{"key": "Authorization", "value": "Bearer CUSTOMER_TOKEN"},
{"key": "x-api-key", "value": "CUSTOMER_API_KEY"}
]

If headers are required, they must be added here.

---

# Step 10 — Run the Script

From the VS Code terminal run:

python run_validation.py

or if required:

python3 run_validation.py

---

# Expected Output

Example output:

Started validation task: 123456789

Final job status:
{ ... }

Validation config:
{ ... }

Validation results:
{ ... }

This confirms:

- validation was started
- the job completed
- results were retrieved successfully

---

# Customer Environment Checklist

Before running validation ensure:

- Cisco AI Defense Management API key is correct
- Management API base URL is correct (https://api.security.cisco.com)
- Endpoint URL is reachable
- request body template matches endpoint format
- response JSON path correctly extracts the application / agent / model output
- headers are configured if required
- OAuth settings added if endpoint requires them

---

# Common Issues

## 401 / 403 Errors

Usually caused by:

- incorrect API key
- incorrect base URL
- insufficient API permissions

---

## 400 Bad Request

Usually caused by:

- incorrect request template
- invalid enum values
- malformed JSON body

---

## Validation Tests Skipped

Often caused by:

- incorrect request template
- incorrect response path
- missing required headers

---

# Recommended Best Practice

Before running AI Defense validation, verify the endpoint manually using:

- curl
- Postman
- a simple Python script

Confirm:

- endpoint accepts the request
- response JSON is correct
- model output exists at the specified response path

---

# Summary

This wrapper allows you to:

- automate Cisco AI Defense validation
- run tests directly from VS Code
- support external model endpoints
- optionally add authentication headers
- retrieve results programmatically

The two most important configuration values are:

request_body_template  
response_json_path

If those are correct, validation should run successfully.
