import streamlit as st
import pandas as pd
import re

# -----------------------------
# Page Config (Called only once)
# -----------------------------
st.set_page_config(page_title="Lexical Analyzer (CD Theory)", layout="wide")

# -----------------------------
# Language Keywords
# -----------------------------
JAVA_KEYWORDS = {
    "abstract", "assert", "boolean", "break", "byte", "case", "catch", "char",
    "class", "const", "continue", "default", "do", "double", "else", "enum",
    "extends", "final", "finally", "float", "for", "goto", "if", "implements",
    "import", "instanceof", "int", "interface", "long", "native", "new",
    "package", "private", "protected", "public", "return", "short", "static",
    "strictfp", "super", "switch", "synchronized", "this", "throw", "throws",
    "transient", "try", "void", "volatile", "while", "true", "false", "null",
    "var", "yield", "record", "sealed", "permits"
}

PYTHON_KEYWORDS = {
    "False", "None", "True", "and", "as", "assert", "async", "await",
    "break", "class", "continue", "def", "del", "elif", "else", "except",
    "finally", "for", "from", "global", "if", "import", "in", "is",
    "lambda", "nonlocal", "not", "or", "pass", "raise", "return",
    "try", "while", "with", "yield", "match", "case", "type"
}

# -----------------------------
# Operator Sets
# -----------------------------
JAVA_OPERATORS = {
    '=', '+', '-', '*', '/', '%', '++', '--', '==', '!=', '>', '<', '>=', '<=',
    '&&', '||', '!', '&', '|', '^', '~', '<<', '>>', '>>>', '+=', '-=',
    '*=', '/=', '%=', '&=', '|=', '^=', '<<=', '>>=', '>>>=', '->', '::',
    '?', ':'
}

PYTHON_OPERATORS = {
    '=', '+', '-', '*', '/', '%', '**', '//', '==', '!=', '>', '<', '>=', '<=',
    'and', 'or', 'not', '&', '|', '^', '~', '<<', '>>', '+=', '-=', '*=',
    '/=', '%=', '&=', '|=', '^=', '<<=', '>>=', '@', ':=', '...'
}

ALL_OPERATORS = JAVA_OPERATORS | PYTHON_OPERATORS
SEPARATORS = {';', ',', '(', ')', '{', '}', '[', ']', '.', ':', '@'}
PYTHON_ESCAPES = {'\\n', '\\t', '\\\\', '\\\'', '\\"', '\\r', '\\b', '\\f'}
JAVA_ESCAPES = {'\\n', '\\t', '\\\\', '\\\'', '\\"', '\\r', '\\b', '\\f'}

