import streamlit as st
import pandas as pd
import re

# ---------------------------
# Language Definition
# ---------------------------

KEYWORDS = {
    "int","float","double","char","if","else","while","for","return",
    "break","continue","void","class","public","private","protected",
    "static","new","try","catch","finally","import","def","True","False"
}

OPERATORS = {
    "+","-","*","/","=","==","!=","<",">","<=",">=","%","&&","||","!"
}

SEPARATORS = {
    ";",",","(",")","{","}","[","]",".",":"
}

# ---------------------------
# Tokenizer
# ---------------------------

def tokenize(code):

    token_pattern = r'"[^"]*"|\d+\.\d+|\d+|==|!=|<=|>=|&&|\|\||[A-Za-z_][A-Za-z0-9_]*|[^\s]'

    tokens = re.findall(token_pattern, code)

    return tokens


# ---------------------------
# Token Classification
# ---------------------------

def classify_tokens(tokens):

    results = []
    errors = []

    for token in tokens:

        token_type = "Unknown"

        if token in KEYWORDS:
            token_type = "Keyword"

        elif token in OPERATORS:
            token_type = "Operator"

        elif token in SEPARATORS:
            token_type = "Separator"

        elif re.fullmatch(r'"[^"]*"', token):
            token_type = "String"

        elif re.fullmatch(r'\d+\.\d+', token):
            token_type = "Float"

        elif re.fullmatch(r'\d+', token):
            token_type = "Integer"

        elif re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', token):
            token_type = "Identifier"

        else:
            token_type = "Lexical Error"
            errors.append(token)

        results.append({
            "Token": token,
            "Type": token_type
        })

    return results, errors


# ---------------------------
# Statistics
# ---------------------------

def generate_statistics(df):

    stats = df["Type"].value_counts()

    return stats


# ---------------------------
# Streamlit UI
# ---------------------------

st.set_page_config(page_title="Code Analyzer", layout="wide")

st.title("🧠 Lexical Code Analyzer")
st.write("Analyze source code tokens, detect lexical errors, and classify elements.")

# Code editor
code = st.text_area(
    "Write your code here",
    height=300,
    placeholder="Type or paste your code..."
)

analyze = st.button("Analyze Code")

if analyze and code:

    tokens = tokenize(code)

    results, errors = classify_tokens(tokens)

    df = pd.DataFrame(results)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Token Table")
        st.dataframe(df)

    with col2:
        st.subheader("Statistics")
        stats = generate_statistics(df)
        st.bar_chart(stats)

    st.subheader("Detected Errors")

    if errors:
        st.error(f"{len(errors)} lexical error(s) found")
        for e in errors:
            st.write("❌", e)
    else:
        st.success("No lexical errors detected")

    st.subheader("Token Count")

    st.write("Total Tokens:", len(tokens))

else:
    st.info("Enter code and click Analyze")


# ---------------------------
# Footer
# ---------------------------

st.markdown("---")
st.caption("Educational Code Analyzer built with Streamlit")
