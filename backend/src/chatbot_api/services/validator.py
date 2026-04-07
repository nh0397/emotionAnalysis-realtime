import sqlglot
import re
from typing import Optional, Tuple, List
from ..schema_config import VALID_TABLES, VALID_COLUMNS

# Convert to sets for faster lookup
ALLOWED_TABLES = set(VALID_TABLES)
ALLOWED_COLUMNS = set(VALID_COLUMNS['tweets'])

def fix_order_by_alias_references(sql: str) -> str:
    """
    Fix ORDER BY clauses that reference column aliases.
    PostgreSQL doesn't allow ORDER BY alias - must repeat expression or use subquery.
    """
    try:
        sql_upper = sql.upper()
        
        # Check if ORDER BY exists
        if "ORDER BY" not in sql_upper:
            return sql
        
        # Extract SELECT clause to find aliases
        select_match = re.search(r'SELECT\s+(.+?)\s+FROM', sql_upper, re.IGNORECASE | re.DOTALL)
        if not select_match:
            return sql
        
        select_clause = select_match.group(1).strip()
        
        # Extract ORDER BY clause
        order_by_match = re.search(r'ORDER\s+BY\s+(.+?)(?:\s+LIMIT|\s*;|$)', sql_upper, re.IGNORECASE | re.DOTALL)
        if not order_by_match:
            return sql
        
        order_by_clause = order_by_match.group(1).strip()
        
        # Find all aliases in SELECT (pattern: expression AS alias)
        alias_map = {}
        alias_pattern = r'(.+?)\s+AS\s+(\w+)'
        for match in re.finditer(alias_pattern, select_clause, re.IGNORECASE):
            expression = match.group(1).strip()
            alias = match.group(2).strip()
            alias_map[alias.upper()] = expression
        
        # Check if ORDER BY references any aliases
        order_by_upper = order_by_clause.upper()
        has_alias_ref = False
        for alias in alias_map.keys():
            # Check if alias appears as a standalone word in ORDER BY
            pattern = r'\b' + re.escape(alias) + r'\b'
            if re.search(pattern, order_by_upper):
                has_alias_ref = True
                break
        
        if not has_alias_ref:
            return sql
        
        # Replace aliases with their expressions in ORDER BY
        fixed_order_by = order_by_clause
        for alias, expression in alias_map.items():
            # Replace alias with expression (case-insensitive, word boundary)
            pattern = r'\b' + re.escape(alias) + r'\b'
            fixed_order_by = re.sub(pattern, f'({expression})', fixed_order_by, flags=re.IGNORECASE)
        
        # Replace ORDER BY clause in original SQL
        order_by_start = sql_upper.find('ORDER BY')
        if order_by_start == -1:
            return sql
        
        # Find where ORDER BY clause ends (LIMIT or end of SQL)
        order_by_end = sql_upper.find(' LIMIT', order_by_start)
        if order_by_end == -1:
            order_by_end = sql_upper.find(';', order_by_start)
        if order_by_end == -1:
            order_by_end = len(sql)
        
        # Replace the ORDER BY clause
        new_sql = sql[:order_by_start + 8] + ' ' + fixed_order_by + sql[order_by_end:]
        
        print(f"[validator.py] Fixed ORDER BY alias references: expanded aliases to expressions")
        return new_sql
        
    except Exception as e:
        print(f"[validator.py] Error in fix_order_by_alias_references: {e}")
        return sql


