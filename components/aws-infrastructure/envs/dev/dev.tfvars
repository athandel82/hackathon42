# dev environment values (ARCHITECTURE.md §6 — single `dev` env, §S6).
#   terraform plan  -var-file=envs/dev/dev.tfvars
#   terraform apply -var-file=envs/dev/dev.tfvars

region = "us-east-1"

# Bedrock — Ingest uses the most powerful invokable model (Opus 4.5).
# Analyze uses Sonnet 4.5: structured output is GA for it, and it comfortably
# fits the synchronous /analyze 30s API Gateway cap (multi-turn Opus would risk
# a 504). Both are Claude 4.x; the analyze-agent core.py fix makes them work
# with Strands structured output.
bedrock_model_id = "us.anthropic.claude-opus-4-5-20251101-v1:0"
analyze_model_id = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"

# Ingest is mechanical: the skill sequences deterministic tool calls to author
# the KB from already-extracted ARXML data — it does not need Opus-level
# reasoning. Opus 4.5 made a single ingest take ~9 min (many sequential authoring
# turns), which blew past the frontend wait. Sonnet 4.5 does the same job in
# ~2-3 min. (Analyze stays on Opus for impact reasoning.)
ingest_model_id = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"

# --- Lambda throughput (reserved concurrency) ------------------------------ #
# This workshop account is concurrency-capped: a WSConcurrencyCurtailer reserves
# the bulk of the 400 account limit, leaving ~103 UnreservedConcurrentExecutions
# with an AWS-enforced 100 floor. So our two functions can reserve ~10 total
# before an apply would push the unreserved pool below 100 and fail.
#
# ingest serves BOTH the sync API (POST /ingest, GET /status) and the async
# self-invoked worker; the frontend polls /status every ~2s during ingestion,
# and a low reserved value lets those polls starve the worker (throttle ->
# backoff -> multi-minute hang + duplicate runs). So ingest gets a generous
# guaranteed reservation (9), leaving the unreserved pool at ~101.
#
# analyze is left UNRESERVED (-1) on purpose: rather than capping it at a small
# number, it can burst into the entire ~101-slot unreserved pool — the most
# concurrency the account guardrail allows for the user-facing sync path.
# Per-invocation compute (memory, ephemeral storage, timeout) is independently
# maxed in modules/compute/main.tf.
ingest_reserved_concurrency  = 9
analyze_reserved_concurrency = -1

# --- frontend: reuse the existing workshop VPC networking ------------------ #
# Discovered in the account: workshop-vpc (vpc-0bb471fd910c268e9).
# The reused security group (sg-03a463cd3038ee65d) opens TCP 22 and 8443 — not
# 80 — so the SPA is served on 8443 (the port already open to the world).
frontend_subnet_id         = "subnet-0ee57d7e82a1863d4" # workshop-public-subnet (us-east-1a, public)
frontend_security_group_id = "sg-03a463cd3038ee65d"     # Workshop instances SG (22 + 8443)
frontend_port              = 8443

# Git URL the EC2 instance clones to build the SPA. Point at the repo that
# contains components/frontend (set this to your fork/clone URL).
frontend_repo_url = "https://github.com/CHANGE_ME/Workshop.git"
frontend_subdir   = "components/frontend"
