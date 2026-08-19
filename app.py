import streamlit as st
from sql_chatbot import generate_sql, execute_query

st.set_page_config(page_title="CRM SQL Chatbot", page_icon="🤖")
st.markdown("""
<style>
.stApp {
    background: linear-gradient(to bottom right, #f0f4f8, #d9e2ec);
}

div[data-testid="stTextInput"] input {
    border: 2px solid #4F8BF9;
    border-radius: 8px;
    padding: 10px;
}

div.stButton > button {
    background-color: #4F8BF9;
    color: white;
    border-radius: 8px;
    border: none;
    padding: 8px 24px;
    font-weight: 600;
}

div.stButton > button:hover {
    background-color: #3a6fd8;
    color: white;
}

div[data-testid="stCodeBlock"] {
    border: 1px solid #4F8BF9;
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)
st.title("🤖 CRM Sales Data — Ask in Plain English")
st.write("Ask a question about the CRM sales data, and I'll write and run the SQL for you.")

# Text input box
user_question = st.text_input("Your question:", placeholder="e.g. Which region has the highest revenue?")

if st.button("Ask"):
    if user_question.strip() == "":
        st.warning("Please type a question first.")
    else:
        with st.spinner("Generating SQL..."):
            sql = generate_sql(user_question)

        st.subheader("Generated SQL")
        st.code(sql, language="sql")

        with st.spinner("Running query..."):
            result, status = execute_query(sql)

        st.subheader("Result")
        if result:
            st.success(status)
            st.dataframe(
                data=result["rows"],
                column_config=None,
                hide_index=True
            )
            # Better display using column names properly:
            import pandas as pd
            df = pd.DataFrame(result["rows"], columns=result["columns"])
            st.dataframe(df, hide_index=True)
        else:
            st.error(status)