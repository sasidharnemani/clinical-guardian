# Clinical Guardian: AI-Powered Healthcare Knowledge Integrity

An automated platform using Google BigQuery's native AI capabilities to analyze and manage critical healthcare knowledge. It addresses the significant challenge of keeping thousands of clinical documents updated in response to new regulatory safety alerts.

This system transforms a months-long manual review process into an automated analysis that completes in minutes, directly reducing patient risk and ensuring regulatory compliance.

## The Problem: The Knowledge Management Gap

Healthcare organizations maintain thousands of clinical protocols and training documents. When a regulator like the FDA issues a critical safety alert, identifying every affected document is a slow, manual, and error-prone process.

-   **High Risk:** This delay, often lasting **6-8 months**, exposes patients to care based on outdated information.
-   **High Cost:** Medical errors stemming from these knowledge gaps cost the healthcare industry over **$20 billion annually**.

Clinical Guardian is designed to close this gap.

## The Solution: Automated Clinical Intelligence

Clinical Guardian automates this process by ingesting regulatory alerts and using a core of three coordinated AI functions within BigQuery to provide immediate, actionable intelligence.

1.  **Clinical Briefing** (`ML.GENERATE_TEXT`): Generates an expert-level summary of the clinical risk and its implications.
2.  **Financial Impact** (`AI.GENERATE_DOUBLE`): Calculates the estimated financial liability of non-compliance, turning abstract risk into a concrete metric.
3.  **Action Plan** (`AI.GENERATE_TABLE`): Produces a structured, department-specific action plan for a coordinated response.

This approach reduces the alert-to-action timeline from months to minutes.

## Architecture

The platform ingests data from multiple FDA sources, processes it using the AI functions native to BigQuery, and produces structured intelligence ready for review and action.

```
FDA Data Streams → BigQuery Tables → BigQuery AI → Actionable Intelligence
├── Safety Communications      ┐
├── Drug Development Alerts    ├→ Core AI Functions
├── Public Health Statements   ┘    ↓
├── Adverse Event Reports           - Clinical Briefing
├── Device Recalls                  - Financial Impact
└── Ground Truth Scenarios          - Action Plan
```

## Getting Started

Follow these steps to deploy and run the Clinical Guardian platform.

### Prerequisites

-   A Google Cloud Project with an active billing account.
-   The `gcloud` CLI installed and authenticated (`gcloud auth login`).
-   Python 3.8+ and `pip`.

### Step 1: Clone and Configure

First, clone the repository and set up your environment variables.

```bash
# Clone the repository
git clone https://github.com/your-username/clinical-guardian.git
cd clinical-guardian

# Set your Google Cloud Project ID
export PROJECT_ID="your-gcp-project-id"

# Configure the gcloud CLI to use your project
gcloud config set project $PROJECT_ID
```

### Step 2: Deploy Infrastructure

Run the setup script to create the necessary Google Cloud resources. This will create a BigQuery dataset, a connection to Vertex AI, and the AI model used for analysis.

```bash
# Make the script executable
chmod +x infraSetup.sh

# Run the script with your Project ID
./infraSetup.sh $PROJECT_ID
```

### Step 3: Load Data

Run the data loader script to populate the BigQuery tables with the provided FDA data sources.

```bash
# Install Python dependencies
pip install -r requirements.txt

# Run the data loader
python dataLoader.py --project-id $PROJECT_ID
```

### Step 4: Run the Demonstration

The primary demonstration is contained within a Jupyter Notebook. Launch the notebook to run the end-to-end analysis.

```bash
# Launch Jupyter Notebook
jupyter notebook Clinical_KDD.ipynb
```
Inside the notebook, execute the cells in order to see the "Trinity of Intelligence" in action on a sample clinical scenario.

## Project Structure

```
clinical-guardian/
├── infraSetup.sh           # Infrastructure deployment script
├── dataLoader.py          # Data loading and processing script
├── Clinical_KDD.ipynb      # Main demonstration notebook
├── requirements.txt        # Python dependencies
├── data/                   # Directory for all raw data sources
└── README.md               # This file
```

## Core AI Functions

Clinical Guardian is built on three key BigQuery AI functions:

#### Clinical Risk Assessment (`ML.GENERATE_TEXT`)
```sql
SELECT ML.GENERATE_TEXT(
  MODEL `project.dataset.clinical_knowledge_integrity`,
  (SELECT "Provide a clinical risk summary for a new warfarin alert...")
)
```

#### Financial Impact Calculation (`AI.GENERATE_DOUBLE`)
```sql
SELECT AI.GENERATE_DOUBLE(
  (SELECT "Calculate financial liability for failing to update warfarin protocols..."),
  connection_id => '...'
).result
```

#### Action Plan Generation (`AI.GENERATE_TABLE`)```sql
SELECT * FROM AI.GENERATE_TABLE(
  MODEL `project.dataset.clinical_knowledge_integrity`,
  (SELECT "Generate a departmental action plan for the warfarin alert..."),
  STRUCT('department STRING, priority STRING' AS output_schema)
)
```

## Contributing

Contributions are welcome. Please fork the repository and create a pull request with your changes.

1.  Fork the repository.
2.  Create your feature branch (`git checkout -b feature/NewFeature`).
3.  Commit your changes (`git commit -m 'Add some NewFeature'`).
4.  Push to the branch (`git push origin feature/NewFeature`).
5.  Open a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
