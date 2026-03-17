import streamlit as st
import pandas as pd
import re

# -----------------------------
# Page Config
# -----------------------------
st.set_page_config(page_title="Lexical Analyzer (CD Theory)", layout="wide")
st.title("🧠 Lexical Analyzer — Compiler Design Theory")

st.write("""
This analyzer strictly follows **Compiler Design: Lexical Analysis rules**.
It detects tokens and lexical errors in Python and Java code, using strict **maximal munch** rules.
""")

# -----------------------------
# Language Keywords, Operators, Separators
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
# Remove Comments
# -----------------------------
def remove_comments(code, language):
    if language == "Python":
        code = re.sub(r'#.*', '', code)
    elif language == "Java":
        code = re.sub(r'//.*', '', code)
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
    return code

# -----------------------------
# Token Patterns
# Strict Maximal Munch Order
# -----------------------------
TOKEN_PATTERNS = [
    ('String', r'"([^"\\]|\\.)*"'),
    ('Float', r'\d+\.\d+'),
    ('Integer', r'\d+'),
    ('Identifier', r'[A-Za-z_][A-Za-z0-9_]*'),
    ('Operator', r'==|!=|<=|>=|\*\*|//|[+\-*/=<>%]'),
    ('Separator', r'[;,()\[\]{}.:]'),
    ('Unknown', r'.'),
]

# -----------------------------
# Tokenizer with Line & Column and Strict Maximal Munch
# -----------------------------
def tokenize(code):
    tokens = []
    idx = 0
    line = 1
    col = 1
    while idx < len(code):
        char = code[idx]
        if char == '\n':
            line += 1
            col = 1
            idx += 1
            continue
        if char.isspace():
            idx += 1
            col += 1
            continue

        match_found = False
        for tok_type, pattern in TOKEN_PATTERNS:
            regex = re.compile(pattern)
            m = regex.match(code, idx)
            if m:
                tok_val = m.group()

                # Strict Identifier check: cannot start with digit
                if tok_type == 'Identifier' and tok_val[0].isdigit():
                    tokens.append({'value': tok_val, 'type': 'Lexical Error (Invalid Identifier)', 'line': line, 'col': col})
                # Float check: multiple dots invalid
                elif tok_type == 'Float' and tok_val.count('.') != 1:
                    tokens.append({'value': tok_val, 'type': 'Lexical Error (Invalid Number)', 'line': line, 'col': col})
                # String check: unterminated
                elif tok_type == 'String' and not tok_val.endswith('"'):
                    tokens.append({'value': tok_val, 'type': 'Lexical Error (Unterminated String)', 'line': line, 'col': col})
                else:
                    tokens.append({'value': tok_val, 'type': tok_type, 'line': line, 'col': col})

                idx += len(tok_val)
                col += len(tok_val)
                match_found = True
                break

        if not match_found:
            tokens.append({'value': char, 'type': 'Lexical Error (Illegal Character)', 'line': line, 'col': col})
            idx += 1
            col += 1

    return tokens

# -----------------------------
# Lexical Error Refinement & Final Classification
# -----------------------------
def classify_token(tok, language):
    val = tok['value']
    tok_type = tok['type']
    keywords = JAVA_KEYWORDS if language=="Java" else PYTHON_KEYWORDS

    # Keywords override Identifier
    if tok_type == 'Identifier' and val in keywords:
        return 'Keyword'

    # String: validate escape sequences
    if tok_type == 'String':
        escapes = re.findall(r'\\.', val)
        for e in escapes:
            if e not in VALID_ESCAPES:
                return 'Lexical Error (Invalid Escape Sequence)'
        return 'String'

    # Float & Integer: extra numeric check
    if tok_type == 'Float':
        if val.count('.') != 1 or re.search(r'[^\d.]', val):
            return 'Lexical Error (Invalid Number)'
        return 'Float'
    if tok_type == 'Integer':
        return 'Integer'

    # Operator & Separator
    if tok_type == 'Operator':
        return 'Operator'
    if tok_type == 'Separator':
        return 'Separator'

    # Already flagged Lexical Error or Unknown
    if 'Lexical Error' in tok_type or tok_type == 'Unknown':
        return tok_type

    # Identifier
    return 'Identifier'

# -----------------------------
# Streamlit UI Inputs
# -----------------------------
language = st.selectbox("Select Language", ["Python", "Java"])
code = st.text_area("Enter your code", height=400, placeholder="Paste your code here...")
analyze = st.button("Analyze Code")

# -----------------------------
# Full Analysis
# -----------------------------
if analyze and code:
    clean_code = remove_comments(code, language)
    raw_tokens = tokenize(clean_code)
    results = []
    errors = []

    for tok in raw_tokens:
        final_type = classify_token(tok, language)
        results.append({
            'Token': tok['value'],
            'Type': final_type,
            'Line': tok['line'],
            'Column': tok['col']
        })
        if 'Lexical Error' in final_type:
            errors.append(tok)

    df = pd.DataFrame(results)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Token Classification")
        st.dataframe(df, use_container_width=True)
    with col2:
        st.subheader("Token Statistics")
        st.bar_chart(df['Type'].value_counts())

    st.subheader("Lexical Errors")
    if errors:
        st.error(f"{len(errors)} lexical error(s) detected")
        for e in errors:
            st.write(f"❌ {e['value']} (Line {e['line']}, Col {e['col']})")
    else:
        st.success("No lexical errors detected")

    st.write("Total Tokens:", len(raw_tokens))
else:
    st.info("Enter code and click Analyze")

st.markdown("---")
st.caption("Lexical Analyzer built for Compiler Design Theory — Python + Java")
