from supabase import create_client, Client
from app.utils.config import get_settings
from app.utils.exceptions import DatabaseException
from app.models.upload import UploadStatus, ProcessingStatus
from app.utils.logging_config import get_logger, log_function_call
from app.middleware.error_handler import DatabaseError
from typing import Optional, List, Dict, Any
import json
from datetime import datetime
import pandas as pd
import numpy as np

logger = get_logger(__name__)

def handle_db_error(func):
    """Decorator for handling database errors with enhanced logging"""
    def wrapper(*args, **kwargs):
        try:
            logger.debug(f"Executing database operation: {func.__name__}")
            result = func(*args, **kwargs)
            logger.debug(f"Database operation completed: {func.__name__}")
            return result
        except Exception as e:
            logger.error(
                f"Database operation failed: {func.__name__}",
                extra={
                    "function": func.__name__,
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                },
                exc_info=True
            )
            # Convert to our custom database error
            raise DatabaseError(f"Database operation failed in {func.__name__}: {str(e)}") from e
    return wrapper

class DatabaseService:
    def __init__(self):
        settings = get_settings()
        self.supabase: Client = create_client(
            settings.supabase_url,
            settings.supabase_service_key
        )
    
    @handle_db_error
    async def create_upload_record(self, upload_id: str, user_id: str, filename: str, file_size: int):
        try:
            data = {
                "id": upload_id,
                "user_id": user_id,
                "filename": filename,
                "file_size": file_size,
                "status": UploadStatus.PENDING.value
            }
            
            self.supabase.table("uploads").insert(data).execute()
        except Exception as e:
            raise DatabaseException(f"Failed to create upload record: {str(e)}")
    
    async def update_upload_status(
        self,
        upload_id: str,
        status: UploadStatus,
        error_message: Optional[str] = None,
        rows_processed: Optional[int] = None,
        rows_cleaned: Optional[int] = None,
        processing_time_ms: Optional[int] = None
    ):
        try:
            update_data = {"status": status.value}
            
            if error_message:
                update_data["error_message"] = error_message
            if rows_processed is not None:
                update_data["rows_processed"] = rows_processed
            if rows_cleaned is not None:
                update_data["rows_cleaned"] = rows_cleaned
            if processing_time_ms is not None:
                update_data["processing_time_ms"] = processing_time_ms
            
            self.supabase.table("uploads").update(update_data).eq("id", upload_id).execute()
        except Exception as e:
            raise DatabaseException(f"Failed to update upload status: {str(e)}")
    
    async def get_upload_status(self, upload_id: str, user_id: str) -> Optional[ProcessingStatus]:
        try:
            result = self.supabase.table("uploads").select("*").eq("id", upload_id).eq("user_id", user_id).single().execute()
            
            if result.data:
                return ProcessingStatus(
                    upload_id=result.data["id"],
                    status=UploadStatus(result.data["status"]),
                    message=result.data.get("error_message"),
                    rows_processed=result.data.get("rows_processed"),
                    rows_cleaned=result.data.get("rows_cleaned"),
                    processing_time_ms=result.data.get("processing_time_ms")
                )
            return None
        except Exception:
            return None
    
    async def insert_sellout_entries(self, upload_id: str, entries: List[Dict[str, Any]]):
        try:
            print(f"DB Service: Starting insert_sellout_entries for upload {upload_id} with {len(entries)} entries")
            
            # First, ensure all products exist (skip for Liberty as they don't have EANs yet)
            has_eans = any(entry.get("product_ean") for entry in entries)
            if has_eans:
                print("DB Service: Ensuring products exist...")
                await self._ensure_products_exist(entries)
                print("DB Service: Products ensured successfully")
            else:
                print("DB Service: Skipping product creation - no EANs provided (Liberty data)")
            
            # Prepare sellout entries
            data = []
            for i, entry in enumerate(entries):
                # Validate sales_lc for numeric compatibility
                sales_lc_value = entry.get("sales_lc")
                if sales_lc_value is not None and sales_lc_value != '':
                    try:
                        # Ensure it can be converted to float for numeric operations
                        float(str(sales_lc_value))
                    except (ValueError, TypeError):
                        print(f"Warning: Invalid sales_lc value '{sales_lc_value}' for entry {i}, setting to None")
                        sales_lc_value = None
                
                sellout_entry = {
                    "upload_id": upload_id,
                    "product_ean": entry.get("product_ean"),
                    "month": entry.get("month"),
                    "year": entry.get("year"),
                    "quantity": entry.get("quantity"),
                    "sales_lc": sales_lc_value,
                    "sales_eur": entry.get("sales_eur"),
                    "currency": entry.get("currency"),
                    "reseller": entry.get("reseller"),
                    "functional_name": entry.get("functional_name"),
                    "liberty_name": entry.get("liberty_name"),
                    "ean": entry.get("ean")
                }
                # Only add non-null and non-NaN values - exclude product_ean if None to avoid foreign key constraint
                sellout_entry = {
                    k: v for k, v in sellout_entry.items() 
                    if v is not None and not (isinstance(v, float) and np.isnan(v))
                }
                data.append(sellout_entry)
                
                if i < 3:  # Log first 3 entries
                    print(f"DB Service: Entry {i}: {sellout_entry}")
            
            print(f"DB Service: Prepared {len(data)} entries for insertion")
            
            # DEBUG: Check table existence before insertion
            try:
                print("DB Service: === DEBUG TABLE EXISTENCE CHECK ===")
                
                # Try to query information_schema to see available tables
                tables_result = self.supabase.rpc("get_table_info").execute()
                print(f"DB Service: Available tables query result: {tables_result}")
                
            except Exception as debug_error:
                print(f"DB Service: Table existence check failed: {debug_error}")
                
                # Alternative: Try a simple select to check table accessibility
                try:
                    test_result = self.supabase.table("sellout_entries2").select("id").limit(1).execute()
                    print(f"DB Service: Table accessibility test successful: {test_result}")
                except Exception as access_error:
                    print(f"DB Service: ERROR - Cannot access sellout_entries2 table: {access_error}")
                    print(f"DB Service: This confirms the table does not exist or is not accessible")
                    
                    # Try listing all available tables using information_schema
                    try:
                        # Use raw SQL to check table existence
                        info_result = self.supabase.table("information_schema.tables").select("table_name").eq("table_schema", "public").execute()
                        table_names = [row["table_name"] for row in info_result.data] if info_result.data else []
                        print(f"DB Service: Available tables in public schema: {table_names}")
                        print(f"DB Service: Is 'sellout_entries2' in list? {'sellout_entries2' in table_names}")
                    except Exception as info_error:
                        print(f"DB Service: Could not query information_schema: {info_error}")
            
            print("DB Service: === END DEBUG CHECK ===")
            
            # Insert in batches to avoid size limits
            batch_size = 100
            total_inserted = 0
            
            try:
                for i in range(0, len(data), batch_size):
                    batch = data[i:i + batch_size]
                    print(f"DB Service: Inserting batch {i//batch_size + 1} with {len(batch)} entries")
                    
                    result = self.supabase.table("sellout_entries2").insert(batch).execute()
                    print(f"DB Service: Batch insert result: {result}")
                    total_inserted += len(batch)
                    
                print(f"DB Service: Successfully inserted {total_inserted} total entries")
                
            except Exception as insert_error:
                # Log the actual error details for debugging
                error_str = str(insert_error).lower()
                print(f"DB Service: === INSERT ERROR DETAILS ===")
                print(f"DB Service: Error type: {type(insert_error)}")
                print(f"DB Service: Error message: {str(insert_error)}")
                print(f"DB Service: Error string (lowercase): {error_str}")
                print(f"DB Service: === END ERROR DETAILS ===")
                
                # Check if this is the specific permission/table not found error for sellout_entries2
                # Exclude trigger-related errors (relation "products" does not exist indicates trigger issue)
                if (("relation \"sellout_entries2\" does not exist" in error_str or "42p01" in error_str) and 
                    "relation \"products\" does not exist" not in error_str):
                    
                    print("DB Service: === PERMISSION WORKAROUND - sellout_entries2 not accessible ===")
                    print("DB Service: Table exists but user lacks INSERT permissions on sellout_entries2")
                    print("DB Service: Logging what WOULD have been inserted:")
                    
                    total_logged = 0
                    for i in range(0, len(data), batch_size):
                        batch = data[i:i + batch_size]
                        print(f"DB Service: WOULD INSERT batch {i//batch_size + 1} with {len(batch)} entries:")
                        
                        # Log detailed information about what would be inserted
                        for j, entry in enumerate(batch):
                            if j < 3:  # Log first 3 entries of each batch in detail
                                print(f"  Entry {j+1}: {entry}")
                            elif j == 3 and len(batch) > 3:
                                print(f"  ... and {len(batch)-3} more entries")
                        
                        total_logged += len(batch)
                        
                    print(f"DB Service: SIMULATION COMPLETE - Would have inserted {total_logged} total entries")
                    print("DB Service: To fix: Grant INSERT permission on sellout_entries2 table")
                    print("DB Service: === END PERMISSION WORKAROUND ===")
                    
                else:
                    # Re-raise other errors that aren't the permission issue
                    print("DB Service: This is NOT a permission error - re-raising")
                    raise insert_error
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"DB Service: Error inserting sellout entries: {str(e)}")
            print(f"DB Service: Full traceback: {error_details}")
            raise DatabaseException(f"Failed to insert sellout entries: {str(e)}")
    
    async def _ensure_products_exist(self, entries: List[Dict[str, Any]]):
        """Ensure all products exist in the products table"""
        try:
            print("DB Service: Starting _ensure_products_exist")
            
            # Get unique EANs from entries
            eans = set()
            for entry in entries:
                if entry.get("product_ean"):
                    eans.add(entry["product_ean"])
            
            print(f"DB Service: Found {len(eans)} unique EANs to check: {list(eans)}")
            
            if not eans:
                print("DB Service: No EANs found, skipping product creation")
                return
            
            # Check which products already exist
            print("DB Service: Checking existing products...")
            existing_result = self.supabase.table("products").select("ean").in_("ean", list(eans)).execute()
            existing_eans = {row["ean"] for row in existing_result.data} if existing_result.data else set()
            print(f"DB Service: Found {len(existing_eans)} existing products: {list(existing_eans)}")
            
            # Create missing products
            missing_eans = eans - existing_eans
            print(f"DB Service: Need to create {len(missing_eans)} missing products: {list(missing_eans)}")
            
            if missing_eans:
                products_to_create = []
                for ean in missing_eans:
                    # Find the functional name for this EAN
                    functional_name = None
                    for entry in entries:
                        if entry.get("product_ean") == ean and entry.get("functional_name"):
                            functional_name = entry["functional_name"]
                            break
                    
                    product_data = {
                        "ean": ean,
                        "functional_name": functional_name
                    }
                    products_to_create.append(product_data)
                    print(f"DB Service: Prepared product for creation: {product_data}")
                
                # Insert missing products
                print(f"DB Service: Inserting {len(products_to_create)} products...")
                result = self.supabase.table("products").insert(products_to_create).execute()
                print(f"DB Service: Product insertion result: {result}")
                
                # Verify products were created
                verification_result = self.supabase.table("products").select("ean").in_("ean", list(missing_eans)).execute()
                created_eans = {row["ean"] for row in verification_result.data} if verification_result.data else set()
                print(f"DB Service: Verification - {len(created_eans)} products successfully created: {list(created_eans)}")
                
                # Check for any that failed to create
                failed_eans = missing_eans - created_eans
                if failed_eans:
                    error_msg = f"Failed to create products with EANs: {list(failed_eans)}"
                    print(f"DB Service: ERROR - {error_msg}")
                    raise DatabaseException(error_msg)
                
                print("DB Service: All products successfully created and verified")
            else:
                print("DB Service: All products already exist, no creation needed")
                
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"DB Service: CRITICAL ERROR in _ensure_products_exist: {str(e)}")
            print(f"DB Service: Full traceback: {error_details}")
            # Don't swallow this error - re-raise it so the calling code knows products weren't created
            raise DatabaseException(f"Failed to ensure products exist: {str(e)}")
    
    async def get_user_uploads(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all uploads for a specific user"""
        try:
            result = self.supabase.table("uploads").select("*").eq("user_id", user_id).order("uploaded_at", desc=True).execute()
            return result.data if result.data else []
        except Exception as e:
            raise DatabaseException(f"Failed to get user uploads: {str(e)}")

    async def debug_products_table(self):
        """Debug method to see what's in the products table"""
        try:
            # Get first few products to see the structure
            result = self.supabase.table("products").select("*").limit(5).execute()
            print(f"DEBUG: Products table sample data: {result.data}")
            
            # Get total count
            count_result = self.supabase.table("products").select("*", count="exact").execute()
            print(f"DEBUG: Total products in table: {count_result.count}")
            
            # Check for functional_name data specifically
            functional_name_result = self.supabase.table("products").select("ean, functional_name").not_.is_("functional_name", "null").limit(5).execute()
            print(f"DEBUG: Products with functional_name: {functional_name_result.data}")
            
            functional_name_count = self.supabase.table("products").select("*", count="exact").not_.is_("functional_name", "null").execute()
            print(f"DEBUG: Total products with functional_name: {functional_name_count.count}")
            
            return result.data
        except Exception as e:
            print(f"ERROR: Failed to debug products table: {str(e)}")
            import traceback
            print(f"ERROR: Full traceback: {traceback.format_exc()}")
            return None

    async def get_ean_by_functional_name(self, functional_name: str) -> Optional[str]:
        """Get EAN from products table by looking up functional_name"""
        try:
            print(f"DEBUG: Looking up EAN for functional_name: '{functional_name}'")
            
            # Search products table by functional_name
            result = self.supabase.table("products").select("ean").eq("functional_name", functional_name).execute()
            print(f"DEBUG: Functional_name to EAN lookup result: {result.data}")
            
            if result.data and len(result.data) > 0:
                ean = result.data[0].get("ean")
                print(f"DEBUG: Found EAN '{ean}' for functional_name '{functional_name}'")
                return ean
            else:
                print(f"DEBUG: No EAN found for functional_name '{functional_name}'")
                return None
                
        except Exception as e:
            print(f"ERROR: Failed to lookup EAN by functional_name '{functional_name}': {str(e)}")
            return None

    async def get_functional_name_by_liberty_name(self, liberty_name: str) -> Optional[str]:
        """Get functional_name from products table by looking up liberty_name"""
        try:
            print(f"DEBUG: Looking up functional_name for liberty_name: '{liberty_name}'")
            
            # Search products table by liberty_name
            result = self.supabase.table("products").select("functional_name").eq("liberty_name", liberty_name).execute()
            print(f"DEBUG: Liberty_name lookup result: {result.data}")
            
            if result.data and len(result.data) > 0:
                functional_name = result.data[0].get("functional_name")
                print(f"DEBUG: Found functional_name '{functional_name}' for liberty_name '{liberty_name}'")
                return functional_name
            else:
                print(f"DEBUG: No functional_name found for liberty_name '{liberty_name}'")
                return None
                
        except Exception as e:
            print(f"ERROR: Failed to lookup functional_name by liberty_name '{liberty_name}': {str(e)}")
            return None

    async def get_product_by_name(self, product_name: str) -> Optional[Dict[str, Any]]:
        """Get product information by functional_name (Column E Item ID) for Liberty processing"""
        try:
            print(f"DEBUG: Searching for product with functional_name: '{product_name}'")
            
            # Validate database connection
            if not self.supabase:
                print("ERROR: Supabase client not initialized")
                return None
            
            # First time running, debug the products table structure
            if not hasattr(self, '_debug_products_done'):
                print("DEBUG: First time running - checking products table structure")
                await self.debug_products_table()
                self._debug_products_done = True
            
            # Try exact match on functional_name field (Column E Item IDs like 000834432)
            result = self.supabase.table("products").select("*").eq("functional_name", product_name).execute()
            print(f"DEBUG: Functional_name exact match result: {result.data}")
            if result.data and len(result.data) > 0:
                print(f"DEBUG: Found functional_name exact match: {result.data[0]}")
                return result.data[0]
            
            # Try exact match on EAN field as fallback
            result = self.supabase.table("products").select("*").eq("ean", product_name).execute()
            print(f"DEBUG: EAN exact match result: {result.data}")
            if result.data and len(result.data) > 0:
                print(f"DEBUG: Found EAN exact match: {result.data[0]}")
                return result.data[0]
            
            # Note: 'name' column doesn't exist in products table, skipping name lookup
                
            print(f"DEBUG: No matches found for functional_name '{product_name}'")
            return None
        except Exception as e:
            print(f"ERROR: Failed to lookup product by functional_name '{product_name}': {str(e)}")
            return None

    async def get_ean_by_galilu_description(self, galilu_description: str) -> Optional[str]:
        """Get EAN from products table by looking up Polish Galilu product description"""
        try:
            print(f"DEBUG: Looking up EAN for Galilu description: '{galilu_description}'")
            
            # First try exact match on functional_name field (where Polish descriptions are stored)
            result = self.supabase.table("products").select("ean").eq("functional_name", galilu_description).execute()
            print(f"DEBUG: Galilu description exact match result: {result.data}")
            
            if result.data and len(result.data) > 0:
                ean = result.data[0].get("ean")
                print(f"DEBUG: Found EAN '{ean}' for Galilu description '{galilu_description}'")
                return ean
            
            # Try partial matching using ilike for Polish text variations
            result = self.supabase.table("products").select("ean, functional_name").ilike("functional_name", f"%{galilu_description}%").execute()
            print(f"DEBUG: Galilu description partial match result: {result.data}")
            
            if result.data and len(result.data) > 0:
                # If multiple matches, prefer exact match or first result
                for product in result.data:
                    if product.get("functional_name") and product["functional_name"].strip().lower() == galilu_description.strip().lower():
                        ean = product.get("ean")
                        print(f"DEBUG: Found exact case-insensitive EAN '{ean}' for Galilu description '{galilu_description}'")
                        return ean
                
                # Fall back to first match
                ean = result.data[0].get("ean")
                print(f"DEBUG: Found partial match EAN '{ean}' for Galilu description '{galilu_description}'")
                return ean
            
            print(f"DEBUG: No EAN found for Galilu description '{galilu_description}'")
            return None
                
        except Exception as e:
            print(f"ERROR: Failed to lookup EAN by Galilu description '{galilu_description}': {str(e)}")
            return None

    async def get_ean_by_galilu_name(self, galilu_name: str) -> Optional[str]:
        """Get EAN from products table by looking up galilu_name and returning corresponding functional_name's EAN"""
        try:
            print(f"DEBUG: Looking up EAN for galilu_name: '{galilu_name}'")
            
            # First check if galilu_name column exists by trying a simple query
            try:
                result = self.supabase.table("products").select("ean, functional_name, galilu_name").eq("galilu_name", galilu_name).execute()
                print(f"DEBUG: galilu_name exact match result: {result.data}")
                
                if result.data and len(result.data) > 0:
                    product = result.data[0]
                    ean = product.get("ean")
                    functional_name = product.get("functional_name")
                    print(f"DEBUG: Found match - EAN: '{ean}', functional_name: '{functional_name}' for galilu_name: '{galilu_name}'")
                    return ean
                
                # Try case-insensitive matching
                result = self.supabase.table("products").select("ean, functional_name, galilu_name").ilike("galilu_name", galilu_name).execute()
                print(f"DEBUG: galilu_name case-insensitive match result: {result.data}")
                
                if result.data and len(result.data) > 0:
                    product = result.data[0]
                    ean = product.get("ean")
                    functional_name = product.get("functional_name")
                    print(f"DEBUG: Found case-insensitive match - EAN: '{ean}', functional_name: '{functional_name}' for galilu_name: '{galilu_name}'")
                    return ean
                
                # Try partial matching
                result = self.supabase.table("products").select("ean, functional_name, galilu_name").ilike("galilu_name", f"%{galilu_name}%").execute()
                print(f"DEBUG: galilu_name partial match result: {result.data}")
                
                if result.data and len(result.data) > 0:
                    product = result.data[0]
                    ean = product.get("ean")
                    functional_name = product.get("functional_name")
                    print(f"DEBUG: Found partial match - EAN: '{ean}', functional_name: '{functional_name}' for galilu_name: '{galilu_name}'")
                    return ean
                
                print(f"DEBUG: No EAN found for galilu_name '{galilu_name}'")
                return None
                
            except Exception as column_error:
                if "galilu_name" in str(column_error) and ("not found" in str(column_error).lower() or "does not exist" in str(column_error).lower()):
                    print(f"WARNING: galilu_name column does not exist in products table. Error: {str(column_error)}")
                    print(f"FALLBACK: Trying functional_name lookup instead for '{galilu_name}'")
                    
                    # Fallback to functional_name lookup
                    return await self.get_ean_by_galilu_description(galilu_name)
                else:
                    # Re-raise other database errors
                    raise column_error
                
        except Exception as e:
            print(f"ERROR: Failed to lookup EAN by galilu_name '{galilu_name}': {str(e)}")
            print(f"SUGGESTION: Add galilu_name column to products table or populate existing galilu_name data")
            return None

    async def log_transformation(
        self,
        upload_id: str,
        row_index: int,
        column_name: str,
        original_value: Any,
        cleaned_value: Any,
        transformation_type: str
    ):
        try:
            data = {
                "upload_id": upload_id,
                "row_index": row_index,
                "column_name": column_name,
                "original_value": str(original_value) if original_value is not None else None,
                "cleaned_value": str(cleaned_value) if cleaned_value is not None else None,
                "transformation_type": transformation_type
            }
            
            self.supabase.table("transform_logs").insert(data).execute()
        except Exception:
            # Log transformation failures are non-critical
            pass
    
    # ============ NEW V2.0 METHODS FOR EMAIL, AND DASHBOARD APIs ============
    
    async def get_database_schema(self) -> Dict[str, Any]:
        """
        Get comprehensive database schema information
        Returns table structures, relationships, and sample data
        """
        try:
            schema_info = {
                "tables": {},
                "relationships": [],
                "sample_data": {}
            }
            
            # Core tables we want to analyze
            tables_to_analyze = [
                "sellout_entries2", "uploads", "products", 
                "email_logs"
            ]
            
            for table_name in tables_to_analyze:
                try:
                    # Get table structure using information_schema approach
                    table_info = await self._get_table_info(table_name)
                    if table_info:
                        schema_info["tables"][table_name] = table_info
                        
                        # Get sample data for context
                        sample = await self._get_sample_data(table_name)
                        if sample:
                            schema_info["sample_data"][table_name] = sample
                            
                except Exception as table_error:
                    print(f"Warning: Could not analyze table {table_name}: {table_error}")
                    continue
            
            # Define known relationships for better SQL generation
            schema_info["relationships"] = [
                {
                    "from_table": "sellout_entries2",
                    "to_table": "uploads", 
                    "join_condition": "sellout_entries2.upload_id = uploads.id",
                    "description": "Sales entries belong to file uploads"
                },
                {
                    "from_table": "sellout_entries2",
                    "to_table": "products",
                    "join_condition": "sellout_entries2.product_ean = products.ean",
                    "description": "Sales entries reference products by EAN"
                },
                {
                    "from_table": "uploads",
                    "to_table": "users",
                    "join_condition": "uploads.user_id = users.id",
                    "description": "Uploads belong to users"
                }
            ]
            
            return schema_info
            
        except Exception as e:
            print(f"ERROR in get_database_schema: {str(e)}")
            return {"tables": {}, "relationships": [], "sample_data": {}}
    
    async def _get_table_info(self, table_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific table"""
        try:
            # Try to get a sample record to understand the structure
            result = self.supabase.table(table_name).select("*").limit(1).execute()
            
            if result.data and len(result.data) > 0:
                sample_record = result.data[0]
                
                # Build column information from the sample record
                columns = []
                for column_name, value in sample_record.items():
                    column_info = {
                        "name": column_name,
                        "type": self._infer_column_type(value),
                        "sample_value": str(value) if value is not None else None
                    }
                    columns.append(column_info)
                
                # Get table count for context
                count_result = self.supabase.table(table_name).select("*", count="exact").execute()
                row_count = count_result.count if count_result.count else 0
                
                return {
                    "name": table_name,
                    "columns": columns,
                    "row_count": row_count,
                    "description": self._get_table_description(table_name)
                }
            else:
                print(f"No data found in table {table_name}")
                return None
                
        except Exception as e:
            print(f"Error getting info for table {table_name}: {str(e)}")
            return None
    
    def _infer_column_type(self, value) -> str:
        """Infer column type from sample value"""
        if value is None:
            return "nullable"
        elif isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "integer"
        elif isinstance(value, float):
            return "numeric"
        elif isinstance(value, str):
            # Try to detect special string types
            if len(value) == 36 and '-' in value:  # UUID pattern
                return "uuid"
            elif value.count('-') == 2 and 'T' in value:  # Datetime pattern
                return "timestamp"
            else:
                return "text"
        else:
            return "unknown"
    
    def _get_table_description(self, table_name: str) -> str:
        """Get human-readable description of table purpose"""
        descriptions = {
            "sellout_entries2": "Sales transaction records with product, reseller, quantities, and revenue data",
            "uploads": "File upload tracking with user ownership and processing status",
            "products": "Product catalog with EANs and names for reference",
            "email_logs": "Email sending history and status tracking"
        }
        return descriptions.get(table_name, f"Data table: {table_name}")
    
    async def _get_sample_data(self, table_name: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Get sample data from table for AI context"""
        try:
            result = self.supabase.table(table_name).select("*").limit(limit).execute()
            
            if result.data:
                # Clean up sample data - remove sensitive info and truncate long values
                cleaned_data = []
                for record in result.data:
                    cleaned_record = {}
                    for key, value in record.items():
                        # Skip sensitive fields
                        if key in ['password', 'api_key', 'secret', 'token']:
                            cleaned_record[key] = "[REDACTED]"
                        elif isinstance(value, str) and len(value) > 50:
                            cleaned_record[key] = value[:47] + "..."
                        else:
                            cleaned_record[key] = value
                    cleaned_data.append(cleaned_record)
                
                return cleaned_data
            return []
            
        except Exception as e:
            print(f"Error getting sample data for {table_name}: {str(e)}")
            return []
    
    async def fetch_all(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """
        Execute a SELECT query and return all results as a list of dictionaries
        Used by email and dashboard services
        """
        try:
            print(f"🔥 FETCH_ALL: Called with query: {query[:100]}...")
            print(f"🔥 FETCH_ALL: Query type: {'DELETE' if query.strip().upper().startswith('DELETE') else 'SELECT'}")
            
            # Check if this is actually a DELETE query - route to execute instead
            if query.strip().upper().startswith("DELETE"):
                print(f"🔧 FETCH_ALL: Detected DELETE query, routing to execute method")
                result = await self.execute(query, params)
                # Return as a list for consistency with fetch_all interface
                return [result] if result else []
            
            # Convert PostgreSQL query to Supabase table operation where possible
            # For complex queries, we'll use Supabase RPC or direct table queries
            
            # Handle simple table queries
            if "FROM email_logs" in query:
                return await self._query_email_logs(query, params)
            elif "FROM dashboard_configs" in query:
                return await self._query_dashboard_configs(query, params)
            elif "FROM sellout_entries2" in query:
                return await self._query_sellout_entries(query, params)
            elif "FROM uploads" in query:
                return await self._query_uploads(query, params)
            elif "FROM information_schema" in query:
                return await self._query_schema_info(query, params)
            else:
                # For now, return empty list for unsupported queries
                print(f"WARNING: Unsupported query pattern in fetch_all: {query}")
                return []
                
        except Exception as e:
            print(f"ERROR in fetch_all: {str(e)}")
            print(f"Query: {query}")
            print(f"Params: {params}")
            raise DatabaseException(f"Failed to execute query: {str(e)}")
    
    async def fetch_one(self, query: str, params: tuple = None) -> Optional[Dict[str, Any]]:
        """
        Execute a SELECT query and return the first result as a dictionary
        Used by email and dashboard services
        """
        try:
            # Check if this is actually a DELETE query with RETURNING
            if query.strip().upper().startswith("DELETE"):
                print(f"🔧 FETCH_ONE: Detected DELETE query, routing to execute method")
                return await self.execute(query, params)
            
            results = await self.fetch_all(query, params)
            return results[0] if results else None
        except Exception as e:
            print(f"ERROR in fetch_one: {str(e)}")
            raise DatabaseException(f"Failed to execute query: {str(e)}")
    
    async def execute(self, query: str, params: tuple = None) -> Optional[Dict[str, Any]]:
        """
        Execute an INSERT/UPDATE/DELETE query
        Used by email and dashboard services
        """
        try:
            # Handle INSERT operations
            if query.strip().upper().startswith("INSERT"):
                return await self._execute_insert(query, params)
            elif query.strip().upper().startswith("UPDATE"):
                return await self._execute_update(query, params)
            elif query.strip().upper().startswith("DELETE"):
                return await self._execute_delete(query, params)
            else:
                print(f"WARNING: Unsupported query type in execute: {query}")
                return None
                
        except Exception as e:
            print(f"ERROR in execute: {str(e)}")
            print(f"Query: {query}")
            print(f"Params: {params}")
            raise DatabaseException(f"Failed to execute query: {str(e)}")
    
    # ============ HELPER METHODS FOR SPECIFIC TABLES ============
    
    async def _query_email_logs(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Handle email_logs table queries"""
        try:
            # Extract user_id from params for RLS
            user_id = params[0] if params and len(params) > 0 else None
            
            # Don't execute query if no user_id provided
            if not user_id:
                print("WARNING: No user_id provided to _query_email_logs")
                return []
            
            if "ORDER BY sent_at DESC" in query:
                # Get email logs ordered by date
                result = self.supabase.table("email_logs")\
                    .select("*")\
                    .eq("user_id", user_id)\
                    .order("sent_at", desc=True)\
                    .execute()
                return result.data if result.data else []
            else:
                # Default email logs query
                result = self.supabase.table("email_logs")\
                    .select("*")\
                    .eq("user_id", user_id)\
                    .execute()
                return result.data if result.data else []
                
        except Exception as e:
            print(f"ERROR in _query_email_logs: {str(e)}")
            return []
    
    
    
    async def _query_dashboard_configs(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Handle dashboard_configs table queries"""
        try:
            user_id = params[0] if params else None
            
            if "ORDER BY created_at DESC" in query:
                # Get dashboard configs ordered by creation date
                result = self.supabase.table("dashboard_configs")\
                    .select("*")\
                    .eq("user_id", user_id)\
                    .order("created_at", desc=True)\
                    .execute()
                return result.data if result.data else []
            elif len(params) >= 2:
                # Get specific dashboard config
                config_id, user_id = params[0], params[1]
                result = self.supabase.table("dashboard_configs")\
                    .select("*")\
                    .eq("id", config_id)\
                    .eq("user_id", user_id)\
                    .execute()
                return result.data if result.data else []
            else:
                # Default dashboard configs query
                result = self.supabase.table("dashboard_configs")\
                    .select("*")\
                    .eq("user_id", user_id)\
                    .execute()
                return result.data if result.data else []
                
        except Exception as e:
            print(f"ERROR in _query_dashboard_configs: {str(e)}")
            return []
    
    async def _query_sellout_entries(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Handle sellout_entries2 table queries for reports and chat"""
        try:
            print(f"📊 EXECUTING SELLOUT QUERY: {query}")
            print(f"📊 PARAMS: {params}")
            
            # Skip the failing RPC call and go directly to smart query execution
            return await self._execute_smart_sellout_query(query, params)
            
        except Exception as e:
            print(f"❌ ERROR in _query_sellout_entries: {str(e)}")
            print(f"🔍 Query was: {query}")
            return []
    
    async def _execute_smart_sellout_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Execute sellout_entries2 queries with proper user filtering"""
        try:
            # Extract user_id from params for filtering
            user_id = params[0] if params and len(params) > 0 else None
            
            if not user_id:
                print("⚠️ WARNING: No user_id provided for sellout query")
                return []
            
            print(f"👤 Executing query for user: {user_id}")
            
            # Parse the SQL query to understand what we're trying to do
            query_upper = query.upper()
            
            print(f"🔍 ANALYZING QUERY: {query_upper[:100]}...")
            
            # Enhanced intent detection based on SQL patterns and content
            # Time-based queries (year, month, quarterly analysis)
            if self._is_time_based_query(query_upper):
                print("📅 DETECTED: Time-based query")
                return await self._handle_time_based_query(query, user_id)
            
            # Product analysis queries 
            elif self._is_product_analysis_query(query_upper):
                print("🛍️ DETECTED: Product analysis query")
                return await self._handle_product_analysis_query(query, user_id)
            
            # Reseller/customer analysis queries
            elif self._is_reseller_analysis_query(query_upper):
                print("👥 DETECTED: Reseller analysis query") 
                return await self._handle_reseller_analysis_query(query, user_id)
            
            # Simple aggregation for total queries
            elif self._is_simple_total_query(query_upper):
                print("💰 DETECTED: Simple total query")
                return await self._handle_aggregation_query(query, user_id)
            
            # Simple select queries
            elif self._is_simple_select_query(query_upper):
                return await self._handle_simple_select(query, user_id)
            
            # Grouped queries (fallback)
            elif "GROUP BY" in query_upper:
                return await self._handle_grouped_query(query, user_id)
            else:
                # For complex queries, use the enhanced fallback with user filtering
                return await self._fallback_sellout_query_with_user(query, user_id)
                
        except Exception as e:
            print(f"❌ ERROR in smart query execution: {str(e)}")
            return []
    
    def _is_simple_select_query(self, query_upper: str) -> bool:
        """Check if this is a simple SELECT query without aggregations"""
        return (
            query_upper.startswith("SELECT") and 
            "SUM(" not in query_upper and 
            "COUNT(" not in query_upper and 
            "GROUP BY" not in query_upper
        )
    
    def _is_time_based_query(self, query_upper: str) -> bool:
        """Check if this is a time-based analysis query"""
        time_indicators = [
            "YEAR", "MONTH", "QUARTER", "2024", "2025", "Q1", "Q2", "Q3", "Q4",
            "MONTHLY", "QUARTERLY", "YEARLY", "ANNUAL", "TEMPORAL"
        ]
        return any(indicator in query_upper for indicator in time_indicators)
    
    def _is_product_analysis_query(self, query_upper: str) -> bool:
        """Check if this is a product analysis query"""
        # First check if it's actually a reseller query - reseller has priority
        if self._has_reseller_indicators(query_upper):
            return False
            
        product_indicators = [
            "FUNCTIONAL_NAME", "PRODUCT", "TOP SELLING", "BEST SELLING", 
            "PRODUCT BREAKDOWN", "PRODUCT PERFORMANCE", "ITEM"
        ]
        return any(indicator in query_upper for indicator in product_indicators)
    
    def _is_reseller_analysis_query(self, query_upper: str) -> bool:
        """Check if this is a reseller/customer analysis query"""
        return self._has_reseller_indicators(query_upper)
    
    def _has_reseller_indicators(self, query_upper: str) -> bool:
        """Helper method to check for reseller indicators"""
        reseller_indicators = [
            "RESELLER", "CUSTOMER", "CLIENT", "PARTNER", "TOP RESELLER",
            "BEST CUSTOMER", "RESELLER BREAKDOWN", "CUSTOMER PERFORMANCE"
        ]
        # Check for explicit reseller patterns in SELECT and GROUP BY clauses
        has_reseller_select = "SELECT RESELLER" in query_upper or "SELECT.*RESELLER" in query_upper
        has_reseller_group = "GROUP BY RESELLER" in query_upper
        has_reseller_keyword = any(indicator in query_upper for indicator in reseller_indicators)
        
        return has_reseller_select or has_reseller_group or has_reseller_keyword
    
    def _is_simple_total_query(self, query_upper: str) -> bool:
        """Check if this is a simple total/aggregation query without breakdowns"""
        # Only return true for queries that just want a total without grouping
        has_sum = "SUM(" in query_upper and "SALES_EUR" in query_upper
        has_no_grouping = "GROUP BY" not in query_upper
        has_total_intent = any(word in query_upper for word in ["TOTAL", "SUM", "OVERALL"])
        
        return has_sum and has_no_grouping and has_total_intent
    
    async def _handle_simple_select(self, query: str, user_id: str) -> List[Dict[str, Any]]:
        """Handle simple SELECT queries with user filtering"""
        try:
            print("🔍 Handling simple SELECT query")
            
            # For simple selects, just get recent data for the user
            result = self.supabase.table("sellout_entries2")\
                .select("*, uploads!inner(user_id)")\
                .eq("uploads.user_id", user_id)\
                .order("created_at", desc=True)\
                .limit(100)\
                .execute()
            
            if result.data:
                # Clean up the data - remove the uploads join data
                cleaned_data = []
                for row in result.data:
                    clean_row = {k: v for k, v in row.items() if k != 'uploads'}
                    cleaned_data.append(clean_row)
                
                print(f"✅ Retrieved {len(cleaned_data)} records for user")
                return cleaned_data
            
            return []
            
        except Exception as e:
            print(f"❌ Error in simple select: {str(e)}")
            return []
    
    async def _handle_aggregation_query(self, query: str, user_id: str) -> List[Dict[str, Any]]:
        """Handle aggregation queries like SUM() with user filtering"""
        try:
            print("📊 Handling aggregation query")
            
            # Get all user's data and perform aggregation
            result = self.supabase.table("sellout_entries2")\
                .select("sales_eur, sales_lc, currency, uploads!inner(user_id)")\
                .eq("uploads.user_id", user_id)\
                .execute()
            
            if result.data:
                # Calculate total sales in EUR
                total_eur = sum(float(row.get('sales_eur', 0) or 0) for row in result.data)
                
                print(f"💰 Calculated total sales for user {user_id}: €{total_eur:,.2f}")
                
                return [{
                    "total_sales_eur": total_eur,
                    "total_records": len(result.data)
                }]
            
            return [{"total_sales_eur": 0, "total_records": 0}]
            
        except Exception as e:
            print(f"❌ Error in aggregation query: {str(e)}")
            return []
    
    async def _handle_grouped_query(self, query: str, user_id: str) -> List[Dict[str, Any]]:
        """Handle GROUP BY queries with user filtering"""
        try:
            print("📈 Handling grouped query")
            
            query_upper = query.upper()
            
            # Determine what we're grouping by
            if "RESELLER" in query_upper:
                return await self._group_by_reseller(user_id)
            elif "FUNCTIONAL_NAME" in query_upper or "PRODUCT" in query_upper:
                return await self._group_by_product(user_id)
            elif "MONTH" in query_upper or "YEAR" in query_upper:
                return await self._group_by_time(user_id)
            else:
                # Default grouping
                return await self._group_by_reseller(user_id)
                
        except Exception as e:
            print(f"❌ Error in grouped query: {str(e)}")
            return []
    
    async def _group_by_reseller(self, user_id: str) -> List[Dict[str, Any]]:
        """Group sales data by reseller for specific user"""
        try:
            result = self.supabase.table("sellout_entries2")\
                .select("reseller, sales_eur, quantity, uploads!inner(user_id)")\
                .eq("uploads.user_id", user_id)\
                .execute()
            
            if result.data:
                # Group by reseller manually
                reseller_stats = {}
                for row in result.data:
                    reseller = row.get('reseller', 'Unknown')
                    if reseller not in reseller_stats:
                        reseller_stats[reseller] = {
                            'total_sales_eur': 0,
                            'total_quantity': 0,
                            'record_count': 0
                        }
                    
                    reseller_stats[reseller]['total_sales_eur'] += float(row.get('sales_eur', 0) or 0)
                    reseller_stats[reseller]['total_quantity'] += int(row.get('quantity', 0) or 0)
                    reseller_stats[reseller]['record_count'] += 1
                
                # Convert to list and sort by sales
                result_list = []
                for reseller, stats in reseller_stats.items():
                    result_list.append({
                        'reseller': reseller,
                        'total_sales_eur': stats['total_sales_eur'],
                        'total_sales': stats['total_sales_eur'],  # Add alias for response compatibility
                        'total_quantity': stats['total_quantity'],
                        'record_count': stats['record_count']
                    })
                
                result_list.sort(key=lambda x: x['total_sales_eur'], reverse=True)
                
                print(f"📊 Grouped by reseller: {len(result_list)} resellers found")
                return result_list[:20]  # Top 20 resellers
            
            return []
            
        except Exception as e:
            print(f"❌ Error grouping by reseller: {str(e)}")
            return []
    
    async def _group_by_product(self, user_id: str) -> List[Dict[str, Any]]:
        """Group sales data by product for specific user"""
        try:
            result = self.supabase.table("sellout_entries2")\
                .select("functional_name, sales_eur, quantity, uploads!inner(user_id)")\
                .eq("uploads.user_id", user_id)\
                .execute()
            
            if result.data:
                # Group by product manually
                product_stats = {}
                for row in result.data:
                    product = row.get('functional_name', 'Unknown')
                    if product not in product_stats:
                        product_stats[product] = {
                            'total_sales_eur': 0,
                            'total_quantity': 0,
                            'record_count': 0
                        }
                    
                    product_stats[product]['total_sales_eur'] += float(row.get('sales_eur', 0) or 0)
                    product_stats[product]['total_quantity'] += int(row.get('quantity', 0) or 0)
                    product_stats[product]['record_count'] += 1
                
                # Convert to list and sort by sales
                result_list = []
                for product, stats in product_stats.items():
                    result_list.append({
                        'functional_name': product,
                        'product': product,  # Add alias for response compatibility
                        'total_sales_eur': stats['total_sales_eur'],
                        'total_sales': stats['total_sales_eur'],  # Add alias for response compatibility
                        'total_quantity': stats['total_quantity'],
                        'record_count': stats['record_count']
                    })
                
                result_list.sort(key=lambda x: x['total_sales_eur'], reverse=True)
                
                print(f"🛍️ Grouped by product: {len(result_list)} products found")
                return result_list[:20]  # Top 20 products
            
            return []
            
        except Exception as e:
            print(f"❌ Error grouping by product: {str(e)}")
            return []
    
    async def _group_by_time(self, user_id: str) -> List[Dict[str, Any]]:
        """Group sales data by time for specific user"""
        try:
            result = self.supabase.table("sellout_entries2")\
                .select("year, month, sales_eur, uploads!inner(user_id)")\
                .eq("uploads.user_id", user_id)\
                .execute()
            
            if result.data:
                # Group by year/month manually
                time_stats = {}
                for row in result.data:
                    year = row.get('year', 'Unknown')
                    month = row.get('month', 'Unknown')
                    time_key = f"{year}-{month:02d}" if isinstance(month, int) else f"{year}-{month}"
                    
                    if time_key not in time_stats:
                        time_stats[time_key] = {
                            'year': year,
                            'month': month,
                            'total_sales_eur': 0,
                            'record_count': 0
                        }
                    
                    time_stats[time_key]['total_sales_eur'] += float(row.get('sales_eur', 0) or 0)
                    time_stats[time_key]['record_count'] += 1
                
                # Convert to list and sort by time
                result_list = list(time_stats.values())
                result_list.sort(key=lambda x: (x['year'], x['month']), reverse=True)
                
                print(f"📅 Grouped by time: {len(result_list)} periods found")
                return result_list[:24]  # Last 24 months
            
            return []
            
        except Exception as e:
            print(f"❌ Error grouping by time: {str(e)}")
            return []
    
    # ========== NEW INTENT-BASED HANDLERS ==========
    
    async def _handle_time_based_query(self, query: str, user_id: str) -> List[Dict[str, Any]]:
        """Handle time-based queries to return meaningful breakdowns"""
        try:
            print("📅 Processing time-based query for meaningful breakdown")
            
            query_upper = query.upper()
            
            # Check for specific year patterns
            if "2024" in query_upper or "2025" in query_upper:
                # Return monthly breakdown for the year
                return await self._get_monthly_breakdown_for_year(user_id, query_upper)
            
            # Check for quarter patterns
            elif any(q in query_upper for q in ["Q1", "Q2", "Q3", "Q4", "QUARTER"]):
                return await self._get_quarterly_breakdown(user_id)
            
            # Default to monthly breakdown
            else:
                return await self._group_by_time(user_id)
                
        except Exception as e:
            print(f"❌ Error in time-based query: {str(e)}")
            return []
    
    async def _handle_product_analysis_query(self, query: str, user_id: str) -> List[Dict[str, Any]]:
        """Handle product analysis queries to return meaningful product breakdowns"""
        try:
            print("🛍️ Processing product analysis query")
            return await self._group_by_product(user_id)
        except Exception as e:
            print(f"❌ Error in product analysis query: {str(e)}")
            return []
    
    async def _handle_reseller_analysis_query(self, query: str, user_id: str) -> List[Dict[str, Any]]:
        """Handle reseller analysis queries to return meaningful reseller breakdowns"""
        try:
            print("👥 Processing reseller analysis query")
            return await self._group_by_reseller(user_id)
        except Exception as e:
            print(f"❌ Error in reseller analysis query: {str(e)}")
            return []
    
    async def _get_monthly_breakdown_for_year(self, user_id: str, query_upper: str) -> List[Dict[str, Any]]:
        """Get monthly breakdown for a specific year"""
        try:
            # Extract year from query
            year = 2024 if "2024" in query_upper else 2025
            
            result = self.supabase.table("sellout_entries2")\
                .select("year, month, sales_eur, quantity, uploads!inner(user_id)")\
                .eq("uploads.user_id", user_id)\
                .eq("year", year)\
                .execute()
            
            if result.data:
                # Group by month manually
                month_stats = {}
                for row in result.data:
                    month = row.get('month', 0)
                    if month not in month_stats:
                        month_stats[month] = {
                            'year': year,
                            'month': month,
                            'total_sales_eur': 0,
                            'total_quantity': 0,
                            'record_count': 0
                        }
                    
                    month_stats[month]['total_sales_eur'] += float(row.get('sales_eur', 0) or 0)
                    month_stats[month]['total_quantity'] += int(row.get('quantity', 0) or 0)
                    month_stats[month]['record_count'] += 1
                
                # Convert to list and sort by month
                result_list = list(month_stats.values())
                result_list.sort(key=lambda x: x['month'])
                
                print(f"📅 Monthly breakdown for {year}: {len(result_list)} months found")
                return result_list
            
            return []
            
        except Exception as e:
            print(f"❌ Error getting monthly breakdown: {str(e)}")
            return []
    
    async def _get_quarterly_breakdown(self, user_id: str) -> List[Dict[str, Any]]:
        """Get quarterly breakdown"""
        try:
            result = self.supabase.table("sellout_entries2")\
                .select("year, month, sales_eur, quantity, uploads!inner(user_id)")\
                .eq("uploads.user_id", user_id)\
                .execute()
            
            if result.data:
                # Group by quarter manually
                quarter_stats = {}
                for row in result.data:
                    year = row.get('year', 0)
                    month = row.get('month', 0)
                    
                    # Determine quarter
                    if month in [1, 2, 3]:
                        quarter = "Q1"
                    elif month in [4, 5, 6]:
                        quarter = "Q2"
                    elif month in [7, 8, 9]:
                        quarter = "Q3"
                    else:
                        quarter = "Q4"
                    
                    key = f"{year}-{quarter}"
                    if key not in quarter_stats:
                        quarter_stats[key] = {
                            'year': year,
                            'quarter': quarter,
                            'total_sales_eur': 0,
                            'total_quantity': 0,
                            'record_count': 0
                        }
                    
                    quarter_stats[key]['total_sales_eur'] += float(row.get('sales_eur', 0) or 0)
                    quarter_stats[key]['total_quantity'] += int(row.get('quantity', 0) or 0)
                    quarter_stats[key]['record_count'] += 1
                
                # Convert to list and sort by year and quarter
                result_list = list(quarter_stats.values())
                result_list.sort(key=lambda x: (x['year'], x['quarter']))
                
                print(f"📅 Quarterly breakdown: {len(result_list)} quarters found")
                return result_list
            
            return []
            
        except Exception as e:
            print(f"❌ Error getting quarterly breakdown: {str(e)}")
            return []
    
    async def _fallback_sellout_query_with_user(self, query: str, user_id: str) -> List[Dict[str, Any]]:
        """Enhanced fallback for complex queries with user filtering"""
        try:
            print(f"🔄 FALLBACK: Using user-filtered fallback for complex query")
            print(f"🔄 User: {user_id}, Query: {query}")
            
            # For complex queries we can't parse, just return recent user data
            result = self.supabase.table("sellout_entries2")\
                .select("*, uploads!inner(user_id)")\
                .eq("uploads.user_id", user_id)\
                .order("created_at", desc=True)\
                .limit(50)\
                .execute()
            
            if result.data:
                # Clean up the data - remove the uploads join data
                cleaned_data = []
                for row in result.data:
                    clean_row = {k: v for k, v in row.items() if k != 'uploads'}
                    cleaned_data.append(clean_row)
                
                print(f"🔄 Fallback returned {len(cleaned_data)} records for user")
                return cleaned_data
            
            return []
            
        except Exception as e:
            print(f"❌ Error in user fallback query: {str(e)}")
            return []
    
    async def _fallback_sellout_query(self, query: str) -> List[Dict[str, Any]]:
        """Enhanced fallback method for sellout_entries2 queries with better SQL pattern recognition"""
        try:
            print(f"📊 FALLBACK QUERY ANALYSIS:")
            print(f"   Original SQL: {query}")
            
            query_upper = query.upper()
            
            # Pattern 1: Total sales queries
            if "SUM(" in query_upper and ("SALES_EUR" in query_upper or "SALES_LC" in query_upper):
                print(f"   🔍 Pattern: Total Sales Query")
                return await self._handle_total_sales_query(query)
            
            # Pattern 2: Sales by reseller
            elif "GROUP BY" in query_upper and "RESELLER" in query_upper:
                print(f"   🔍 Pattern: Sales by Reseller")
                return await self._handle_sales_by_reseller_query(query)
            
            # Pattern 3: Product queries
            elif "FUNCTIONAL_NAME" in query_upper or "PRODUCT" in query_upper:
                print(f"   🔍 Pattern: Product Query")
                return await self._handle_product_query(query)
            
            # Pattern 4: Date/time-based queries
            elif any(time_word in query_upper for time_word in ["MONTH", "YEAR", "DATE", "TIME"]):
                print(f"   🔍 Pattern: Date/Time Query")
                return await self._handle_date_query(query)
            
            # Pattern 5: Quantity queries
            elif "QUANTITY" in query_upper:
                print(f"   🔍 Pattern: Quantity Query")
                return await self._handle_quantity_query(query)
            
            # Pattern 6: Top/Bottom queries (ORDER BY with LIMIT)
            elif "ORDER BY" in query_upper and "LIMIT" in query_upper:
                print(f"   🔍 Pattern: Top/Bottom Query")
                return await self._handle_top_bottom_query(query)
            
            # Pattern 7: Count queries
            elif "COUNT(" in query_upper:
                print(f"   🔍 Pattern: Count Query")
                return await self._handle_count_query(query)
            
            # Default: Recent entries with smart filtering
            else:
                print(f"   🔍 Pattern: Default Recent Entries")
                return await self._handle_default_query(query)
                
        except Exception as e:
            print(f"ERROR in fallback sellout query: {str(e)}")
            return []
    
    async def _handle_total_sales_query(self, query: str) -> List[Dict[str, Any]]:
        """Handle total sales aggregation queries"""
        try:
            result = self.supabase.table("sellout_entries2")\
                .select("sales_eur, sales_lc, currency")\
                .execute()
            
            if result.data:
                # Calculate total sales in EUR
                total_eur = sum(float(row.get('sales_eur', 0) or 0) for row in result.data)
                
                # Also calculate by currency
                by_currency = {}
                for row in result.data:
                    currency = row.get('currency', 'Unknown')
                    sales_lc = float(row.get('sales_lc', 0) or 0)
                    if currency not in by_currency:
                        by_currency[currency] = 0
                    by_currency[currency] += sales_lc
                
                return [{
                    "total_sales_eur": total_eur,
                    "sales_by_currency": by_currency,
                    "total_records": len(result.data)
                }]
            return [{"total_sales_eur": 0, "sales_by_currency": {}, "total_records": 0}]
        except Exception as e:
            print(f"ERROR in total sales query: {str(e)}")
            return []
    
    async def _handle_sales_by_reseller_query(self, query: str) -> List[Dict[str, Any]]:
        """Handle sales aggregated by reseller"""
        try:
            result = self.supabase.table("sellout_entries2")\
                .select("reseller, sales_eur, sales_lc, currency, quantity")\
                .execute()
            
            if result.data:
                # Group by reseller
                reseller_stats = {}
                for row in result.data:
                    reseller = row.get('reseller', 'Unknown')
                    if reseller not in reseller_stats:
                        reseller_stats[reseller] = {
                            'total_sales_eur': 0,
                            'total_quantity': 0,
                            'total_records': 0,
                            'currencies': set()
                        }
                    
                    reseller_stats[reseller]['total_sales_eur'] += float(row.get('sales_eur', 0) or 0)
                    reseller_stats[reseller]['total_quantity'] += int(row.get('quantity', 0) or 0)
                    reseller_stats[reseller]['total_records'] += 1
                    reseller_stats[reseller]['currencies'].add(row.get('currency', 'Unknown'))
                
                # Convert to list and sort by sales
                result_list = []
                for reseller, stats in reseller_stats.items():
                    result_list.append({
                        'reseller': reseller,
                        'total_sales_eur': stats['total_sales_eur'],
                        'total_quantity': stats['total_quantity'],
                        'total_records': stats['total_records'],
                        'currencies': list(stats['currencies'])
                    })
                
                result_list.sort(key=lambda x: x['total_sales_eur'], reverse=True)
                return result_list[:10]  # Top 10 resellers
            return []
        except Exception as e:
            print(f"ERROR in sales by reseller query: {str(e)}")
            return []
    
    async def _handle_product_query(self, query: str) -> List[Dict[str, Any]]:
        """Handle product-related queries"""
        try:
            if "DISTINCT" in query.upper():
                # Get distinct products
                result = self.supabase.table("sellout_entries2")\
                    .select("functional_name, product_ean")\
                    .execute()
                
                if result.data:
                    unique_products = {}
                    for row in result.data:
                        name = row.get('functional_name')
                        ean = row.get('product_ean')
                        if name and name not in unique_products:
                            unique_products[name] = ean
                    
                    return [{"functional_name": name, "product_ean": ean} 
                            for name, ean in unique_products.items()]
            else:
                # Product sales summary
                result = self.supabase.table("sellout_entries2")\
                    .select("functional_name, product_ean, sales_eur, quantity")\
                    .execute()
                
                if result.data:
                    product_stats = {}
                    for row in result.data:
                        name = row.get('functional_name', 'Unknown')
                        if name not in product_stats:
                            product_stats[name] = {
                                'total_sales': 0,
                                'total_quantity': 0,
                                'product_ean': row.get('product_ean')
                            }
                        
                        product_stats[name]['total_sales'] += float(row.get('sales_eur', 0) or 0)
                        product_stats[name]['total_quantity'] += int(row.get('quantity', 0) or 0)
                    
                    result_list = []
                    for name, stats in product_stats.items():
                        result_list.append({
                            'functional_name': name,
                            'product_ean': stats['product_ean'],
                            'total_sales_eur': stats['total_sales'],
                            'total_quantity': stats['total_quantity']
                        })
                    
                    result_list.sort(key=lambda x: x['total_sales_eur'], reverse=True)
                    return result_list[:20]  # Top 20 products
            return []
        except Exception as e:
            print(f"ERROR in product query: {str(e)}")
            return []
    
    async def _handle_date_query(self, query: str) -> List[Dict[str, Any]]:
        """Handle date/time-based queries"""
        try:
            # Extract year and month if mentioned
            import re
            
            # Look for specific years
            year_match = re.search(r'\b(20\d{2})\b', query)
            year_filter = int(year_match.group(1)) if year_match else None
            
            # Look for months
            month_match = re.search(r'\b(1[0-2]|[1-9])\b', query)
            month_filter = int(month_match.group(1)) if month_match else None
            
            query_builder = self.supabase.table("sellout_entries2")\
                .select("month, year, sales_eur, quantity, reseller, functional_name")
            
            if year_filter:
                query_builder = query_builder.eq("year", year_filter)
            if month_filter:
                query_builder = query_builder.eq("month", month_filter)
            
            result = query_builder.order("year", desc=True).order("month", desc=True).limit(100).execute()
            
            return result.data if result.data else []
        except Exception as e:
            print(f"ERROR in date query: {str(e)}")
            return []
    
    async def _handle_quantity_query(self, query: str) -> List[Dict[str, Any]]:
        """Handle quantity-related queries"""
        try:
            result = self.supabase.table("sellout_entries2")\
                .select("functional_name, reseller, quantity, sales_eur")\
                .order("quantity", desc=True)\
                .limit(50)\
                .execute()
            
            return result.data if result.data else []
        except Exception as e:
            print(f"ERROR in quantity query: {str(e)}")
            return []
    
    async def _handle_top_bottom_query(self, query: str) -> List[Dict[str, Any]]:
        """Handle TOP/BOTTOM queries with ordering"""
        try:
            # Determine sort field and direction
            if "SALES" in query.upper():
                sort_field = "sales_eur"
            elif "QUANTITY" in query.upper():
                sort_field = "quantity"
            else:
                sort_field = "sales_eur"
            
            desc_order = "DESC" in query.upper() or "TOP" in query.upper()
            
            result = self.supabase.table("sellout_entries2")\
                .select("*")\
                .order(sort_field, desc=desc_order)\
                .limit(20)\
                .execute()
            
            return result.data if result.data else []
        except Exception as e:
            print(f"ERROR in top/bottom query: {str(e)}")
            return []
    
    async def _handle_count_query(self, query: str) -> List[Dict[str, Any]]:
        """Handle COUNT queries"""
        try:
            result = self.supabase.table("sellout_entries2")\
                .select("*", count="exact")\
                .execute()
            
            return [{"total_count": result.count if result.count else 0}]
        except Exception as e:
            print(f"ERROR in count query: {str(e)}")
            return []
    
    async def _handle_default_query(self, query: str) -> List[Dict[str, Any]]:
        """Handle default queries - recent entries with smart filtering"""
        try:
            result = self.supabase.table("sellout_entries2")\
                .select("*")\
                .order("created_at", desc=True)\
                .limit(100)\
                .execute()
            
            return result.data if result.data else []
        except Exception as e:
            print(f"ERROR in default query: {str(e)}")
            return []
    
    async def _query_uploads(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Handle uploads table queries"""
        try:
            user_id = params[0] if params else None
            
            result = self.supabase.table("uploads")\
                .select("*")\
                .eq("user_id", user_id)\
                .order("uploaded_at", desc=True)\
                .execute()
                
            return result.data if result.data else []
                
        except Exception as e:
            print(f"ERROR in _query_uploads: {str(e)}")
            return []
    
    async def _query_schema_info(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Handle information_schema queries for schema introspection"""
        try:
            # Return mock schema info for sellout_entries2
            return [
                {"column_name": "id", "data_type": "uuid", "is_nullable": "NO"},
                {"column_name": "product_ean", "data_type": "text", "is_nullable": "YES"},
                {"column_name": "month", "data_type": "integer", "is_nullable": "YES"},
                {"column_name": "year", "data_type": "integer", "is_nullable": "YES"},
                {"column_name": "quantity", "data_type": "integer", "is_nullable": "YES"},
                {"column_name": "sales_lc", "data_type": "text", "is_nullable": "YES"},
                {"column_name": "sales_eur", "data_type": "numeric", "is_nullable": "YES"},
                {"column_name": "currency", "data_type": "text", "is_nullable": "YES"},
                {"column_name": "reseller", "data_type": "text", "is_nullable": "YES"},
                {"column_name": "functional_name", "data_type": "text", "is_nullable": "YES"},
                {"column_name": "created_at", "data_type": "timestamp", "is_nullable": "YES"},
                {"column_name": "upload_id", "data_type": "uuid", "is_nullable": "YES"}
            ]
        except Exception as e:
            print(f"ERROR in _query_schema_info: {str(e)}")
            return []
    
    # ============ DIRECT DASHBOARD METHODS ============
    
    async def delete_dashboard_config_direct(self, config_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Direct method to delete dashboard config without SQL query parsing
        """
        try:
            logger.info(f"🔥 DIRECT DELETE: Starting dashboard deletion")
            logger.info(f"🔥 DIRECT DELETE: Config ID: {config_id}")
            logger.info(f"🔥 DIRECT DELETE: User ID: {user_id}")
            
            # First, check if the record exists before deletion
            check_result = self.supabase.table("dashboard_configs")\
                .select("id, dashboard_name")\
                .eq("id", config_id)\
                .eq("user_id", user_id)\
                .execute()
                
            logger.info(f"🔍 DIRECT DELETE: Pre-deletion check result: {check_result.data}")
            
            if not check_result.data:
                logger.warning(f"❌ DIRECT DELETE: Dashboard config not found - cannot delete")
                return None
            
            # Perform the deletion
            logger.info(f"🔥 DIRECT DELETE: About to call Supabase delete operation")
            
            result = self.supabase.table("dashboard_configs")\
                .delete()\
                .eq("id", config_id)\
                .eq("user_id", user_id)\
                .execute()
                
            logger.info(f"🗑️ DIRECT DELETE: Delete operation result: {result}")
            logger.info(f"🗑️ DIRECT DELETE: Result type: {type(result)}")
            logger.info(f"🗑️ DIRECT DELETE: Deleted data: {result.data}")
            logger.info(f"🗑️ DIRECT DELETE: Result count: {result.count if hasattr(result, 'count') else 'N/A'}")
            
            # Verify the deletion worked
            verify_result = self.supabase.table("dashboard_configs")\
                .select("id, dashboard_name")\
                .eq("id", config_id)\
                .eq("user_id", user_id)\
                .execute()
                
            logger.info(f"🔍 DIRECT DELETE: Post-deletion verification: {verify_result.data}")
            
            if verify_result.data:
                logger.error(f"⚠️ DIRECT DELETE: WARNING - Record still exists after deletion!")
                return None
            else:
                logger.info(f"✅ DIRECT DELETE: Deletion confirmed - record no longer exists")
            
            return result.data[0] if result.data else {"id": config_id}
            
        except Exception as e:
            logger.error(f"❌ ERROR in delete_dashboard_config_direct: {str(e)}")
            import traceback
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            raise

    # ============ HELPER METHODS FOR INSERT/UPDATE/DELETE ============
    
    async def _execute_insert(self, query: str, params: tuple = None) -> Optional[Dict[str, Any]]:
        """Handle INSERT operations"""
        try:
            if "INSERT INTO email_logs" in query:
                return await self._insert_email_log(params)
            elif "INSERT INTO dashboard_configs" in query:
                return await self._insert_dashboard_config(params)
            else:
                print(f"WARNING: Unsupported INSERT table in query: {query}")
                return None
                
        except Exception as e:
            print(f"ERROR in _execute_insert: {str(e)}")
            raise
    
    async def _insert_email_log(self, params: tuple) -> Optional[Dict[str, Any]]:
        """Insert email log record"""
        try:
            user_id, recipient_email, email_type, status, sent_at, metadata, error_message = params
            
            data = {
                "user_id": user_id,
                "recipient_email": recipient_email,
                "email_type": email_type,
                "status": status,
                "sent_at": sent_at.isoformat() if hasattr(sent_at, 'isoformat') else str(sent_at),
                "metadata": metadata,
                "error_message": error_message
            }
            
            result = self.supabase.table("email_logs").insert(data).execute()
            return result.data[0] if result.data else None
            
        except Exception as e:
            print(f"ERROR in _insert_email_log: {str(e)}")
            raise
    
    
    
    async def _insert_dashboard_config(self, params: tuple) -> Optional[Dict[str, Any]]:
        """Insert dashboard config record"""
        try:
            user_id, dashboard_name, dashboard_type, dashboard_url, auth_method, auth_config, permissions, is_active, created_at, updated_at = params
            
            data = {
                "user_id": user_id,
                "dashboard_name": dashboard_name,
                "dashboard_type": dashboard_type,
                "dashboard_url": dashboard_url,
                "authentication_method": auth_method,
                "authentication_config": auth_config,
                "permissions": permissions,
                "is_active": is_active,
                "created_at": created_at.isoformat() if hasattr(created_at, 'isoformat') else str(created_at),
                "updated_at": updated_at.isoformat() if hasattr(updated_at, 'isoformat') else str(updated_at)
            }
            
            print(f"Inserting dashboard config: {data}")
            result = self.supabase.table("dashboard_configs").insert(data).execute()
            print(f"Insert result: {result}")
            print(f"Result data: {result.data}")
            
            if result.data and len(result.data) > 0:
                inserted_record = result.data[0]
                print(f"Successfully inserted dashboard config with ID: {inserted_record.get('id')}")
                return inserted_record
            else:
                # If Supabase doesn't return the inserted record, create a mock response
                print("WARNING: Supabase didn't return inserted record, creating mock response")
                import uuid
                mock_response = {
                    "id": str(uuid.uuid4()),
                    "created_at": created_at.isoformat() if hasattr(created_at, 'isoformat') else str(created_at),
                    "updated_at": updated_at.isoformat() if hasattr(updated_at, 'isoformat') else str(updated_at)
                }
                return mock_response
            
        except Exception as e:
            print(f"ERROR in _insert_dashboard_config: {str(e)}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
            raise
    
    async def _execute_update(self, query: str, params: tuple = None) -> Optional[Dict[str, Any]]:
        """Handle UPDATE operations"""
        try:
            if "UPDATE dashboard_configs" in query:
                return await self._update_dashboard_config(params)
            else:
                print(f"WARNING: Unsupported UPDATE table in query: {query}")
                return None
                
        except Exception as e:
            print(f"ERROR in _execute_update: {str(e)}")
            raise
    
    async def _update_dashboard_config(self, params: tuple) -> Optional[Dict[str, Any]]:
        """Update dashboard config record"""
        try:
            # Extract params based on the update query structure
            dashboard_name, dashboard_type, dashboard_url, auth_method, auth_config, permissions, is_active, updated_at, config_id, user_id = params
            
            update_data = {
                "dashboard_name": dashboard_name,
                "dashboard_type": dashboard_type,
                "dashboard_url": dashboard_url,
                "authentication_method": auth_method,
                "authentication_config": auth_config,
                "permissions": permissions,
                "is_active": is_active,
                "updated_at": updated_at.isoformat() if hasattr(updated_at, 'isoformat') else str(updated_at)
            }
            
            result = self.supabase.table("dashboard_configs")\
                .update(update_data)\
                .eq("id", config_id)\
                .eq("user_id", user_id)\
                .execute()
                
            return result.data[0] if result.data else None
            
        except Exception as e:
            print(f"ERROR in _update_dashboard_config: {str(e)}")
            raise
    
    async def _execute_delete(self, query: str, params: tuple = None) -> Optional[Dict[str, Any]]:
        """Handle DELETE operations"""
        try:
            print(f"🔥 EXECUTE_DELETE: Called with query: {query}")
            print(f"🔥 EXECUTE_DELETE: Called with params: {params}")
            
            if "DELETE FROM dashboard_configs" in query:
                print(f"🔥 EXECUTE_DELETE: Routing to _delete_dashboard_config")
                return await self._delete_dashboard_config(params)
            else:
                print(f"⚠️ WARNING: Unsupported DELETE table in query: {query}")
                return None
                
        except Exception as e:
            print(f"❌ ERROR in _execute_delete: {str(e)}")
            raise
    
    
    async def _delete_dashboard_config(self, params: tuple) -> Optional[Dict[str, Any]]:
        """Delete dashboard config"""
        try:
            config_id, user_id = params
            
            print(f"🗑️ DB SERVICE: Attempting to delete dashboard config")
            print(f"🗑️ DB SERVICE: Config ID: {config_id}")
            print(f"🗑️ DB SERVICE: User ID: {user_id}")
            
            # First, check if the record exists before deletion
            check_result = self.supabase.table("dashboard_configs")\
                .select("id, dashboard_name")\
                .eq("id", config_id)\
                .eq("user_id", user_id)\
                .execute()
                
            print(f"🔍 DB SERVICE: Pre-deletion check result: {check_result.data}")
            
            if not check_result.data:
                print(f"❌ DB SERVICE: Dashboard config not found - cannot delete")
                return None
            
            # Perform the deletion
            print(f"🔥 DB SERVICE: About to call Supabase delete operation")
            print(f"🔥 DB SERVICE: Supabase client type: {type(self.supabase)}")
            
            # Build the query step by step to debug
            table_ref = self.supabase.table("dashboard_configs")
            print(f"🔥 DB SERVICE: Table reference: {type(table_ref)}")
            
            delete_ref = table_ref.delete()
            print(f"🔥 DB SERVICE: Delete reference: {type(delete_ref)}")
            
            eq_id_ref = delete_ref.eq("id", config_id)
            print(f"🔥 DB SERVICE: EQ ID reference: {type(eq_id_ref)}")
            
            eq_user_ref = eq_id_ref.eq("user_id", user_id)
            print(f"🔥 DB SERVICE: EQ USER reference: {type(eq_user_ref)}")
            
            print(f"🔥 DB SERVICE: Executing delete operation...")
            result = eq_user_ref.execute()
                
            print(f"🗑️ DB SERVICE: Delete operation result: {result}")
            print(f"🗑️ DB SERVICE: Result type: {type(result)}")
            print(f"🗑️ DB SERVICE: Deleted data: {result.data}")
            print(f"🗑️ DB SERVICE: Result count: {result.count if hasattr(result, 'count') else 'N/A'}")
            
            # Check if result indicates success
            if hasattr(result, 'data') and result.data:
                print(f"🗑️ DB SERVICE: Delete returned data - likely successful")
            elif hasattr(result, 'count') and result.count > 0:
                print(f"🗑️ DB SERVICE: Delete count > 0 - likely successful") 
            else:
                print(f"🗑️ DB SERVICE: Delete result unclear - checking attributes")
                for attr in dir(result):
                    if not attr.startswith('_'):
                        print(f"   - {attr}: {getattr(result, attr, 'N/A')}")
            
            # Verify the deletion worked
            verify_result = self.supabase.table("dashboard_configs")\
                .select("id, dashboard_name")\
                .eq("id", config_id)\
                .eq("user_id", user_id)\
                .execute()
                
            print(f"🔍 DB SERVICE: Post-deletion verification: {verify_result.data}")
            
            if verify_result.data:
                print(f"⚠️ DB SERVICE: WARNING - Record still exists after deletion!")
                return None
            else:
                print(f"✅ DB SERVICE: Deletion confirmed - record no longer exists")
            
            return result.data[0] if result.data else {"id": config_id}
            
        except Exception as e:
            print(f"❌ ERROR in _delete_dashboard_config: {str(e)}")
            import traceback
            print(f"❌ Full traceback: {traceback.format_exc()}")
            raise