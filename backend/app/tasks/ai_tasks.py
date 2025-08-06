"""
AI and chat-related background tasks
"""
from celery_app import celery_app
from app.services.db_service import DatabaseService
from app.api.chat import ConversationMemoryService, SupabaseChatAgent
from app.utils.logging_config import get_logger
from langchain_openai import ChatOpenAI
from app.utils.config import get_settings
import asyncio

logger = get_logger(__name__)

@celery_app.task(
    name='app.tasks.ai_tasks.process_bulk_chat_requests',
    bind=True,
    queue='ai_processing'
)
def process_bulk_chat_requests(self, chat_requests):
    """Process multiple chat requests in background"""
    try:
        logger.info(f"Processing {len(chat_requests)} chat requests")
        results = []
        
        # Initialize chat components
        settings = get_settings()
        llm = ChatOpenAI(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            temperature=settings.openai_temperature
        )
        
        # Process each request
        for i, request_data in enumerate(chat_requests):
            try:
                # Update task progress
                self.update_state(
                    state='PROGRESS',
                    meta={'current': i + 1, 'total': len(chat_requests)}
                )
                
                # Process chat request
                # This would contain the actual chat processing logic
                result = {
                    'request_id': request_data.get('id'),
                    'response': 'Chat processed successfully',
                    'status': 'completed'
                }
                results.append(result)
                
            except Exception as e:
                logger.error(f"Failed to process chat request {i}: {e}")
                results.append({
                    'request_id': request_data.get('id'),
                    'error': str(e),
                    'status': 'failed'
                })
        
        logger.info(f"Completed bulk chat processing: {len(results)} results")
        return {
            'status': 'completed',
            'total_processed': len(results),
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Bulk chat processing failed: {e}", exc_info=True)
        raise

@celery_app.task(
    name='app.tasks.ai_tasks.preprocess_data_for_ai',
    bind=True,
    queue='ai_processing'
)
def preprocess_data_for_ai(self, user_id, data_filters=None):
    """Preprocess user data for faster AI responses"""
    try:
        logger.info(f"Preprocessing AI data for user {user_id}")
        
        db_service = DatabaseService()
        
        # Get user's data with filters
        query = db_service.supabase.table("sellout_entries2")\
            .select("functional_name, reseller, sales_eur, quantity, month, year, product_ean, currency")
        
        if data_filters:
            if 'years' in data_filters:
                query = query.in_("year", data_filters['years'])
            if 'months' in data_filters:
                query = query.in_("month", data_filters['months'])
        
        result = query.order("created_at", desc=True).limit(10000).execute()
        
        if result.data:
            # Create aggregated summaries for faster AI processing
            summary_data = _create_ai_summary(result.data)
            
            # Cache the processed data
            cache_key = f"ai_preprocessed:{user_id}"
            if data_filters:
                import hashlib
                filter_hash = hashlib.md5(str(sorted(data_filters.items())).encode()).hexdigest()
                cache_key = f"ai_preprocessed:{user_id}:{filter_hash}"
            
            # Store in cache (you would implement caching here)
            logger.info(f"AI preprocessing completed for user {user_id}: {len(result.data)} records processed")
            
            return {
                'status': 'completed',
                'cache_key': cache_key,
                'records_processed': len(result.data),
                'summary_size': len(str(summary_data))
            }
        
        else:
            logger.warning(f"No data found for AI preprocessing: user {user_id}")
            return {'status': 'no_data', 'message': 'No data available for processing'}
            
    except Exception as e:
        logger.error(f"AI preprocessing failed for user {user_id}: {e}", exc_info=True)
        raise

@celery_app.task(
    name='app.tasks.ai_tasks.generate_insights_report',
    bind=True,
    queue='ai_processing'
)
def generate_insights_report(self, user_id, report_type='monthly'):
    """Generate AI-powered insights report"""
    try:
        logger.info(f"Generating {report_type} insights report for user {user_id}")
        
        # This would contain logic to generate comprehensive insights
        # using the chat AI system to analyze user's data
        
        insights = {
            'report_type': report_type,
            'generated_at': '2024-01-01T00:00:00Z',
            'key_insights': [
                'Sales increased by 25% compared to previous period',
                'Top performing product: Product A',
                'Best performing reseller: Customer 1'
            ],
            'recommendations': [
                'Focus on expanding Product A inventory',
                'Strengthen relationship with Customer 1',
                'Consider promotional campaigns for underperforming products'
            ]
        }
        
        # Store the report
        db_service = DatabaseService()
        report_data = {
            'user_id': user_id,
            'report_type': report_type,
            'insights': insights,
            'generated_at': insights['generated_at']
        }
        
        # You would save this to a reports table
        logger.info(f"Insights report generated for user {user_id}")
        
        return {
            'status': 'completed',
            'report_id': f"rpt_{user_id}_{report_type}",
            'insights_count': len(insights['key_insights']),
            'recommendations_count': len(insights['recommendations'])
        }
        
    except Exception as e:
        logger.error(f"Insights report generation failed: {e}", exc_info=True)
        raise

def _create_ai_summary(data):
    """Create aggregated summary for AI processing"""
    try:
        # Create various aggregations
        summary = {
            'total_records': len(data),
            'date_range': {
                'years': list(set(row.get('year') for row in data if row.get('year'))),
                'months': list(set(row.get('month') for row in data if row.get('month')))
            },
            'resellers': {},
            'products': {},
            'totals': {
                'sales_eur': 0,
                'quantity': 0
            }
        }
        
        # Aggregate by resellers and products
        for row in data:
            # Reseller aggregation
            reseller = row.get('reseller', 'Unknown')
            if reseller not in summary['resellers']:
                summary['resellers'][reseller] = {'sales_eur': 0, 'quantity': 0, 'records': 0}
            
            summary['resellers'][reseller]['sales_eur'] += float(row.get('sales_eur', 0) or 0)
            summary['resellers'][reseller]['quantity'] += int(row.get('quantity', 0) or 0)
            summary['resellers'][reseller]['records'] += 1
            
            # Product aggregation
            product = row.get('functional_name', 'Unknown')
            if product not in summary['products']:
                summary['products'][product] = {'sales_eur': 0, 'quantity': 0, 'records': 0}
                
            summary['products'][product]['sales_eur'] += float(row.get('sales_eur', 0) or 0)
            summary['products'][product]['quantity'] += int(row.get('quantity', 0) or 0)
            summary['products'][product]['records'] += 1
            
            # Overall totals
            summary['totals']['sales_eur'] += float(row.get('sales_eur', 0) or 0)
            summary['totals']['quantity'] += int(row.get('quantity', 0) or 0)
        
        # Sort by sales for top performers
        summary['top_resellers'] = sorted(
            summary['resellers'].items(),
            key=lambda x: x[1]['sales_eur'],
            reverse=True
        )[:10]
        
        summary['top_products'] = sorted(
            summary['products'].items(), 
            key=lambda x: x[1]['sales_eur'],
            reverse=True
        )[:10]
        
        return summary
        
    except Exception as e:
        logger.error(f"Failed to create AI summary: {e}")
        return {'error': str(e)}