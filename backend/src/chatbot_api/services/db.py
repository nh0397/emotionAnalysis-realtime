import psycopg
import os
from typing import List, Dict, Optional, Tuple

def get_db_connection():
    """Create a psycopg connection to the database"""
    return psycopg.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=int(os.getenv("PGPORT", 5432)),
        user=os.getenv("PGUSER", "tweetuser"),
        password=os.getenv("PGPASSWORD", "tweetpass"),
        dbname=os.getenv("PGDATABASE", "tweetdb")
    )

def run_sql(sql: str, timeout: Optional[int] = 10) -> Tuple[List[Dict], Optional[str]]:
    """
    Execute SQL query safely and return results.
    Returns: (rows, error_message)
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Set statement timeout only if specified
                if timeout is not None:
                    cur.execute(f"SET statement_timeout = '{timeout}s'")
                
                # Execute query
                cur.execute(sql)
                
                # Fetch results
                columns = [desc[0] for desc in cur.description] if cur.description else []
                rows = cur.fetchall()
                
                # Convert to list of dicts
                result = [dict(zip(columns, row)) for row in rows]
                
                return result, None
                
    except psycopg.errors.QueryCanceled:
        return [], f"Query timeout after {timeout}s"
    except psycopg.Error as e:
        return [], f"Database error: {str(e)}"
    except Exception as e:
        return [], f"Execution error: {str(e)}"

def check_explain_cost(sql: str, max_cost: float = 10000.0) -> Tuple[bool, Optional[str]]:
    """
    Run EXPLAIN to check query cost before execution.
    Returns: (is_safe, error_message)
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"EXPLAIN {sql}")
                plan = cur.fetchall()
                
                # Parse first line for cost estimate
                if plan and len(plan) > 0:
                    first_line = str(plan[0][0])
                    # Extract cost from "cost=X..Y"
                    if "cost=" in first_line:
                        cost_part = first_line.split("cost=")[1].split("..")[1].split(" ")[0]
                        estimated_cost = float(cost_part)
                        
                        if estimated_cost > max_cost:
                            return False, f"Query too expensive (cost: {estimated_cost:.0f})"
                
                return True, None
                
    except Exception as e:
        # If EXPLAIN fails, be conservative and reject
        return False, f"Cost check failed: {str(e)}"
