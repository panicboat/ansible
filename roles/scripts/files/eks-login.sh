#!/usr/bin/env bash
# eks-login.sh - Source this to assume eks-admin-${env} role and update
# kubeconfig for the panicboat platform EKS cluster.
#
# Usage:
#   source ./eks-login.sh [environment]
#
# Default environment: production.
# MUST be sourced (not executed) so that AWS_* env vars persist in the
# parent shell. Session is valid for 1 hour (matches the role's
# max_session_duration in aws/eks/modules/iam_admin.tf).
#
# Prerequisites:
#   - aws CLI v2 with credentials configured for an IAM principal that has
#     sts:AssumeRole permission on the eks-admin-${env} role
#   - jq
#   - kubectl

if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
  echo "ERROR: This script must be sourced, not executed." >&2
  echo "Usage: source $(basename "$0") [environment]" >&2
  exit 1
fi

_env="${1:-production}"
_region="ap-northeast-1"

_account_id=$(aws sts get-caller-identity --query 'Account' --output text)
_role_arn="arn:aws:iam::${_account_id}:role/eks-admin-${_env}"

echo "[eks-login] Assuming ${_role_arn}..."
_creds=$(aws sts assume-role \
  --role-arn "${_role_arn}" \
  --role-session-name "kubectl-${USER:-debug}" \
  --query 'Credentials' \
  --output json)

export AWS_ACCESS_KEY_ID=$(echo "${_creds}" | jq -r .AccessKeyId)
export AWS_SECRET_ACCESS_KEY=$(echo "${_creds}" | jq -r .SecretAccessKey)
export AWS_SESSION_TOKEN=$(echo "${_creds}" | jq -r .SessionToken)

aws sts get-caller-identity --query 'Arn' --output text
aws eks update-kubeconfig --region "${_region}" --name "eks-${_env}"

echo "[eks-login] Done. AWS_* env vars exported. Session valid for 1 hour."
unset _env _region _account_id _role_arn _creds
