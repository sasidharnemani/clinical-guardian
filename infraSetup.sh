#!/bin/bash

# Clinical Guardian - Infrastructure Setup for BigQuery AI Hackathon
# Usage: ./setup_infrastructure.sh [PROJECT_ID]

set -e  # Exit on any error

# Configuration
PROJECT_ID=${1:-$(gcloud config get-value project)}
REGION="us-central1"
BQ_LOCATION="US"
DATASET_ID="clinical_knowledge_integrity"
BUCKET_NAME="${PROJECT_ID}-clinical-guardian"
CONNECTION_NAME="clinical-guardian-ai-connection"

echo "======================================"
echo "Clinical Guardian - Infrastructure Setup"
echo "======================================"
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "BigQuery Location: $BQ_LOCATION"
echo "Dataset: $DATASET_ID"
echo "Bucket: $BUCKET_NAME"
echo "Connection: $CONNECTION_NAME"
echo "======================================"

# Step 1: Validate Prerequisites
echo ""
echo "Step 1: Validating prerequisites..."

# Check authentication
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "."; then
    echo "Error: No active gcloud authentication found."
    echo "Please run: gcloud auth login"
    exit 1
fi
echo "- Authentication validated"

# Check project access
if ! gcloud projects describe $PROJECT_ID >/dev/null 2>&1; then
    echo "Error: Cannot access project $PROJECT_ID"
    exit 1
fi
echo "- Project access confirmed"

# Set project
gcloud config set project $PROJECT_ID --quiet
echo "- Project set to $PROJECT_ID"

# Check billing
BILLING_ENABLED=$(gcloud beta billing projects describe $PROJECT_ID --format="value(billingEnabled)" 2>/dev/null || echo "false")
if [ "$BILLING_ENABLED" != "True" ]; then
    echo "Error: Billing is not enabled for project $PROJECT_ID"
    exit 1
fi
echo "- Billing is enabled"

# Step 2: Enable Required APIs
echo ""
echo "Step 2: Enabling required APIs..."

APIS=(
    "bigquery.googleapis.com"
    "storage.googleapis.com"
    "aiplatform.googleapis.com"
    "bigqueryconnection.googleapis.com"
)

for api in "${APIS[@]}"; do
    echo "- Enabling $api..."
    gcloud services enable $api --quiet
done

echo "Waiting for APIs to be fully enabled (30 seconds)..."
sleep 30

# Step 3: Create BigQuery Dataset
echo ""
echo "Step 3: Creating BigQuery dataset..."

if ! bq show --dataset $PROJECT_ID:$DATASET_ID >/dev/null 2>&1; then
    bq mk --dataset \
        --location=$BQ_LOCATION \
        --description="Clinical Guardian - AI-powered healthcare knowledge platform" \
        $PROJECT_ID:$DATASET_ID
    echo "- Dataset created: $DATASET_ID"
else
    echo "- Dataset already exists: $DATASET_ID"
fi

# Step 4: Create Cloud Storage Bucket
echo ""
echo "Step 4: Creating Cloud Storage bucket..."

if ! gsutil ls gs://$BUCKET_NAME >/dev/null 2>&1; then
    gsutil mb -l $BQ_LOCATION gs://$BUCKET_NAME
    echo "- Bucket created: $BUCKET_NAME"
else
    echo "- Bucket already exists: $BUCKET_NAME"
fi

# Step 5: Create Vertex AI Connection for BigQuery
echo "Step 5: Creating Vertex AI connection..."

# List existing connections safely (ignore headers, blank lines)
EXISTING_CONNECTIONS=$(bq ls --connection --project_id="$PROJECT_ID" --location="$BQ_LOCATION" 2>/dev/null | awk 'NR>2 {print $1}')

# Count matches for your connection name
if echo "$EXISTING_CONNECTIONS" | grep -qw "$CONNECTION_NAME"; then
    echo "- Connection already exists: $CONNECTION_NAME"
else
    bq mk --connection \
        --location="$BQ_LOCATION" \
        --project_id="$PROJECT_ID" \
        --connection_type=CLOUD_RESOURCE \
        "$CONNECTION_NAME"
    echo "- Connection created: $CONNECTION_NAME"
    sleep 10
fi


# Get connection service account and grant permissions
echo ""
echo "Step 6: Configuring connection permissions..."

# --- FIX: Add a retry loop to handle the propagation delay of the connection's service account ---
MAX_RETRIES=6
RETRY_DELAY=10 # in seconds
CONNECTION_SA="" # Initialize as empty

