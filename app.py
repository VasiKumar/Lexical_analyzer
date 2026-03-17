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

VALID_ESCAPES = {"\\n","\\t","\\\\","\\'","\\\""}

# -----------------------------
# Comment Remover
# -----------------------------

def remove_comments(code, language):

    if language == "Python":
        code = re.sub(r'#.*', '', code)

    elif language == "Java":
        code = re.sub(r'//.*', '', code)
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)

    return code


# -----------------------------
# Tokenizer (Improved)
# -----------------------------

def tokenize(code):

    token_pattern = r'"[^"\n]*"?|\d+\.\d+\.\d+|\d+\.\d+|\d+|==|!=|<=|>=|\*\*|//|[A-Za-z_][A-Za-z0-9_]*|[^\s]'
    tokens = re.findall(token_pattern, code)

    return tokens


# -----------------------------
# Lexical Error Checks
# -----------------------------

def check_lexical_errors(token):

    # 1. Unterminated string
    if token.startswith('"') and not token.endswith('"'):
        return "Unterminated String"

    # 2. Invalid identifier (starts with number but has letters)
    if re.fullmatch(r'\d+[A-Za-z_]+[A-Za-z0-9_]*', token):
        return "Invalid Identifier"

    # 3. Invalid number format
    if re.fullmatch(r'\d+\.\d+\.\d+', token):
        return "Invalid Number"

    # 4. Invalid escape sequence
    if token.startswith('"') and token.endswith('"'):
        escapes = re.findall(r'\\.', token)
        for e in escapes:
            if e not in VALID_ESCAPES:
                return "Invalid Escape Sequence"

    # 5. Illegal character
    if re.fullmatch(r'[^\w\s]', token) and token not in OPERATORS and token not in SEPARATORS:
        return "Illegal Character"

    return None


# -----------------------------
# Token Classification
# -----------------------------

def classify_tokens(tokens, language):

    results = []
    errors = []

    keywords = JAVA_KEYWORDS if language == "Java" else PYTHON_KEYWORDS

    for token in tokens:

        error_type = check_lexical_errors(token)

        if error_type:
            token_type = f"Lexical Error ({error_type})"
            errors.append(token)

        elif token in keywords:
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
            token_type = "Lexical Error (Unknown)"
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

language = st.selectbox(
    "Select Programming Language",
    ["Python", "Java"]
)

code = st.text_area(
    "Write or paste your code",
    height=300
)

analyze = st.button("Analyze Code")

# -----------------------------
# Analysis
# -----------------------------

if analyze and code:

    clean_code = remove_comments(code, language)
    tokens = tokenize(clean_code)
    results, errors = classify_tokens(tokens, language)

    if len(results) == 0:
        st.warning("No tokens found")
    else:
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
    st.info("Enter code and click Analyze")

st.markdown("---")
st.caption("Improved Lexical Analyzer (Covers all major lexical errors)")
