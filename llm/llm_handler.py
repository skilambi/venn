import openai
import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from config.settings import get_settings
from database.snowflake_connector import snowflake_connector

logger = logging.getLogger(__name__)
settings = get_settings()

openai.api_key = settings.openai_api_key


class LLMHandler:
    def __init__(self):
        self.model = settings.llm_model
        self.temperature = settings.llm_temperature
        self.max_tokens = settings.llm_max_tokens
    
    def extract_sql_from_response(self, response: str) -> Optional[str]:
        """Extract SQL query from LLM response."""
        # Look for SQL in code blocks
        sql_pattern = r'```sql\n(.*?)\n```'
        matches = re.findall(sql_pattern, response, re.DOTALL | re.IGNORECASE)
        
        if matches:
            return matches[0].strip()
        
        # Look for SELECT statements
        select_pattern = r'(SELECT\s+.*?(?:;|$))'
        matches = re.findall(select_pattern, response, re.DOTALL | re.IGNORECASE)
        
        if matches:
            return matches[0].strip()
        
        return None
    
    async def generate_sql_query(
        self,
        user_prompt: str,
        available_tables: List[str],
        table_schemas: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Generate SQL query based on user prompt and available tables."""
        
        # Build context about available tables
        schema_context = "Available tables and their schemas:\n\n"
        for table in available_tables:
            schema_context += f"Table: {table}\n"
            if table in table_schemas:
                schema_context += "Columns:\n"
                for col in table_schemas[table]:
                    schema_context += f"  - {col['COLUMN_NAME']} ({col['DATA_TYPE']})"
                    if col.get('COMMENT'):
                        schema_context += f" - {col['COMMENT']}"
                    schema_context += "\n"
            schema_context += "\n"
        
        system_prompt = """You are a SQL query assistant for Snowflake databases.
Your role is to help users query data by generating safe, read-only SQL queries.

Rules:
1. ONLY generate SELECT queries - no modifications allowed
2. Always include appropriate LIMIT clauses (max 1000 rows)
3. Use proper Snowflake SQL syntax
4. If the user's request is unclear, ask for clarification
5. Explain what the query does in simple terms

When providing a SQL query, always wrap it in ```sql``` code blocks."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"{schema_context}\n\nUser request: {user_prompt}"}
        ]
        
        try:
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            content = response.choices[0].message.content
            sql_query = self.extract_sql_from_response(content)
            
            return {
                "success": True,
                "response": content,
                "sql_query": sql_query,
                "model_used": self.model
            }
            
        except Exception as e:
            logger.error(f"Error generating SQL query: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": None,
                "sql_query": None
            }
    
    async def process_data_request(
        self,
        user_prompt: str,
        allowed_tables: Optional[List[str]] = None,
        enterprise_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a data request from a user in a thread.
        Generates SQL, executes it, and returns formatted results.
        """
        
        # Get available tables
        all_tables = snowflake_connector.list_available_tables()
        
        # Filter to allowed tables if specified
        if allowed_tables:
            available_tables = [t for t in all_tables if t in allowed_tables]
        else:
            available_tables = all_tables
        
        if not available_tables:
            return {
                "success": False,
                "error": "No tables available for querying",
                "message": "You don't have access to any tables in this context."
            }
        
        # Get schemas for available tables
        table_schemas = {}
        for table in available_tables[:10]:  # Limit to first 10 tables for context
            try:
                table_schemas[table] = snowflake_connector.get_table_schema(table)
            except Exception as e:
                logger.warning(f"Could not get schema for table {table}: {str(e)}")
        
        # Generate SQL query
        sql_result = await self.generate_sql_query(user_prompt, available_tables, table_schemas)
        
        if not sql_result["success"] or not sql_result["sql_query"]:
            return {
                "success": False,
                "error": "Could not generate SQL query",
                "llm_response": sql_result.get("response"),
                "message": "I couldn't generate a valid SQL query for your request."
            }
        
        # Validate query safety
        if not snowflake_connector.validate_query_safety(sql_result["sql_query"]):
            return {
                "success": False,
                "error": "Generated query is not safe to execute",
                "sql_query": sql_result["sql_query"],
                "message": "The generated query contains forbidden operations."
            }
        
        # Execute query
        try:
            query_results = snowflake_connector.execute_read_query(
                sql_result["sql_query"],
                limit=100  # Limit results for chat context
            )
            
            # Format results for display
            formatted_results = self.format_query_results(query_results)
            
            return {
                "success": True,
                "sql_query": sql_result["sql_query"],
                "llm_response": sql_result["response"],
                "query_results": query_results,
                "formatted_results": formatted_results,
                "row_count": len(query_results),
                "model_used": sql_result["model_used"],
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "sql_query": sql_result["sql_query"],
                "llm_response": sql_result["response"],
                "message": f"Error executing query: {str(e)}"
            }
    
    def format_query_results(self, results: List[Dict[str, Any]], max_rows: int = 10) -> str:
        """Format query results for display in chat."""
        if not results:
            return "No results found."
        
        # Get column names
        columns = list(results[0].keys())
        
        # Create formatted output
        output = f"Found {len(results)} rows. Showing first {min(len(results), max_rows)}:\n\n"
        
        # Add header
        output += " | ".join(columns) + "\n"
        output += "-" * (len(" | ".join(columns))) + "\n"
        
        # Add rows
        for row in results[:max_rows]:
            row_values = [str(row.get(col, "")) for col in columns]
            output += " | ".join(row_values) + "\n"
        
        if len(results) > max_rows:
            output += f"\n... and {len(results) - max_rows} more rows"
        
        return output


# Singleton instance
llm_handler = LLMHandler()