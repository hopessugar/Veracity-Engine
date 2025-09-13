#!/bin/bash

# --- Veracity Engine Backend Deployment Script ---
# This script provides commands to manually deploy the Cloud Function and manage its secrets.
#
# Prerequisites:
# 1. Google Cloud SDK (gcloud) installed and authenticated: `gcloud auth login`
# 2. Your Google Cloud Project ID is set: `gcloud config set project YOUR_PROJECT_ID`

# --- Configuration ---
# Change these variables to match your GCP setup.
GCP_PROJECT_ID=$(gcloud config get-value project)
REGION="us-central1"
FUNCTION_NAME="veracity-engine-api"
SERVICE_ACCOUNT_EMAIL=$(gcloud iam service-accounts list --filter="displayName:Cloud Functions Service Agent" --format="value(email)")

echo "--- Using Configuration ---"
echo "Project ID: $GCP_PROJECT_ID"
echo "Region: $REGION"
echo "Function Name: $FUNCTION_NAME"
echo "Service Account: $SERVICE_ACCOUNT_EMAIL"
echo "--------------------------"

# --- Step 1: Manage Secrets (Run these once) ---
# This section shows how to create secrets in Google Secret Manager.
# You will be prompted to enter the secret values securely.

echo "Creating secrets in Google Secret Manager (if they don't exist)..."
gcloud secrets create GEMINI_API_KEY --replication-policy="automatic" --project="$GCP_PROJECT_ID" || echo "Secret GEMINI_API_KEY already exists."
gcloud secrets create GOOGLE_API_KEY --replication-policy="automatic" --project="$GCP_PROJECT_ID" || echo "Secret GOOGLE_API_KEY already exists."

echo "Set the secret values. Paste your key when prompted and press Enter."
echo "Enter your Gemini API Key:"
read -s GEMINI_KEY_VALUE
echo "$GEMINI_KEY_VALUE" | gcloud secrets versions add GEMINI_API_KEY --data-file=- --project="$GCP_PROJECT_ID"

echo "Enter your Google API Key (for Safe Browsing/Fact Check):"
read -s GOOGLE_KEY_VALUE
echo "$GOOGLE_KEY_VALUE" | gcloud secrets versions add GOOGLE_API_KEY --data-file=- --project="$GCP_PROJECT_ID"

# --- Step 2: Grant Permissions ---
# The Cloud Function's service account needs permission to access the secrets.

echo "Granting Secret Manager access to the service account..."
gcloud secrets add-iam-policy-binding GEMINI_API_KEY \
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
  --role="roles/secretmanager.secretAccessor" \
  --project="$GCP_PROJECT_ID"

gcloud secrets add-iam-policy-binding GOOGLE_API_KEY \
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
  --role="roles/secretmanager.secretAccessor" \
  --project="$GCP_PROJECT_ID"


# --- Step 3: Deploy the Cloud Function ---
# This command packages and deploys the function.
# It links the secrets we created to the function's environment variables.

echo "Deploying the Cloud Function..."
gcloud functions deploy "$FUNCTION_NAME" \
  --gen2 \
  --region="$REGION" \
  --runtime=python311 \
  --source=./backend \
  --entry-point=veracity_engine_api \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars="APP_ENV=production,LOG_LEVEL=INFO,GCP_PROJECT_ID=$GCP_PROJECT_ID" \
  --set-secrets="GEMINI_API_KEY=GEMINI_API_KEY:latest,GOOGLE_API_KEY=GOOGLE_API_KEY:latest" \
  --project="$GCP_PROJECT_ID"

echo "--- Deployment Complete ---"
FUNCTION_URL=$(gcloud functions describe "$FUNCTION_NAME" --region="$REGION" --format="value(url)")
echo "Function URL: $FUNCTION_URL"