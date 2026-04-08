# Complete Flow: User Message to Response

## 1. Frontend (User sends message)

**File:** `frontend/src/chatbot/FloatingChatbot.jsx`

1. **User types message** → `ask()` function triggered
2. **Get/Create session ID** from localStorage
3. **Prepare payload:**
   ```javascript
   {
     question: "Show me top 5 states by anger",
     session_id: "session_123...",
     current_page: "emotion_map" // from Navigation component
   }
   ```
4. **POST request** to `http://localhost:9000/chat`
5. **Wait for response** (with AbortController for cancellation)

---

## 2. Backend API Server (Entry Point)

**File:** `backend/src/api_server.py`

### Route: `POST /chat`

1. **Extract request data:**
   - `question`: User's query
   - `session_id`: Session identifier
   - `current_page`: Current UI page (emotion_map, analytics, etc.)

2. **Intent Classification** (`classify_intent_smart()`)
   - Uses LLM (`OLLAMA_MODEL_INTENT`) to classify:
     - `data_query`: User wants data/analytics
     - `rag_query`: User needs UI help
     - `smalltalk`: Casual conversation
   - Fast path: Greetings skip LLM call

3. **Route based on intent:**
   - `data_query` → `handle_data_query()`
   - `rag_query` → `handle_rag_query()`
   - `smalltalk` → `handle_smalltalk()`

---

## 3. Data Query Handler

**File:** `backend/src/api_server.py` → `handle_data_query()`

### Step 1: Check LangChain Pipeline (if enabled)

```python
if use_langchain:
    # Use LangChain analytics pipeline
    memory = langchain_memory_store[session_id]  # Get conversation memory
    result = run_analytics_pipeline(question, memory, current_page)
    return result
```

### Step 2: Fallback to Legacy Pipeline (if LangChain disabled/fails)

1. **Context Detection** (`detect_contextual_followup()`)
   - Checks if question is follow-up ("plot it", "get complete data")
   - Returns previous query context if detected

2. **SQL Generation** (`generate_sql()`)
   - Uses NL2SQL provider (Gemini or Ollama)
   - Model: `OLLAMA_MODEL_NL2SQL` or `GEMINI_MODEL_NL2SQL`
   - Includes schema context, guardrails, error feedback

3. **SQL Validation & Auto-Fix:**
   - `add_limit_if_missing()`: Ensures LIMIT clause
   - `ensure_group_by()`: Adds missing GROUP BY columns
   - `ensure_order_by_in_select()`: Adds missing aggregates to SELECT
   - `fix_order_by_alias_references()`: **NEW** Fixes alias references in ORDER BY
   - `validate_sql()`: Safety checks (no DELETE, INSERT, etc.)

4. **Execute SQL** (`run_sql()`)
   - Connects to PostgreSQL
   - Executes query
   - Returns rows as list of dicts

5. **Chart Selection** (`infer_chart_type()`)
   - Uses LLM (`OLLAMA_MODEL_CHART`) to suggest chart type
   - Returns: `{chart_type, suggest_filters, filter_types}`
   - Auto-detects filters based on data structure

6. **Auto-visualization Decision** (`should_auto_visualize()`)
   - Microsoft Fabric-inspired: Decides if modal should auto-open

7. **Natural Language Response** (`generate_nl_response()`)
   - Uses LLM (`OLLAMA_MODEL_NL_RESPONSE`) to generate user-friendly message

8. **Return Response:**
   ```python
   {
     "sql": "...",
     "rows": [...],
     "chart_hint": "radar_chart",
     "chart_filters": ["emotion", "state"],
     "auto_show_viz": true,
     "message": "Based on the data...",
     "notice": None
   }
   ```

---

## 4. LangChain Analytics Pipeline (Advanced Flow)

**File:** `backend/src/chatbot_api/langchain_chain.py` → `run_analytics_pipeline()`

### Step 1: Context Detection
- Check `memory.last_query_context` for recent query
- Check `memory.chat_history` for conversation context
- Detect visualization requests ("plot it", "chart it")

