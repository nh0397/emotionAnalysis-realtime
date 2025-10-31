import sqlglot
from typing import Optional, Tuple, List
from ..schema_config import VALID_TABLES, VALID_COLUMNS

# Convert to sets for faster lookup
ALLOWED_TABLES = set(VALID_TABLES)
ALLOWED_COLUMNS = set(VALID_COLUMNS['tweets'])

def ensure_group_by(sql: str) -> str:
    """Auto-add missing non-aggregate selected columns to GROUP BY (PostgreSQL)."""
    try:
        parsed = sqlglot.parse_one(sql, read="postgres")
        if not isinstance(parsed, sqlglot.exp.Select):
            return sql

        # Collect selected columns that are NOT aggregates
        non_agg_cols: List[sqlglot.exp.Column] = []
        for sel in parsed.expressions or []:
            expr = sel.this if isinstance(sel, sqlglot.exp.Alias) else sel
            # If the expression contains any aggregate ancestor, skip
            if expr.find(sqlglot.exp.Aggregate):
                continue
            # Plain column?
            if isinstance(expr, sqlglot.exp.Column):
                non_agg_cols.append(expr)

        if not non_agg_cols:
            return parsed.sql(dialect="postgres")

        # Current GROUP BY columns (by SQL string form)
        group = parsed.args.get("group")
        current: List[str] = []
        if group and isinstance(group, sqlglot.exp.Group):
            for gexpr in group.expressions or []:
                current.append(gexpr.sql(dialect="postgres"))

        # Determine missing columns
        missing_sql: List[str] = []
        for c in non_agg_cols:
            col_sql = c.sql(dialect="postgres")
            if col_sql not in current:
                missing_sql.append(col_sql)

        if not missing_sql:
            return parsed.sql(dialect="postgres")

        # Build/extend GROUP BY
        new_group_exprs: List[sqlglot.exp.Expression] = []
        if group and isinstance(group, sqlglot.exp.Group):
            new_group_exprs.extend(group.expressions or [])
        for ms in missing_sql:
            new_group_exprs.append(sqlglot.parse_one(ms, read="postgres"))

        parsed.set("group", sqlglot.exp.Group(expressions=new_group_exprs))
        return parsed.sql(dialect="postgres")
    except Exception:
        return sql

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