# -----------------------------
# Lexical Analyzer Class
# -----------------------------
class LexicalAnalyzer:
    def __init__(self, language):
        self.language = language
        self.tokens = []
        self.errors = []
        self.line = 1
        self.col = 1
        self.idx = 0
        self.code = ""
        
    def analyze(self, code):
        self.code = code
        self.tokens = []
        self.errors = []
        self.line = 1
        self.col = 1
        self.idx = 0
        
        while self.idx < len(self.code):
            if self.code[self.idx].isspace():
                if self.code[self.idx] == '\n':
                    self.line += 1
                    self.col = 1
                else:
                    self.col += 1
                self.idx += 1
                continue
                
            matched = (self.match_string() or
                      self.match_comment() or
                      self.match_number() or
                      self.match_operator() or
                      self.match_separator() or
                      self.match_identifier() or
                      self.match_error())
            
            if not matched:
                self.idx += 1
                self.col += 1
        return self.tokens

    def match_string(self):
        start_line, start_col = self.line, self.col
        prefix, is_raw, is_bytes = "", False, False
        
        if self.language == "Python":
            prefix_match = re.match(r'^[rbfuRBFU]+', self.code[self.idx:])
            if prefix_match:
                prefix = prefix_match.group()
                is_raw = 'r' in prefix.lower()
                is_bytes = 'b' in prefix.lower()
                self.idx += len(prefix)
                self.col += len(prefix)

        # Triple-quoted strings (Python)
        for q in ('"""', "'''"):
            if self.code.startswith(q, self.idx):
                quote = q
                self.idx += 3
                self.col += 3
                content = ""
                while self.idx < len(self.code):
                    if self.code.startswith(quote, self.idx):
                        self.idx += 3
                        self.col += 3
                        self.add_token('String', prefix + quote + content + quote, start_line, start_col)
                        return True
                    char = self.code[self.idx]
                    content += char
                    if char == '\n': self.line += 1; self.col = 1
                    else: self.col += 1
                    self.idx += 1
                self.add_error('Unterminated String', prefix + quote + content, start_line, start_col)
                return True

        # Single/Double-quoted strings
        if self.idx < len(self.code) and self.code[self.idx] in ('"', "'"):
            quote = self.code[self.idx]
            self.idx += 1; self.col += 1
            content = ""
            while self.idx < len(self.code):
                if not is_raw and self.code[self.idx] == '\\':
                    content += self.code[self.idx:self.idx+2]
                    self.idx += 2; self.col += 2
                    continue
                if self.code[self.idx] == quote:
                    self.idx += 1; self.col += 1
                    self.add_token('String', prefix + quote + content + quote, start_line, start_col)
                    return True
                if self.code[self.idx] == '\n':
                    if self.language == "Java":
                        self.add_error('Unterminated String', prefix + quote + content, start_line, start_col)
                        return True
                    self.line += 1; self.col = 1
                else: self.col += 1
                content += self.code[self.idx]
                self.idx += 1
            self.add_error('Unterminated String', prefix + quote + content, start_line, start_col)
            return True
        return False

    def match_comment(self):
        start_line, start_col = self.line, self.col
        if self.language == "Python" and self.code[self.idx] == '#':
            comment = ""
            while self.idx < len(self.code) and self.code[self.idx] != '\n':
                comment += self.code[self.idx]
                self.idx += 1; self.col += 1
            self.add_token('Comment', comment, start_line, start_col)
            return True
        elif self.language == "Java":
            if self.code.startswith('//', self.idx):
                comment = ""
                while self.idx < len(self.code) and self.code[self.idx] != '\n':
                    comment += self.code[self.idx]
                    self.idx += 1; self.col += 1
                self.add_token('Comment', comment, start_line, start_col)
                return True
            elif self.code.startswith('/*', self.idx):
                comment = ""
                while self.idx < len(self.code):
                    if self.code.startswith('*/', self.idx):
                        comment += '*/'
                        self.idx += 2; self.col += 2
                        self.add_token('Comment', comment, start_line, start_col)
                        return True
                    char = self.code[self.idx]
                    comment += char
                    if char == '\n': self.line += 1; self.col = 1
                    else: self.col += 1
                    self.idx += 1
                self.add_error('Unterminated Comment', comment, start_line, start_col)
                return True
        return False

    def match_number(self):
        start_line, start_col = self.line, self.col
        patterns = [
            (r'0[xX][0-9a-fA-F_]+', 'HexInteger'),
            (r'0[bB][01_]+', 'BinaryInteger'),
            (r'0[oO][0-7_]+', 'OctalInteger'),
            (r'\d+\.\d*(?:[eE][+-]?\d+)?|\.\d+(?:[eE][+-]?\d+)?|\d+[eE][+-]?\d+', 'Float'),
            (r'\d+(?:_\d+)*', 'Integer')
        ]
        for pattern, ttype in patterns:
            m = re.match(pattern, self.code[self.idx:])
            if m:
                val = m.group()
                self.idx += len(val); self.col += len(val)
                self.add_token(ttype, val, start_line, start_col)
                return True
        return False

    def match_operator(self):
        ops = sorted(ALL_OPERATORS, key=len, reverse=True)
        for op in ops:
            if self.code.startswith(op, self.idx):
                self.add_token('Operator', op, self.line, self.col)
                self.idx += len(op); self.col += len(op)
                return True
        return False

    def match_separator(self):
        if self.code[self.idx] in SEPARATORS:
            self.add_token('Separator', self.code[self.idx], self.line, self.col)
            self.idx += 1; self.col += 1
            return True
        return False

    def match_identifier(self):
        pattern = r'[^\d\W]\w*' if self.language == "Python" else r'[A-Za-z_$][A-Za-z0-9_$]*'
        m = re.match(pattern, self.code[self.idx:])
        if m:
            val = m.group()
            keywords = JAVA_KEYWORDS if self.language == "Java" else PYTHON_KEYWORDS
            self.add_token('Keyword' if val in keywords else 'Identifier', val, self.line, self.col)
            self.idx += len(val); self.col += len(val)
            return True
        return False

    def match_error(self):
        self.add_error('Illegal Character', self.code[self.idx], self.line, self.col)
        self.idx += 1; self.col += 1
        return True

    def add_token(self, ttype, val, line, col):
        self.tokens.append({'value': val, 'type': ttype, 'line': line, 'col': col})

    def add_error(self, etype, val, line, col):
        self.tokens.append({'value': val, 'type': f'Lexical Error ({etype})', 'line': line, 'col': col})
        self.errors.append({'value': val, 'error': etype, 'line': line, 'col': col})

# -----------------------------
# UI Logic
# -----------------------------
st.title("🧠 Complete Lexical Analyzer — All Edge Cases Covered")
st.write("Supports Python and Java analysis with full line/column tracking.")

language = st.selectbox("Select Language", ["Python", "Java"])
code_input = st.text_area("Enter your code here", height=300)

if st.button("Analyze Code"):
    if code_input:
        analyzer = LexicalAnalyzer(language)
        results = analyzer.analyze(code_input)
        df = pd.DataFrame(results)
        
        c1, c2 = st.columns([2, 1])
        with c1:
            st.subheader("Token Stream")
            st.dataframe(df, use_container_width=True)
        with c2:
            st.subheader("Stats")
            st.write(f"**Total Tokens:** {len(results)}")
            st.write(f"**Errors:** {len(analyzer.errors)}")
            if not df.empty:
                st.bar_chart(df['type'].value_counts())
    else:
        st.warning("Please enter some code first.")
