import snowflake.connector
from snowflake.connector import DictCursor
from typing import List, Dict, Any, Optional
from contextlib import contextmanager
import logging

from config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class SnowflakeConnector:
    def __init__(self):
        self.connection_params = {
            'account': settings.snowflake_account,
            'user': settings.snowflake_user,
            'password': settings.snowflake_password,
            'warehouse': settings.snowflake_warehouse,
            'database': settings.snowflake_database,
            'schema': settings.snowflake_schema,
            'role': settings.snowflake_role
        }
    
    @contextmanager
    def get_connection(self):
        conn = None
        try:
            conn = snowflake.connector.connect(**self.connection_params)
            yield conn
        finally:
            if conn:
                conn.close()
    
    def execute_read_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Execute a read-only query on Snowflake.
        Enforces SELECT-only queries and result limits.
        """
        # Basic validation - ensure it's a SELECT query
        query_upper = query.strip().upper()
        if not query_upper.startswith('SELECT'):
            raise ValueError("Only SELECT queries are allowed")
        
        # Check for dangerous keywords
        dangerous_keywords = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER', 'TRUNCATE']
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                raise ValueError(f"Query contains forbidden keyword: {keyword}")
        
        # Add limit if not present
        if 'LIMIT' not in query_upper:
            query = f"{query} LIMIT {limit}"
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(DictCursor)
                
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                results = cursor.fetchall()
                cursor.close()
                
                return results
                
        except Exception as e:
            logger.error(f"Error executing Snowflake query: {str(e)}")
            raise
    
    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Get schema information for a specific table."""
        query = """
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            IS_NULLABLE,
            COLUMN_DEFAULT,
            COMMENT
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = %(table_name)s
            AND TABLE_SCHEMA = %(schema)s
        ORDER BY ORDINAL_POSITION
        """
        
        return self.execute_read_query(
            query,
            params={
                'table_name': table_name,
                'schema': settings.snowflake_schema
            }
        )
    
    def list_available_tables(self) -> List[str]:
        """List all tables available in the current schema."""
        query = """
        SELECT TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = %(schema)s
            AND TABLE_TYPE IN ('BASE TABLE', 'VIEW')
        ORDER BY TABLE_NAME
        """
        
        results = self.execute_read_query(
            query,
            params={'schema': settings.snowflake_schema}
        )
        
        return [row['TABLE_NAME'] for row in results]
    
    def validate_query_safety(self, query: str) -> bool:
        """
        Validate that a query is safe to execute.
        Returns True if safe, False otherwise.
        """
        query_upper = query.strip().upper()
        
        # Must be a SELECT query
        if not query_upper.startswith('SELECT'):
            return False
        
        # Check for dangerous operations
        dangerous_patterns = [
            'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 
            'ALTER', 'TRUNCATE', 'MERGE', 'CALL', 'EXECUTE'
        ]
        
        for pattern in dangerous_patterns:
            if pattern in query_upper:
                return False
        
        return True


# Singleton instance
snowflake_connector = SnowflakeConnector()