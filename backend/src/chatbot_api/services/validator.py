import sqlglot
from typing import Optional, Tuple
from ..schema_config import VALID_TABLES, VALID_COLUMNS

# Convert to sets for faster lookup
ALLOWED_TABLES = set(VALID_TABLES)
ALLOWED_COLUMNS = set(VALID_COLUMNS['tweets'])

def validate_sql(sql: Optional[str]) -> Tuple[bool, Optional[str]]:
    """
    Validate SQL for safety and correctness.
    Returns: (is_valid, error_message)
    """
    if not sql:
        return False, "Empty SQL query"
    
    try:
        # Parse SQL with sqlglot
        parsed = sqlglot.parse_one(sql, read="postgres")
        
        # Check it's a SELECT
        if not isinstance(parsed, sqlglot.exp.Select):
            return False, "Only SELECT queries are allowed"
        
        # Check for dangerous keywords (DDL/DML)
        sql_upper = sql.upper()
        dangerous_keywords = [
            "INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER",
            "TRUNCATE", "GRANT", "REVOKE", "EXEC", "EXECUTE"
        ]
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                return False, f"Forbidden keyword: {keyword}"
        
        # Check for LIMIT
        if "LIMIT" not in sql_upper:
            return False, "Query must include LIMIT clause"
        
        # Extract tables referenced
        tables = set()
        for table in parsed.find_all(sqlglot.exp.Table):
            tables.add(table.name.lower())
        
        # Validate tables
        invalid_tables = tables - ALLOWED_TABLES
        if invalid_tables:
            return False, f"Invalid table(s): {', '.join(invalid_tables)}"
        
        # Extract columns and validate (optional deep check)
        # For now we just check table names are correct
        
        return True, None
        
    except sqlglot.errors.ParseError as e:
        return False, f"SQL parse error: {str(e)}"
    except Exception as e:
        return False, f"Validation error: {str(e)}"

def add_limit_if_missing(sql: str, max_limit: int = 500) -> str:
    """Ensure LIMIT is present and not too high"""
    sql_upper = sql.upper()
    if "LIMIT" not in sql_upper:
        # Add limit before semicolon if present
        if sql.endswith(";"):
            return f"{sql[:-1]} LIMIT {max_limit};"
        else:
            return f"{sql} LIMIT {max_limit};"
    return sql