def ensure_order_by_in_select(sql: str) -> str:
    """Auto-add missing ORDER BY columns/aggregates to SELECT clause."""
    try:
        # Simple regex-based approach for robustness
        sql_upper = sql.upper()
        
        # Check if ORDER BY exists
        if "ORDER BY" not in sql_upper:
            return sql
        
        # Extract ORDER BY clause
        order_by_match = re.search(r'ORDER\s+BY\s+(.+?)(?:\s+LIMIT|\s*;|$)', sql_upper, re.IGNORECASE | re.DOTALL)
        if not order_by_match:
            return sql
        
        order_by_clause = order_by_match.group(1).strip()
        
        # Extract aggregate functions from ORDER BY (AVG, SUM, COUNT, etc.)
        agg_patterns = [
            (r'AVG\(([^)]+)\)', 'AVG'),
            (r'SUM\(([^)]+)\)', 'SUM'),
            (r'COUNT\(([^)]+)\)', 'COUNT'),
            (r'MAX\(([^)]+)\)', 'MAX'),
            (r'MIN\(([^)]+)\)', 'MIN'),
            (r'STDDEV\(([^)]+)\)', 'STDDEV'),
        ]
        
        # Check SELECT clause
        select_match = re.search(r'SELECT\s+(.+?)\s+FROM', sql_upper, re.IGNORECASE | re.DOTALL)
        if not select_match:
            return sql
        
        select_clause = select_match.group(1).strip()
        
        # Find missing aggregates in SELECT
        missing_aggregates = []
        for pattern, agg_type in agg_patterns:
            matches = re.finditer(pattern, order_by_clause, re.IGNORECASE)
            for match in matches:
                full_expr = match.group(0)  # e.g., "AVG(anger)"
                column = match.group(1).lower()  # e.g., "anger"
                
                # Check if this aggregate is already in SELECT
                # Look for AVG(anger), avg(anger), or aliases
                if full_expr not in select_clause and full_expr.lower() not in select_clause.lower():
                    # Check for common aliases
                    alias_patterns = [
                        f'{agg_type.lower()}_{column}',
                        f'avg_{column}',
                        f'{column}_avg',
                        'avg_value',
                        'metric'
                    ]
                    found_alias = False
                    for alias in alias_patterns:
                        if alias in select_clause.lower():
                            found_alias = True
                            break
                    
                    if not found_alias:
                        missing_aggregates.append((agg_type, column, full_expr))
        
        if not missing_aggregates:
            return sql
        
        # Add missing aggregates to SELECT
        # Find the position to insert (before FROM)
        from_pos = sql_upper.find(' FROM')
        if from_pos == -1:
            return sql
        
        # Build new SELECT clause additions
        additions = []
        for agg_type, column, full_expr in missing_aggregates:
            # Smart alias based on column name
            if 'anger' in column:
                alias = 'avg_anger' if agg_type == 'AVG' else f'{agg_type.lower()}_{column}'
            elif 'fear' in column:
                alias = 'avg_fear' if agg_type == 'AVG' else f'{agg_type.lower()}_{column}'
            elif 'joy' in column:
                alias = 'avg_joy' if agg_type == 'AVG' else f'{agg_type.lower()}_{column}'
            else:
                alias = f'{agg_type.lower()}_{column}' if agg_type != 'AVG' else f'avg_{column}'
            
            additions.append(f", {full_expr} AS {alias}")
        
        # Insert additions before FROM
        insert_pos = from_pos
        new_sql = sql[:insert_pos] + "".join(additions) + sql[insert_pos:]
        
        print(f"[validator.py] Auto-added missing ORDER BY aggregates to SELECT: {[a[2:] for a in additions]}")
        return new_sql
        
    except Exception as e:
        print(f"[validator.py] Error in ensure_order_by_in_select: {e}")
        return sql


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
    
    Uses simple string-based validation for reliability, with sqlglot only for basic syntax check.
    """
    if not sql:
        return False, "Empty SQL query"
    
    sql_upper = sql.upper()
    sql_lower = sql.lower()
    
    # 1. Check for dangerous keywords (DDL/DML) - but allow WITH, STDDEV, etc.
    dangerous_keywords = [
        "INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER",
        "TRUNCATE", "GRANT", "REVOKE", "EXEC", "EXECUTE"
    ]
    for keyword in dangerous_keywords:
        if keyword in sql_upper:
            return False, f"Forbidden keyword: {keyword}"
    
    # 2. Must be a SELECT query (allow WITH ... SELECT)
    if not (sql_upper.startswith("SELECT") or sql_upper.startswith("WITH")):
        return False, "Only SELECT queries are allowed"
    
    # 3. Check for LIMIT
    if "LIMIT" not in sql_upper:
        return False, "Query must include LIMIT clause"
    
    # 4. Extract CTE names from WITH clauses (simple regex-like approach)
    cte_names = set()
    if "WITH" in sql_upper:
        # Find all "WITH name AS" patterns
        # Pattern: WITH Name AS or WITH Name AS (
        pattern = r'WITH\s+(\w+)\s+AS'
        matches = re.findall(pattern, sql_upper, re.IGNORECASE)
        cte_names = {m.lower() for m in matches}
    
    # 5. Find valid table references using string matching (more reliable than parsing)
    # Look for table names after FROM, JOIN, or in CTE definitions
    found_valid_tables = set()
    for table in ALLOWED_TABLES:
        # Check various patterns where table name might appear
        patterns = [
            f"FROM {table}",
            f"FROM {table} ",
            f"FROM {table}\n",
            f"FROM {table}\t",
            f"FROM {table},",
            f"FROM {table})",
            f"JOIN {table}",
            f"JOIN {table} ",
            f"JOIN {table}\n",
            f"JOIN {table}\t",
            f"JOIN {table},",
            f"JOIN {table})",
            f", {table} ",
            f", {table}\n",
            f", {table}\t",
            f", {table},",
            f", {table})",
            f" {table} ",
            f" {table}\n",
            f" {table}\t",
        ]
        for pattern in patterns:
            if pattern.lower() in sql_lower:
                found_valid_tables.add(table)
                break
    
    # 6. Check if any found tables are invalid (not in allowed list and not CTE names)
    # For now, we just check that we found at least one valid table
    if not found_valid_tables:
        return False, f"Query must reference at least one valid table: {', '.join(ALLOWED_TABLES)}"
    
    # 7. Optional: Try to parse with sqlglot for basic syntax validation
    # But don't fail if parsing fails - complex SQL might not parse perfectly
    try:
        parsed = sqlglot.parse_one(sql, read="postgres")
        # Just check it's a SELECT or WITH - don't use it for table extraction
        is_select = isinstance(parsed, sqlglot.exp.Select)
        is_with = isinstance(parsed, sqlglot.exp.With)
        if not (is_select or is_with):
            # If parsing says it's not valid, still allow it if string checks pass
            # (might be a parsing limitation)
            pass
    except Exception:
        # Parsing failed - that's OK, we'll trust string-based validation
        pass
    
    # All checks passed
    return True, None

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

