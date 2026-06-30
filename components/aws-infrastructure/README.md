# aws-infrastructure

Terraform IaC for the SDV platform. Provisions the AWS runtime for all
components: the HTTP API, the two agent Lambdas (container images), storage and
supporting services, and the frontend EC2 instance. See [`ARCHITECTURE.md`](./ARCHITECTURE.md).

## Layout

```
aws-infrastructure/
├── main.tf            # provider, S3 backend, module wiring (storage→compute→api→frontend)
├── variables.tf
├── outputs.tf
├── modules/
│   ├── storage/       # S3 KB bucket + DynamoDB repos/results tables
│   ├── compute/       # ECR ×2 + image build/push + both Lambdas + IAM + env vars
│   ├── api/           # HTTP API + routes + CORS(*) + proxy integrations
│   └── frontend/      # EC2 (reused VPC/subnet/SG); user-data builds SPA, writes config.json
└── envs/
    └── dev/
        ├── backend.hcl   # S3 state + DynamoDB lock config
        └── dev.tfvars    # dev variable values (reused VPC networking, model id, repo url)
```

Apply order is acyclic — `storage → compute → api → frontend`. `api` does not
depend on `frontend` (CORS `*`), which breaks the EC2↔API cycle.

## Prerequisites

- Terraform ≥ 1.5, Docker (with buildx), AWS credentials.
- The agent components must be buildable container images before `apply`:
  - `../ingestion-agent/Dockerfile` (present)
  - `../analyze-agent/Dockerfile` (must exist — that component builds it per its §11.1)
- Images are built for **linux/arm64** (Lambda `arm64`/Graviton) by default, which
  builds natively on an arm64 host. Set `-var lambda_architecture=x86_64` (and the
  build switches to `linux/amd64`) to follow ARCHITECTURE.md §S7 instead.

## State backend bootstrap (one-time)

The S3 state bucket and DynamoDB lock table can't be created by the same config
that uses them as a backend, so create them once:

```bash
aws s3api create-bucket --bucket sdv-dev-tfstate-CHANGEME --region us-east-1
aws s3api put-bucket-versioning --bucket sdv-dev-tfstate-CHANGEME \
  --versioning-configuration Status=Enabled
aws dynamodb create-table --table-name sdv-dev-tflock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST --region us-east-1
```

Then set the matching `bucket` / `dynamodb_table` in `envs/dev/backend.hcl`.

## Usage

```bash
# Init with the dev backend (omit -backend-config for a quick local-state try).
terraform init -backend-config=envs/dev/backend.hcl

terraform plan  -var-file=envs/dev/dev.tfvars
terraform apply -var-file=envs/dev/dev.tfvars

# Useful outputs
terraform output api_url        # frontend apiBaseUrl
terraform output frontend_url
terraform output kb_bucket
```

Set `frontend_repo_url` in `dev.tfvars` to the git URL the EC2 instance clones
to build the SPA. To skip the EC2 instance, pass `-var deploy_frontend=false`.

## Notes on reused networking

The frontend instance reuses the existing **workshop-vpc** subnet and security
group rather than creating its own (per deployment guidance). That security
group opens TCP **22** and **8443** (not 80), so the SPA is served on **8443**
(`frontend_port`). If you open port 80 on the group, set `frontend_port = 80`.

## Validation

```bash
terraform fmt -recursive -check
terraform init -backend=false
terraform validate
```
