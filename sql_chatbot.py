from google import genai
import psycopg2

# --- Configuration ---
client = genai.Client(api_key="YOUR_API_KEY_HERE")

DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "dbname": "crm_sales_db",
    "user": "postgres",
    "password": "enter your db password"
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)


# --- Schema context given to the AI ---
SCHEMA_CONTEXT = """
Table: opportunities
Columns:
- deal_id (text, primary key)
- company_name (text)
- region (text) — values: North, South, East, West, Central
- industry (text) — values: Retail, Manufacturing, Healthcare, IT Services, Finance, Education
- lead_source (text) — values: Website, Referral, Cold Call, Trade Show, Partner, Social Media
- sales_rep (text)
- stage (text) — values: Prospecting, Qualification, Proposal, Negotiation, Closed Won, Closed Lost
- amount_usd (numeric) — deal value in USD
- created_date (date) — when the deal was created
- close_date (date) — when the deal closed, NULL if still open
- is_won (boolean)
- sales_cycle_days (numeric) — days between created_date and close_date, NULL if still open
"""


# --- Step 1: Ask the AI to turn a question into SQL ---
def generate_sql(user_question):
    prompt = f"""You are a PostgreSQL expert. Given the database schema below, 
write a single valid PostgreSQL query that answers the user's question.

{SCHEMA_CONTEXT}

Rules:
- Return ONLY the SQL query, no explanation, no markdown formatting, no ```sql tags
- Only generate SELECT statements — never INSERT, UPDATE, DELETE, or DROP
- Use proper PostgreSQL syntax

User question: {user_question}

SQL query:"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )
    sql_query = response.text.strip()
    sql_query = sql_query.replace("```sql", "").replace("```", "").strip()

    return sql_query


# --- Step 2: Safety guardrail — only allow SELECT queries ---
def is_safe_query(sql_query):
    """Only allow SELECT statements — block anything that could modify or delete data."""
    forbidden_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "CREATE"]
    sql_upper = sql_query.upper()

    if not sql_upper.strip().startswith("SELECT"):
        return False, "Query does not start with SELECT — blocked for safety."

    for keyword in forbidden_keywords:
        if keyword in sql_upper:
            return False, f"Query contains forbidden keyword '{keyword}' — blocked for safety."

    return True, "Safe"


# --- Step 3: Execute the (safe) query against the real database ---
def execute_query(sql_query):
    is_safe, message = is_safe_query(sql_query)
    if not is_safe:
        return None, message

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(sql_query)

        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()

        cursor.close()
        conn.close()

        return {"columns": columns, "rows": rows}, "Success"
    except Exception as e:
        return None, f"Database error: {str(e)}"


# --- Test run ---
if __name__ == "__main__":
    conn = get_db_connection()
    print("Connected successfully:", conn)
    conn.close()
    print()

    question = "Which region has the highest total revenue from closed won deals?"
    sql = generate_sql(question)
    print("Generated SQL:\n", sql)

    result, status = execute_query(sql)
    print("\nStatus:", status)
    if result:
        print("Columns:", result["columns"])
        print("Rows:", result["rows"])