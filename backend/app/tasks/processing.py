"""
File processing and data cleaning background tasks
"""
from celery_app import celery_app
from app.services.db_service import DatabaseService
from app.services.cleaning_service import CleaningService
from app.utils.logging_config import get_logger
from app.models.upload import UploadStatus, ProcessingStatus
import pandas as pd
import os
import time

logger = get_logger(__name__)

@celery_app.task(
    name='app.tasks.processing.process_uploaded_file',
    bind=True,
    queue='file_processing'
)
def process_uploaded_file(self, upload_id, user_id, file_path):
    """Process uploaded Excel file in background"""
    try:
        logger.info(f"Starting file processing for upload {upload_id}")
        
        # Update task progress
        self.update_state(state='PROGRESS', meta={'stage': 'initializing', 'progress': 0})
        
        # Initialize services
        db_service = DatabaseService()
        cleaning_service = CleaningService()
        
        # Update upload status
        await db_service.update_upload_status(
            upload_id, 
            UploadStatus.PROCESSING,
            processing_status=ProcessingStatus.READING_FILE
        )
        
        # Read the file
        self.update_state(state='PROGRESS', meta={'stage': 'reading_file', 'progress': 10})
        
        try:
            if file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path)
            elif file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_path}")
                
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            await db_service.update_upload_status(
                upload_id, 
                UploadStatus.FAILED,
                error_message=f"Failed to read file: {str(e)}"
            )
            raise
        
        # Validate file structure
        self.update_state(state='PROGRESS', meta={'stage': 'validating', 'progress': 20})
        
        required_columns = ['functional_name', 'reseller', 'sales_eur', 'quantity']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            error_msg = f"Missing required columns: {missing_columns}"
            logger.error(error_msg)
            await db_service.update_upload_status(
                upload_id,
                UploadStatus.FAILED,
                error_message=error_msg
            )
            raise ValueError(error_msg)
        
        # Clean and process data
        self.update_state(state='PROGRESS', meta={'stage': 'cleaning', 'progress': 30})
        
        await db_service.update_upload_status(
            upload_id,
            UploadStatus.PROCESSING,
            processing_status=ProcessingStatus.CLEANING_DATA
        )
        
        # Apply data cleaning
        cleaned_df = cleaning_service.clean_dataframe(df)
        
        # Batch process data in chunks
        self.update_state(state='PROGRESS', meta={'stage': 'saving', 'progress': 50})
        
        chunk_size = 1000
        total_chunks = len(cleaned_df) // chunk_size + (1 if len(cleaned_df) % chunk_size else 0)
        
        await db_service.update_upload_status(
            upload_id,
            UploadStatus.PROCESSING,
            processing_status=ProcessingStatus.SAVING_TO_DATABASE
        )
        
        processed_records = 0
        
        for i, chunk_start in enumerate(range(0, len(cleaned_df), chunk_size)):
            chunk_end = min(chunk_start + chunk_size, len(cleaned_df))
            chunk = cleaned_df[chunk_start:chunk_end]
            
            # Process chunk
            chunk_records = []
            for _, row in chunk.iterrows():
                record = {
                    'upload_id': upload_id,
                    'functional_name': row.get('functional_name'),
                    'reseller': row.get('reseller'),
                    'sales_eur': float(row.get('sales_eur', 0)),
                    'quantity': int(row.get('quantity', 0)),
                    'month': int(row.get('month', 1)),
                    'year': int(row.get('year', 2024)),
                    'product_ean': row.get('product_ean'),
                    'currency': row.get('currency', 'EUR')
                }
                chunk_records.append(record)
            
            # Save chunk to database
            try:
                db_service.supabase.table("sellout_entries2").insert(chunk_records).execute()
                processed_records += len(chunk_records)
                
                # Update progress
                progress = 50 + int(((i + 1) / total_chunks) * 40)
                self.update_state(
                    state='PROGRESS', 
                    meta={
                        'stage': 'saving', 
                        'progress': progress,
                        'records_processed': processed_records,
                        'total_records': len(cleaned_df)
                    }
                )
                
            except Exception as e:
                logger.error(f"Failed to save chunk {i}: {e}")
                await db_service.update_upload_status(
                    upload_id,
                    UploadStatus.FAILED,
                    error_message=f"Failed to save data: {str(e)}"
                )
                raise
        
        # Finalize processing
        self.update_state(state='PROGRESS', meta={'stage': 'finalizing', 'progress': 90})
        
        # Update upload status to completed
        await db_service.update_upload_status(
            upload_id,
            UploadStatus.COMPLETED,
            processing_status=ProcessingStatus.COMPLETED,
            processed_records=processed_records
        )
        
        # Clean up temporary file
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.warning(f"Failed to clean up temporary file {file_path}: {e}")
        
        # Complete
        self.update_state(state='SUCCESS', meta={'stage': 'completed', 'progress': 100})
        
        logger.info(f"File processing completed for upload {upload_id}: {processed_records} records")
        
        return {
            'status': 'completed',
            'upload_id': upload_id,
            'records_processed': processed_records,
            'total_records': len(cleaned_df)
        }
        
    except Exception as e:
        logger.error(f"File processing failed for upload {upload_id}: {e}", exc_info=True)
        
        # Update upload status to failed
        try:
            await db_service.update_upload_status(
                upload_id,
                UploadStatus.FAILED,
                error_message=str(e)
            )
        except Exception as update_error:
            logger.error(f"Failed to update upload status: {update_error}")
        
        raise

