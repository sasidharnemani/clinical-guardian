#!/usr/bin/env python3
"""
Clinical Guardian - Data Loader
Loads CSV data into BigQuery tables and uploads documents to Cloud Storage
"""

import os
import sys
import pandas as pd
from google.cloud import bigquery
from google.cloud import storage
import uuid
from datetime import datetime
import argparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ClinicalDataLoader:
    def __init__(self, project_id, dataset_id, bucket_name):
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.bucket_name = bucket_name
        self.bq_client = bigquery.Client(project=project_id)
        self.storage_client = storage.Client(project=project_id)
        
    def load_ground_truth_data(self, data_folder):
        """Load ground truth CSV data into BigQuery"""
        logger.info("Loading ground truth data...")
        
        # Look for ground truth CSV files
        ground_truth_files = []
        for file in os.listdir(data_folder):
            if file.startswith('clinical_ground_truth') and file.endswith('.csv'):
                ground_truth_files.append(os.path.join(data_folder, file))
        
        if not ground_truth_files:
            logger.warning("No ground truth CSV files found")
            return
        
        # Use the most recent file
        latest_file = max(ground_truth_files, key=os.path.getctime)
        logger.info(f"Loading from: {latest_file}")
        
        try:
            # Read CSV
            df = pd.read_csv(latest_file)
            logger.info(f"Read {len(df)} rows from ground truth data")
            
            # Add ID column if missing
            if 'id' not in df.columns:
                df['id'] = [str(uuid.uuid4()) for _ in range(len(df))]
            
            # Ensure date columns are properly formatted
            date_columns = ['fda_approval_date', 'update_date', 'compliance_deadline']
            for col in date_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce').dt.date
            
            # Add created_at timestamp
            df['created_at'] = datetime.now()
            
            # Insert into BigQuery
            table_id = f"{self.project_id}.{self.dataset_id}.ground_truth_master"
            job_config = bigquery.LoadJobConfig(
                write_disposition="WRITE_TRUNCATE",  # Replace existing data
                autodetect=True
            )
            
            job = self.bq_client.load_table_from_dataframe(df, table_id, job_config=job_config)
            job.result()  # Wait for completion
            
            logger.info(f"Successfully loaded {len(df)} rows into ground_truth_master table")
            
        except Exception as e:
            logger.error(f"Error loading ground truth data: {e}")
    
    def load_adverse_events_data(self, data_folder):
        """Load FDA adverse events data into BigQuery"""
        logger.info("Loading FDA adverse events data...")
        
        # Look for drug event CSV files
        adverse_event_files = []
        for file in os.listdir(data_folder):
            if file.startswith('drug-event') and file.endswith('.csv'):
                adverse_event_files.append(os.path.join(data_folder, file))
        
        if not adverse_event_files:
            logger.warning("No adverse event CSV files found")
            return
        
        # Process each file and combine
        all_events = []
        for file_path in adverse_event_files:
            try:
                df = pd.read_csv(file_path)
                logger.info(f"Read {len(df)} rows from {os.path.basename(file_path)}")
                all_events.append(df)
            except Exception as e:
                logger.error(f"Error reading {file_path}: {e}")
        
        if not all_events:
            return
        
        # Combine all adverse events
        combined_df = pd.concat(all_events, ignore_index=True)
        
        # Sample down to manageable size for demo (keep most recent 1000 records)
        if len(combined_df) > 1000:
            combined_df = combined_df.sample(n=1000, random_state=42)
            logger.info(f"Sampled down to {len(combined_df)} rows for demo")
        
        # Add processing metadata
        for col in combined_df.columns:
            if combined_df[col].dtype == 'object':
                combined_df[col] = combined_df[col].astype(str)


        combined_df['processed_at'] = datetime.now()
        combined_df['source_file'] = 'fda_adverse_events'
        
        try:
            # Create or update adverse events table
            table_id = f"{self.project_id}.{self.dataset_id}.fda_adverse_events"
            job_config = bigquery.LoadJobConfig(
                write_disposition="WRITE_TRUNCATE",
                autodetect=True
            )
            
            job = self.bq_client.load_table_from_dataframe(combined_df, table_id, job_config=job_config)
            job.result()
            
            logger.info(f"Successfully loaded {len(combined_df)} adverse events")
            
        except Exception as e:
            logger.error(f"Error loading adverse events: {e}")
    
    def load_recalls_data(self, data_folder):
        """Load FDA recalls data into BigQuery"""
        logger.info("Loading FDA recalls data...")
        
        recalls_file = os.path.join(data_folder, 'Recalls.csv')
        if not os.path.exists(recalls_file):
            logger.warning("Recalls.csv not found")
            return
        
        try:
            df = pd.read_csv(recalls_file)
            logger.info(f"Read {len(df)} rows from Recalls.csv")
            
            # Add processing metadata
            df['processed_at'] = datetime.now()
            
            # Insert into BigQuery
            table_id = f"{self.project_id}.{self.dataset_id}.fda_recalls"
            job_config = bigquery.LoadJobConfig(
                write_disposition="WRITE_TRUNCATE",
                autodetect=True
            )
            
            job = self.bq_client.load_table_from_dataframe(df, table_id, job_config=job_config)
            job.result()
            
            logger.info(f"Successfully loaded {len(df)} recalls")
            
        except Exception as e:
            logger.error(f"Error loading recalls data: {e}")
    
    def upload_hospital_documents(self, data_folder):
        """Upload hospital documents to Cloud Storage"""
        logger.info("Uploading hospital documents...")
        
        uploads_folder = os.path.join(data_folder, 'clinical_document_corpus')
        if not os.path.exists(uploads_folder):
            logger.warning("clinical_document_corpus folder not found in data directory")
            return
        
        try:
            bucket = self.storage_client.bucket(self.bucket_name)
            uploaded_count = 0
            
            for root, dirs, files in os.walk(uploads_folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    # Skip hidden files and system files
                    if file.startswith('.') or file.endswith('.tmp'):
                        continue
                    
                    # Create blob name (preserve folder structure)
                    relative_path = os.path.relpath(file_path, uploads_folder)
                    blob_name = f"hospital_documents/{relative_path}"
                    
                    try:
                        blob = bucket.blob(blob_name)
                        blob.upload_from_filename(file_path)
                        uploaded_count += 1
                        logger.info(f"Uploaded: {blob_name}")
                        
                    except Exception as e:
                        logger.error(f"Error uploading {file}: {e}")
            
            logger.info(f"Successfully uploaded {uploaded_count} documents")
            
        except Exception as e:
            logger.error(f"Error accessing bucket: {e}")
    
    def create_document_metadata(self, data_folder):
        """Create metadata entries for uploaded documents"""
        logger.info("Creating document metadata...")
        
        uploads_folder = os.path.join(data_folder, 'uploads')
        if not os.path.exists(uploads_folder):
            return
        
        document_records = []
        
        for root, dirs, files in os.walk(uploads_folder):
            for file in files:
                if file.startswith('.') or file.endswith('.tmp'):
                    continue
                
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, uploads_folder)
                
                # Determine document type
                file_ext = os.path.splitext(file)[1].lower()
                doc_type = self.determine_document_type(file)
                
                record = {
                    'document_id': str(uuid.uuid4()),
                    'document_name': file,
                    'document_uri': f"gs://{self.bucket_name}/hospital_documents/{relative_path}",
                    'document_type': doc_type,
                    'source_format': file_ext.replace('.', '').upper() if file_ext else 'UNKNOWN',
                    'upload_timestamp': datetime.now(),
                    'processing_status': 'UPLOADED',
                    'file_size_bytes': os.path.getsize(file_path)
                }
                
                document_records.append(record)
        
        if document_records:
            try:
                df = pd.DataFrame(document_records)
                table_id = f"{self.project_id}.{self.dataset_id}.knowledge_base_master"
                
                job_config = bigquery.LoadJobConfig(
                    write_disposition="WRITE_APPEND",
                    autodetect=True
                )
                
                job = self.bq_client.load_table_from_dataframe(df, table_id, job_config=job_config)
                job.result()
                
                logger.info(f"Created metadata for {len(document_records)} documents")
                
            except Exception as e:
                logger.error(f"Error creating document metadata: {e}")
    
    def determine_document_type(self, filename):
        """Determine document type from filename"""
        filename_lower = filename.lower()
        
        if any(keyword in filename_lower for keyword in ['protocol', 'sop']):
            return 'CLINICAL_PROTOCOL'
        elif any(keyword in filename_lower for keyword in ['memo', 'training']):
            return 'TRAINING_MATERIAL'
        elif any(keyword in filename_lower for keyword in ['manual', 'device']):
            return 'DEVICE_MANUAL'
        elif any(keyword in filename_lower for keyword in ['guideline', 'guidance']):
            return 'CLINICAL_GUIDELINE'
        else:
            return 'GENERAL_CLINICAL'

    def load_fda_statements(self, data_folder):
        """Load FDA public statements data into BigQuery"""
        logger.info("Loading FDA public statements...")
    
        statements_file = os.path.join(data_folder, 'FDA_Stmts.csv')
        if not os.path.exists(statements_file):
            logger.warning("FDA_Stmts.csv not found")
            return
    
        try:
            df = pd.read_csv(statements_file)
            logger.info(f"Read {len(df)} rows from FDA_Stmts.csv")
        
            # Clean and standardize column names
            df.columns = df.columns.str.strip()
        
            # Add processing metadata
            df['processed_at'] = datetime.now()
            df['source_file'] = 'FDA_Stmts'
        
            # Parse dates if needed
            if 'Date' in df.columns:
                df['statement_date'] = pd.to_datetime(df['Date'], errors='coerce').dt.date
        
            # Insert into BigQuery
            table_id = f"{self.project_id}.{self.dataset_id}.fda_public_statements"
            job_config = bigquery.LoadJobConfig(
                write_disposition="WRITE_TRUNCATE",
                autodetect=True
            )
        
            job = self.bq_client.load_table_from_dataframe(df, table_id, job_config=job_config)
            job.result()
        
            logger.info(f"Successfully loaded {len(df)} FDA public statements")
        
        except Exception as e:
            logger.error(f"Error loading FDA public statements: {e}")    
    
    def load_fda_safety_communications(self, data_folder):
        """Load FDA safety communications data into BigQuery"""
        logger.info("Loading FDA safety communications...")
    
        safety_file = os.path.join(data_folder, 'fda_safety.csv')
        if not os.path.exists(safety_file):
            logger.warning("fda_safety.csv not found")
            return
    
        try:
            df = pd.read_csv(safety_file)
            logger.info(f"Read {len(df)} rows from fda_safety.csv")
        
            # Clean and standardize column names
            df.columns = df.columns.str.strip()
        
            # Add processing metadata
            df['processed_at'] = datetime.now()
            df['source_file'] = 'fda_safety'
        
            # Parse dates if needed
            if 'Date' in df.columns:
                df['alert_date'] = pd.to_datetime(df['Date'], errors='coerce').dt.date
        
            # Insert into BigQuery
            table_id = f"{self.project_id}.{self.dataset_id}.fda_safety_communications"
            job_config = bigquery.LoadJobConfig(
                write_disposition="WRITE_TRUNCATE",
                autodetect=True
            )
        
            job = self.bq_client.load_table_from_dataframe(df, table_id, job_config=job_config)
            job.result()
        
            logger.info(f"Successfully loaded {len(df)} FDA safety communications")
        
        except Exception as e:
            logger.error(f"Error loading FDA safety communications: {e}")

    def load_fda_drug_alerts(self, data_folder):
        """Load FDA drug alerts data into BigQuery"""
        logger.info("Loading FDA drug alerts...")
    
        alerts_file = os.path.join(data_folder, 'DrugAlerts_FDA.csv')
        if not os.path.exists(alerts_file):
            logger.warning("DrugAlerts_FDA.csv not found")
            return
    
        try:
            df = pd.read_csv(alerts_file)
            logger.info(f"Read {len(df)} rows from DrugAlerts_FDA.csv")
        
            # Clean and standardize column names
            df.columns = df.columns.str.strip()
        
            # Add processing metadata
            df['processed_at'] = datetime.now()
            df['source_file'] = 'DrugAlerts_FDA'
        
            # Parse dates if needed
            if 'Date' in df.columns:
                df['alert_date'] = pd.to_datetime(df['Date'], errors='coerce').dt.date
        
            # Insert into BigQuery
            table_id = f"{self.project_id}.{self.dataset_id}.fda_drug_alerts"
            job_config = bigquery.LoadJobConfig(
                write_disposition="WRITE_TRUNCATE",
                autodetect=True
            )
        
            job = self.bq_client.load_table_from_dataframe(df, table_id, job_config=job_config)
            job.result()
        
            logger.info(f"Successfully loaded {len(df)} FDA drug alerts")
        
        except Exception as e:
            logger.error(f"Error loading FDA drug alerts: {e}")


    def run_full_load(self, data_folder):
        """Run complete data loading process"""
        logger.info(f"Starting data load from: {data_folder}")
        
        # Validate data folder exists
        if not os.path.exists(data_folder):
            logger.error(f"Data folder not found: {data_folder}")
            return False
        
        try:
            # Load all data types
            self.load_ground_truth_data(data_folder)
            self.load_adverse_events_data(data_folder)
            self.load_recalls_data(data_folder)
            
            # Load new FDA data sources
            self.load_fda_safety_communications(data_folder)
            self.load_fda_drug_alerts(data_folder)
            self.load_fda_statements(data_folder)
            
            # Upload documents and create metadata
            self.upload_hospital_documents(data_folder)
            self.create_document_metadata(data_folder)
            
            logger.info("Data loading completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error during data loading: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description="Load clinical data into BigQuery and Cloud Storage")
    parser.add_argument("--project-id", required=True, help="Google Cloud Project ID")
    parser.add_argument("--dataset-id", default="clinical_knowledge_integrity", help="BigQuery dataset ID")
    parser.add_argument("--bucket-name", help="Cloud Storage bucket name (defaults to PROJECT_ID-clinical-guardian)")
    parser.add_argument("--data-folder", default="data", help="Folder containing data files")
    
    args = parser.parse_args()
    
    # Set default bucket name if not provided
    if not args.bucket_name:
        args.bucket_name = f"{args.project_id}-clinical-guardian"
    
    # Initialize loader
    loader = ClinicalDataLoader(args.project_id, args.dataset_id, args.bucket_name)
    
    # Run the loading process
    success = loader.run_full_load(args.data_folder)
    
    if success:
        logger.info("All data loaded successfully")
        sys.exit(0)
    else:
        logger.error("Data loading failed")
        sys.exit(1)

if __name__ == "__main__":
    main()