### Step 2: Early Exit (if visualization request)
- Return previous results instantly (no new SQL)

### Step 3: Query Complexity Analysis
- `_analyze_query_complexity()`: Classifies as low/medium/high
- Adjusts SQL generation strategy

### Step 4: SQL Generation with Retry
- `generate_sql_with_retry()`: 3 attempts max
- Uses validation feedback to improve
- Complexity-aware prompts
- Falls back Gemini → Ollama if needed

### Step 5: Query Optimization
- `add_limit_if_missing()`
- `ensure_group_by()`
- `ensure_order_by_in_select()`
- `fix_order_by_alias_references()`: **NEW** Fixes PostgreSQL alias issue

### Step 6: Execute SQL
- `run_sql()`: Execute and get results

### Step 7: Parallel Processing
- **Chart Selection** + **NL Response** run simultaneously (faster!)

### Step 8: Auto-visualization Decision
- `should_auto_visualize()`: Microsoft Fabric-inspired logic

### Step 9: Update Memory
- Store query context for next request
- Add to chat history

---

## 5. Frontend Response Handling

**File:** `frontend/src/chatbot/FloatingChatbot.jsx`

1. **Parse response:**
   ```javascript
   {
     sql: "...",
     rows: [...],
     chart_hint: "radar_chart",
     chart_filters: ["emotion", "state"],
     auto_show_viz: true,
     message: "..."
   }
   ```

2. **Add to chat history:**
   - User message
   - Bot response (with SQL, rows, chart hint)

3. **Auto-open modal** (if `auto_show_viz === true`):
   - Opens SQL details modal
   - Auto-expands visualization section
   - Shows chart with filters (if `chart_filters` provided)

4. **Render chart** (`ChartRenderer` component):
   - Detects chart type from `chart_hint`
   - Renders filter controls (if `filters` array provided)
   - Applies filters in real-time
   - Updates chart dynamically

---

## Key Files & Functions

### Backend
- `api_server.py`: Main API routes, intent classification, routing
- `langchain_chain.py`: Advanced analytics pipeline with memory
- `services/validator.py`: SQL validation & auto-fix (including alias fixes)
- `services/chart_llm.py`: Intelligent chart selection with filter detection
- `services/intent_classifier.py`: Intent classification
- `services/nl_response.py`: Natural language response generation
- `services/db.py`: Database connection & SQL execution

### Frontend
- `FloatingChatbot.jsx`: Main chatbot UI, message handling, chart rendering
- `ChartRenderer`: Smart chart rendering with filter controls

---

## Error Handling Flow

1. **SQL Generation fails** → Retry up to 3 times with feedback
2. **SQL Validation fails** → Return human-friendly error message
3. **SQL Execution fails** → Return "Query engine is busy" message
4. **Chart selection fails** → Fall back to rule-based detection
5. **LLM fails** → Fall back to backup model (Gemini → Ollama)

---

## Memory & Context

- **Session-based memory**: Each session has its own `AnalyticsMemory`
- **Last query context**: Stores SQL, rows, chart hint for follow-ups
- **Chat history**: Full conversation for context-aware responses
- **Context detection**: Detects "plot it", "get complete data", etc.

---

## SQL Auto-Fix Pipeline (Foolproof Chain)

1. **Missing LIMIT** → Auto-add LIMIT 500
2. **Missing GROUP BY** → Auto-add non-aggregate columns
3. **Missing aggregates in SELECT** → Auto-add to SELECT when used in ORDER BY
4. **Alias in ORDER BY** → **NEW** Expand alias to full expression (PostgreSQL doesn't allow aliases)
   - Example: `ORDER BY diff` → `ORDER BY ABS(x - y)`
   - Handles complex expressions: `ORDER BY (a + b)` → `ORDER BY ((ABS(x-y)) + (ABS(z-w)))`
5. **Validation** → Safety checks (no dangerous operations)

**All fixes are applied automatically - no user intervention needed!**

