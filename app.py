import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Lexical Code Analyzer", layout="wide")

# -----------------------------
# Language Keyword Sets
# -----------------------------

JAVA_KEYWORDS = {
"class","public","private","protected","static","void","int","float",
"double","char","boolean","if","else","switch","case","for","while",
"do","break","continue","return","new","try","catch","finally","import"
}

PYTHON_KEYWORDS = {
"def","return","if","elif","else","for","while","break","continue",
"import","from","as","class","try","except","finally","with","lambda",
"True","False","None","pass","yield"
}

OPERATORS = {
"+","-","*","/","=","==","!=","<",">","<=",">=","%","//","**"
}

SEPARATORS = {
";",",","(",")","{","}","[","]",".",":"
}

# -----------------------------
# Tokenizer
# -----------------------------

def tokenize(code):

    token_pattern = r'"[^"]*"|\d+\.\d+|\d+|==|!=|<=|>=|\*\*|//|[A-Za-z_][A-Za-z0-9_]*|[^\s]'
    tokens = re.findall(token_pattern, code)

    return tokens


# -----------------------------
# Token Classification
# -----------------------------

def classify_tokens(tokens, language):

    results = []
    errors = []

    if language == "Java":
        keywords = JAVA_KEYWORDS
    else:
        keywords = PYTHON_KEYWORDS

    for token in tokens:

        if token in keywords:
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


# -----------------------------
# Streamlit UI
# -----------------------------

st.title("🧠 Code Lexical Analyzer")

st.write("Analyze Java or Python code for token classification and lexical errors.")

# Language dropdown
language = st.selectbox(
    "Select Programming Language",
    ["Python", "Java"]
)

# Code editor
code = st.text_area(
    "Write or paste your code",
    height=300,
    placeholder="Start typing your code here..."
)

analyze = st.button("Analyze Code")

# -----------------------------
# Analysis
# -----------------------------

if analyze and code:

    tokens = tokenize(code)
    results, errors = classify_tokens(tokens, language)

    df = pd.DataFrame(results)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Token Classification")
        st.dataframe(df, use_container_width=True)

    with col2:
        st.subheader("Token Statistics")
        stats = df["Type"].value_counts()
        st.bar_chart(stats)

    st.subheader("Error Report")

    if errors:
        st.error(f"{len(errors)} lexical error(s) detected")
        for e in errors:
            st.write("❌", e)
    else:
        st.success("No lexical errors detected")

    st.write("Total Tokens:", len(tokens))

else:
    st.info("Select a language, enter code, and click Analyze")

st.markdown("---")
st.caption("Educational Compiler Design Tool built with Streamlit")