for i in $(seq 1 $MAX_RETRIES); do
    echo "- Attempt $i/$MAX_RETRIES: Fetching connection service account..."
    
    # Try to get the service account ID
    CONNECTION_SA=$(bq show --connection --project_id=$PROJECT_ID --location=$BQ_LOCATION  --format=json $CONNECTION_NAME | \
        python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('cloudResource', {}).get('serviceAccountId', ''))" 2>/dev/null || echo "")

    # If the service account ID is found, break the loop
    if [ ! -z "$CONNECTION_SA" ]; then
        echo "- Success: Found service account."
        break
    fi

    # If it's the last attempt, don't wait
    if [ "$i" -eq "$MAX_RETRIES" ]; then
        break
    fi

    echo "- Service account not yet available. Waiting ${RETRY_DELAY}s..."
    sleep $RETRY_DELAY
done
# --- END FIX ---


# Now, proceed with the original logic, but with a much higher chance of success
if [ ! -z "$CONNECTION_SA" ]; then
    echo "- Connection service account: $CONNECTION_SA"
    
    # Grant necessary roles to the connection's service account
    ROLES=(
        "roles/aiplatform.user"
        "roles/bigquery.connectionUser"
        "roles/storage.objectViewer" # If you use GCS data
        "roles/storage.objectAdmin"
        "roles/iam.serviceAccountTokenCreator"
    )
    
    for role in "${ROLES[@]}"; do
        echo "- Granting $role..."
        gcloud projects add-iam-policy-binding $PROJECT_ID \
            --member="serviceAccount:$CONNECTION_SA" \
            --role="$role" \
            --quiet >/dev/null 2>&1
    done
    
    echo "- Permissions configured successfully"
else
    echo ""
    echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
    echo "!!! CRITICAL WARNING: Could not retrieve connection service account after multiple retries."
    echo "!!! You must configure permissions manually in the IAM console."
    echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
fi

# Step 7: Create Core BigQuery Tables
echo ""
echo "Step 7: Creating BigQuery tables..."

