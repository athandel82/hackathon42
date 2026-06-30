# Backend configuration for the `dev` environment (ARCHITECTURE.md §6).
# Supplied at init time:
#   terraform init -backend-config=envs/dev/backend.hcl
#
# The state bucket and lock table are infra-only and must be bootstrapped once
# before the first init (see README.md "State backend bootstrap").

bucket         = "sdv-dev-tfstate-450947772796"
key            = "aws-infrastructure/dev/terraform.tfstate"
region         = "us-east-1"
dynamodb_table = "sdv-dev-tflock"
encrypt        = true