@celery_app.task(
    name='app.tasks.processing.validate_data_integrity',
    bind=True,
    queue='file_processing'
)
def validate_data_integrity(self, upload_id):
    """Validate data integrity after upload"""
    try:
        logger.info(f"Validating data integrity for upload {upload_id}")
        
        db_service = DatabaseService()
        
        # Get upload info
        upload_info = db_service.supabase.table("uploads").select("*").eq("id", upload_id).execute()
        
        if not upload_info.data:
            raise ValueError(f"Upload {upload_id} not found")
        
        # Get all records for this upload
        records = db_service.supabase.table("sellout_entries2")\
            .select("*")\
            .eq("upload_id", upload_id)\
            .execute()
        
        if not records.data:
            raise ValueError(f"No records found for upload {upload_id}")
        
        validation_results = {
            'total_records': len(records.data),
            'issues': [],
            'warnings': []
        }
        
        # Validate data quality
        for i, record in enumerate(records.data):
            # Check for negative sales
            if record.get('sales_eur', 0) < 0:
                validation_results['warnings'].append(f"Record {i}: Negative sales value")
            
            # Check for missing essential data
            if not record.get('functional_name'):
                validation_results['issues'].append(f"Record {i}: Missing product name")
            
            if not record.get('reseller'):
                validation_results['issues'].append(f"Record {i}: Missing reseller")
            
            # Check for unrealistic quantities
            quantity = record.get('quantity', 0)
            if quantity > 100000:  # Arbitrary large number check
                validation_results['warnings'].append(f"Record {i}: Very large quantity ({quantity})")
        
        # Store validation results
        validation_summary = {
            'upload_id': upload_id,
            'total_records': validation_results['total_records'],
            'issues_count': len(validation_results['issues']),
            'warnings_count': len(validation_results['warnings']),
            'validation_passed': len(validation_results['issues']) == 0
        }
        
        logger.info(f"Data validation completed for upload {upload_id}: {validation_summary}")
        
        return validation_results
        
    except Exception as e:
        logger.error(f"Data validation failed for upload {upload_id}: {e}", exc_info=True)
        raise

@celery_app.task(
    name='app.tasks.processing.generate_processing_report',
    bind=True,
    queue='file_processing'
)
def generate_processing_report(self, upload_id):
    """Generate comprehensive processing report"""
    try:
        logger.info(f"Generating processing report for upload {upload_id}")
        
        db_service = DatabaseService()
        
        # Get upload and processing data
        upload_data = db_service.supabase.table("uploads").select("*").eq("id", upload_id).execute()
        records_data = db_service.supabase.table("sellout_entries2")\
            .select("*")\
            .eq("upload_id", upload_id)\
            .execute()
        
        if not upload_data.data:
            raise ValueError(f"Upload {upload_id} not found")
        
        upload_info = upload_data.data[0]
        records = records_data.data or []
        
        # Generate report
        report = {
            'upload_id': upload_id,
            'filename': upload_info.get('filename'),
            'upload_date': upload_info.get('created_at'),
            'processing_status': upload_info.get('status'),
            'total_records': len(records),
            'file_size_bytes': upload_info.get('file_size'),
            'processing_summary': {
                'resellers_count': len(set(r.get('reseller') for r in records if r.get('reseller'))),
                'products_count': len(set(r.get('functional_name') for r in records if r.get('functional_name'))),
                'total_sales_eur': sum(float(r.get('sales_eur', 0)) for r in records),
                'total_quantity': sum(int(r.get('quantity', 0)) for r in records),
                'date_range': {
                    'years': sorted(set(r.get('year') for r in records if r.get('year'))),
                    'months': sorted(set(r.get('month') for r in records if r.get('month')))
                }
            }
        }
        
        # Store report (you could save this to a reports table)
        logger.info(f"Processing report generated for upload {upload_id}")
        
        return report
        
    except Exception as e:
        logger.error(f"Report generation failed for upload {upload_id}: {e}", exc_info=True)
        raise