# Ground truth master table
echo "- Creating ground_truth_master table..."
bq query --use_legacy_sql=false --replace=true << EOF
CREATE OR REPLACE TABLE \`$PROJECT_ID.$DATASET_ID.ground_truth_master\` (
    id STRING,
    drug_name STRING,
    device_name STRING,
    condition STRING,
    old_dosage STRING,
    new_dosage STRING,
    old_warning STRING,
    new_warning STRING,
    old_indication STRING,
    new_indication STRING,
    recall_reason STRING,
    risk_level STRING,
    update_date DATE,
    source_url STRING,
    clinical_significance STRING,
    patient_safety_impact STRING,
    compliance_deadline DATE,
    manufacturer STRING,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);
EOF

# Document embeddings table for vector search
echo "- Creating document_embeddings table..."
bq query --use_legacy_sql=false --replace=true << EOF
CREATE OR REPLACE TABLE \`$PROJECT_ID.$DATASET_ID.document_embeddings\` (
    document_id STRING,
    document_name STRING,
    document_content STRING,
    content_embedding ARRAY<FLOAT64>,
    document_type STRING,
    risk_level STRING,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);
EOF

# FDA Adverse Events table
echo "- Creating fda_adverse_events table..."
bq query --use_legacy_sql=false --replace=true << EOF
CREATE OR REPLACE TABLE \`$PROJECT_ID.$DATASET_ID.fda_adverse_events\` (
    safetyreportid STRING,
    receivedate STRING,
    serious INT64,
    reporttype STRING,
    fulfillexpeditecriteria STRING,
    occurcountry STRING,
    reporter_qualification STRING,
    patientonsetage FLOAT64,
    patientsex STRING,
    medicinalproduct STRING,
    brand_name STRING,
    manufacturer_name STRING,
    drugcharacterization STRING,
    action_taken_with_drug STRING,
    drugindication STRING,
    drugdosagetext STRING,
    reactions STRING,
    reaction_outcomes STRING,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    source_file STRING
);
EOF

# FDA Recalls table
echo "- Creating fda_recalls table..."
bq query --use_legacy_sql=false --replace=true << EOF
CREATE OR REPLACE TABLE \`$PROJECT_ID.$DATASET_ID.fda_recalls\` (
    WEB_ADDRESS STRING,
    RECALL_NUMBER STRING,
    PRODUCT_DESCRIPTION STRING,
    TRADE_NAME STRING,
    RECALL_CLASS INT64,
    CENTER STRING,
    CENTER_CLASSIFICATION_DT STRING,
    POSTED_INTERNET_DT STRING,
    TERMINATION_DT STRING,
    FIRM_NAME STRING,
    MANUFACTURER_RECALL_REASON STRING,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);
EOF

# Knowledge base master table (for document metadata)
echo "- Creating knowledge_base_master table..."
bq query --use_legacy_sql=false --replace=true << EOF
CREATE OR REPLACE TABLE \`$PROJECT_ID.$DATASET_ID.knowledge_base_master\` (
    document_id STRING,
    document_name STRING,
    document_uri STRING,
    document_type STRING,
    source_format STRING,
    content_text STRING,
    upload_timestamp TIMESTAMP,
    processing_status STRING,
    extracted_entities ARRAY<STRUCT<
        entity_type STRING,
        entity_value STRING,
        confidence FLOAT64
    >>,
    document_metadata STRUCT<
        page_count INT64,
        file_size_bytes INT64,
        creation_date DATE,
        last_modified TIMESTAMP
    >,
    embeddings ARRAY<FLOAT64>,
    processed_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);
EOF

# Create Object Table for multimodal processing (Approach 3)
echo "- Creating object table for multimodal processing..."
bq query --use_legacy_sql=false --replace=true << EOF
CREATE OR REPLACE EXTERNAL TABLE \`$PROJECT_ID.$DATASET_ID.clinical_documents_object_table\`
WITH CONNECTION \`$PROJECT_ID.$BQ_LOCATION.${CONNECTION_NAME}\`
OPTIONS (
    object_metadata = 'SIMPLE',
    uris = ['gs://${BUCKET_NAME}/*']
);
EOF

# Step 8: Create BigQuery ML Models
echo ""
echo "Step 8: Creating BigQuery ML models..."

# Create Gemini model for text generation
echo "- Creating Gemini model for text generation..."
echo "This step can take upto 3 minutes"

bq query --use_legacy_sql=false --replace=true "
CREATE OR REPLACE MODEL \`$PROJECT_ID.$DATASET_ID.clinical_knowledge_integrity\`
REMOTE WITH CONNECTION \`projects/$PROJECT_ID/locations/US/connections/$CONNECTION_NAME\`
OPTIONS (
  remote_service_type = 'CLOUD_AI_LARGE_LANGUAGE_MODEL_V1',
  endpoint = 'gemini-2.5-flash'
)"
echo "  If the model creation fails due to permissions still not in place, please create at the end manually in the BQ console using the SQL..."
echo "  Permissions needed are - https://cloud.google.com/bigquery/docs/generate-text-tutorial#grant-permissions"


# Step 9: Verify Final Setup and Provide Next Steps
echo ""
echo "==================================================="
echo " Final Setup Verification"
echo "==================================================="

VERIFICATION_FAILED=false

# Check 1: BigQuery Dataset
echo -n "  - Verifying BigQuery Dataset..."
if bq show --dataset $PROJECT_ID:$DATASET_ID >/dev/null 2>&1; then
    echo " [OK]"
else
    echo " [FAILED]"
    VERIFICATION_FAILED=true
fi

# Check 2: BigQuery Connection
echo -n "  - Verifying BigQuery Connection..."
if bq show --connection --project_id=$PROJECT_ID --location=$BQ_LOCATION $CONNECTION_NAME >/dev/null 2>&1; then
    echo " [OK]"
else
    echo " [FAILED]"
    VERIFICATION_FAILED=true
fi

# Check 3: The Critical AI Model
echo -n "  - Verifying BigQuery AI Model..."
if bq show --model $PROJECT_ID:$DATASET_ID.clinical_knowledge_integrity >/dev/null 2>&1; then
    echo " [OK]"
else
    echo " [FAILED]"
    VERIFICATION_FAILED=true
fi

echo ""

# Final Summary and Next Steps
if [ "$VERIFICATION_FAILED" = true ]; then
    echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
    echo "!!! WARNING: One or more critical resources failed verification."
    echo "!!! Please review the logs above before proceeding."
    echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
else
    echo "==================================================="
    echo " Infrastructure Setup Complete"
    echo "==================================================="
    echo "  Project ID:   $PROJECT_ID"
    echo "  BQ Dataset:   $PROJECT_ID.$DATASET_ID"
    echo "  BQ Connection:  $CONNECTION_NAME"
    echo "  AI Model:     clinical_knowledge_integrity"
    echo ""
    echo "---------------------------------------------------"
    echo "NEXT STEP: You are now ready to load the data!"
    echo "==> Open and execute the 'python data_loader.py --project-id $PROJECT_ID"
    echo "---------------------------------------------------"
fi