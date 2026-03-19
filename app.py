import streamlit as st
import pandas as pd
import re

# -----------------------------
# Page Config
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
# Operator Sets — strictly separated by language
# NOTE: 'and', 'or', 'not' are Python keyword-operators; handled via keyword
#       matching so they are NOT listed as operator symbols here.
# -----------------------------
JAVA_OPERATORS = {
    '>>>=', '>>=', '<<=',
    '**', '//', '==', '!=', '>=', '<=', '&&', '||', '++', '--',
    '+=', '-=', '*=', '/=', '%=', '&=', '|=', '^=', '<<', '>>', '>>>',
    '->', '::',
    '=', '+', '-', '*', '/', '%', '>', '<',
    '!', '&', '|', '^', '~',
    '?', ':'
}

PYTHON_OPERATORS = {
    '<<=', '>>=',
    '**', '//', '==', '!=', '>=', '<=', '<<', '>>',
    '+=', '-=', '*=', '/=', '%=', '&=', '|=', '^=', '**=', '//=', '@=',
    ':=', '...',
    '=', '+', '-', '*', '/', '%', '>', '<',
    '&', '|', '^', '~', '@'
}

# Separators are also language-specific
# '@' is Python-only (decorator prefix); '#' is Python-only (comment)
JAVA_SEPARATORS  = {';', ',', '(', ')', '{', '}', '[', ']', '.'}
PYTHON_SEPARATORS = {';', ',', '(', ')', '{', '}', '[', ']', '.', ':', '@'}

# Characters that are simply illegal at the lexical level for each language
# (not operators, not separators, not start of any valid token)
JAVA_ILLEGAL_CHARS   = {'#', '`', '\\', '$'[1:]}   # $ is legal in Java identifiers, keep it out
PYTHON_ILLEGAL_CHARS = {'`', '\\'}                  # backslash only illegal outside strings

# -----------------------------
# Lexical Analyzer Class
# -----------------------------
class LexicalAnalyzer:
    def __init__(self, language):
        self.language   = language
        self.tokens     = []
        self.errors     = []
        self.line       = 1
        self.col        = 1
        self.idx        = 0
        self.code       = ""
        # Choose the correct operator / separator sets once
        if language == "Java":
            self.operators  = JAVA_OPERATORS
            self.separators = JAVA_SEPARATORS
        else:
            self.operators  = PYTHON_OPERATORS
            self.separators = PYTHON_SEPARATORS

    # ------------------------------------------------------------------
    def analyze(self, code):
        self.code   = code
        self.tokens = []
        self.errors = []
        self.line   = 1
        self.col    = 1
        self.idx    = 0

        while self.idx < len(self.code):
            ch = self.code[self.idx]

            # Whitespace
            if ch.isspace():
                if ch == '\n':
                    self.line += 1
                    self.col = 1
                else:
                    self.col += 1
                self.idx += 1
                continue

            # '#' in Java is always a lexical error — check BEFORE comment matching
            if self.language == "Java" and ch == '#':
                self.add_error('Illegal Character', '#', self.line, self.col)
                self.idx += 1
                self.col += 1
                continue

            matched = (
                self.match_comment()      or
                self.match_string()       or
                self.match_number()       or
                self.match_operator()     or
                self.match_separator()    or
                self.match_identifier()   or
                self.match_error()
            )

            if not matched:
                self.idx += 1
                self.col += 1

        return self.tokens

    # ------------------------------------------------------------------
    # STRING MATCHING
    # ------------------------------------------------------------------
    def match_string(self):
        start_line, start_col = self.line, self.col
        prefix   = ""
        is_raw   = False

        # Python string prefixes (r, b, f, u and combinations)
        if self.language == "Python":
            prefix_match = re.match(r'^[rbfuRBFU]{1,3}', self.code[self.idx:])
            if prefix_match:
                candidate = prefix_match.group()
                # Only consume prefix if immediately followed by a quote
                after = self.idx + len(candidate)
                if after < len(self.code) and self.code[after] in ('"', "'"):
                    prefix  = candidate
                    is_raw  = 'r' in prefix.lower()
                    self.idx += len(prefix)
                    self.col += len(prefix)

        # Java character literal  'x'
        if self.language == "Java" and self.idx < len(self.code) and self.code[self.idx] == "'":
            return self._match_java_char_literal(start_line, start_col)

        # Triple-quoted strings (Python only)
        if self.language == "Python":
            for q in ('"""', "'''"):
                if self.code.startswith(q, self.idx):
                    self.idx += 3; self.col += 3
                    content = ""
                    while self.idx < len(self.code):
                        if self.code.startswith(q, self.idx):
                            self.idx += 3; self.col += 3
                            self.add_token('String', prefix + q + content + q, start_line, start_col)
                            return True
                        ch = self.code[self.idx]
                        content += ch
                        if ch == '\n': self.line += 1; self.col = 1
                        else: self.col += 1
                        self.idx += 1
                    self.add_error('Unterminated String', prefix + q + content, start_line, start_col)
                    return True

        # Regular single / double quoted strings
        if self.idx < len(self.code) and self.code[self.idx] in ('"', "'"):
            quote = self.code[self.idx]
            self.idx += 1; self.col += 1
            content = ""
            while self.idx < len(self.code):
                ch = self.code[self.idx]
                # Escape sequence
                if not is_raw and ch == '\\':
                    esc = self.code[self.idx: self.idx + 2]
                    content += esc
                    self.idx += 2; self.col += 2
                    continue
                # Closing quote
                if ch == quote:
                    self.idx += 1; self.col += 1
                    self.add_token('String', prefix + quote + content + quote, start_line, start_col)
                    return True
                # Newline inside string
                if ch == '\n':
                    # Java strings cannot span lines
                    self.add_error('Unterminated String', prefix + quote + content, start_line, start_col)
                    return True
                content += ch
                self.col += 1
                self.idx += 1
            self.add_error('Unterminated String', prefix + quote + content, start_line, start_col)
            return True

        return False

    def _match_java_char_literal(self, start_line, start_col):
        """Java single-character literals: 'a', '\\n', etc."""
        self.idx += 1; self.col += 1   # consume opening '
        content = "'"
        closed  = False
        while self.idx < len(self.code):
            ch = self.code[self.idx]
            if ch == '\\':
                esc = self.code[self.idx: self.idx + 2]
                content += esc
                self.idx += 2; self.col += 2
                continue
            if ch == "'":
                content += "'"
                self.idx += 1; self.col += 1
                closed = True
                break
            if ch == '\n':
                break
            content += ch
            self.idx += 1; self.col += 1
        if closed:
            self.add_token('CharLiteral', content, start_line, start_col)
        else:
            self.add_error('Unterminated Char Literal', content, start_line, start_col)
        return True

    # ------------------------------------------------------------------
    # COMMENT MATCHING
    # ------------------------------------------------------------------
    def match_comment(self):
        start_line, start_col = self.line, self.col

        # Python single-line comment
        if self.language == "Python" and self.code[self.idx] == '#':
            comment = ""
            while self.idx < len(self.code) and self.code[self.idx] != '\n':
                comment += self.code[self.idx]
                self.idx += 1; self.col += 1
            self.add_token('Comment', comment, start_line, start_col)
            return True

        # Java single-line comment
        if self.language == "Java" and self.code.startswith('//', self.idx):
            comment = ""
            while self.idx < len(self.code) and self.code[self.idx] != '\n':
                comment += self.code[self.idx]
                self.idx += 1; self.col += 1
            self.add_token('Comment', comment, start_line, start_col)
            return True

        # Java multi-line comment
        if self.language == "Java" and self.code.startswith('/*', self.idx):
            comment = ""
            while self.idx < len(self.code):
                if self.code.startswith('*/', self.idx):
                    comment += '*/'
                    self.idx += 2; self.col += 2
                    self.add_token('Comment', comment, start_line, start_col)
                    return True
                ch = self.code[self.idx]
                comment += ch
                if ch == '\n': self.line += 1; self.col = 1
                else: self.col += 1
                self.idx += 1
            self.add_error('Unterminated Comment', comment, start_line, start_col)
            return True

        return False

    # ------------------------------------------------------------------
    # NUMBER MATCHING
    # ------------------------------------------------------------------
    def match_number(self):
        start_line, start_col = self.line, self.col

        # Must start with a digit or a dot followed by a digit
        if not (self.code[self.idx].isdigit() or
                (self.code[self.idx] == '.' and self.idx + 1 < len(self.code)
                 and self.code[self.idx + 1].isdigit())):
            return False

        patterns = [
            # Hex / Bin / Oct — integers only (Java & Python)
            (r'0[xX][0-9a-fA-F][0-9a-fA-F_]*[lLjJ]?', 'HexInteger'),
            (r'0[bB][01][01_]*[lLjJ]?',                 'BinaryInteger'),
            (r'0[oO][0-7][0-7_]*[lLjJ]?',               'OctalInteger'),
            # Float / complex
            (r'\d[\d_]*\.[\d_]*(?:[eE][+-]?\d[\d_]*)?[fFdDjJ]?', 'Float'),
            (r'\.\d[\d_]*(?:[eE][+-]?\d[\d_]*)?[fFdDjJ]?',       'Float'),
            (r'\d[\d_]*[eE][+-]?\d[\d_]*[fFdDjJ]?',              'Float'),
            # Plain integer (with optional Java long suffix or Python complex j)
            (r'\d[\d_]*[lLjJ]?',                                   'Integer'),
        ]

        for pattern, ttype in patterns:
            m = re.match(pattern, self.code[self.idx:])
            if m:
                val = m.group()
                # Make sure we didn't accidentally eat into an identifier
                end = self.idx + len(val)
                if end < len(self.code) and (self.code[end].isalpha() or self.code[end] == '_'):
                    # e.g. "1abc" — stop at the digit part, the rest is an error
                    # Find longest purely digit+underscore+suffix portion
                    m2 = re.match(r'[\d_]+[lLjJfFdD]?', self.code[self.idx:])
                    if m2:
                        val = m2.group()
                        end = self.idx + len(val)
                        if end < len(self.code) and (self.code[end].isalpha() or self.code[end] == '_'):
                            # The digit portion alone is fine; the letter suffix will be its own error
                            pass
                self.idx += len(val); self.col += len(val)
                self.add_token(ttype, val, start_line, start_col)
                return True

        return False

    # ------------------------------------------------------------------
    # OPERATOR MATCHING  (language-specific set)
    # ------------------------------------------------------------------
    def match_operator(self):
        ops = sorted(self.operators, key=len, reverse=True)
        for op in ops:
            if self.code.startswith(op, self.idx):
                self.add_token('Operator', op, self.line, self.col)
                self.idx += len(op); self.col += len(op)
                return True
        return False

    # ------------------------------------------------------------------
    # SEPARATOR MATCHING  (language-specific set)
    # ------------------------------------------------------------------
    def match_separator(self):
        if self.code[self.idx] in self.separators:
            self.add_token('Separator', self.code[self.idx], self.line, self.col)
            self.idx += 1; self.col += 1
            return True
        return False

    # ------------------------------------------------------------------
    # IDENTIFIER / KEYWORD MATCHING
    # ------------------------------------------------------------------
    def match_identifier(self):
        # Java identifiers may start with $ or _; Python uses Unicode \w
        if self.language == "Java":
            pattern = r'[A-Za-z_$][A-Za-z0-9_$]*'
        else:
            pattern = r'[^\d\W]\w*'

        m = re.match(pattern, self.code[self.idx:])
        if m:
            val      = m.group()
            keywords = JAVA_KEYWORDS if self.language == "Java" else PYTHON_KEYWORDS
            ttype    = 'Keyword' if val in keywords else 'Identifier'
            self.add_token(ttype, val, self.line, self.col)
            self.idx += len(val); self.col += len(val)
            return True
        return False

    # ------------------------------------------------------------------
    # CATCH-ALL ERROR
    # ------------------------------------------------------------------
    def match_error(self):
        ch = self.code[self.idx]
        self.add_error('Illegal Character', ch, self.line, self.col)
        self.idx += 1; self.col += 1
        return True

    # ------------------------------------------------------------------
    def add_token(self, ttype, val, line, col):
        self.tokens.append({'Value': val, 'Type': ttype, 'Line': line, 'Col': col})

    def add_error(self, etype, val, line, col):
        label = f'Lexical Error ({etype})'
        self.tokens.append({'Value': val, 'Type': label, 'Line': line, 'Col': col})
        self.errors.append({'Value': val, 'Error': etype, 'Line': line, 'Col': col})


# =============================================================================
# UI
# =============================================================================
st.title("🧠 Lexical Analyzer — Java & Python")
st.caption("Strictly lexical analysis: tokens, errors, line/column tracking. Comments excluded from stats.")

col_lang, col_btn = st.columns([3, 1])
with col_lang:
    language = st.selectbox("Select Language", ["Python", "Java"])
code_input = st.text_area("Enter your code here", height=300,
                           placeholder="Paste Java or Python source code…")

analyze_clicked = st.button("⚡ Analyze Code", type="primary")

if analyze_clicked:
    if not code_input.strip():
        st.warning("Please enter some code first.")
    else:
        analyzer = LexicalAnalyzer(language)
        all_tokens = analyzer.analyze(code_input)

        # Separate comments from the real token stream
        non_comment_tokens = [t for t in all_tokens if t['Type'] != 'Comment']
        comment_tokens      = [t for t in all_tokens if t['Type'] == 'Comment']
        error_tokens        = [t for t in all_tokens if t['Type'].startswith('Lexical Error')]

        df_all      = pd.DataFrame(all_tokens)
        df_no_cmt   = pd.DataFrame(non_comment_tokens) if non_comment_tokens else pd.DataFrame()
        df_errors   = pd.DataFrame(analyzer.errors)    if analyzer.errors    else pd.DataFrame()
        df_comments = pd.DataFrame(comment_tokens)     if comment_tokens     else pd.DataFrame()

        # ── Token Stream ──────────────────────────────────────────────
        st.subheader("📋 Token Stream")
        if not df_no_cmt.empty:
            st.dataframe(df_no_cmt, use_container_width=True)
        else:
            st.info("No tokens found.")

        # ── Stats + Chart ─────────────────────────────────────────────
        c1, c2 = st.columns([1, 2])
        with c1:
            st.subheader("📊 Summary")
            total_real  = len(non_comment_tokens)
            total_cmts  = len(comment_tokens)
            total_errs  = len(error_tokens)
            total_all   = len(all_tokens)

            st.metric("Total Tokens", total_real)
            st.metric("Lexical Errors", total_errs)

        with c2:
            st.subheader("🔢 Token Type Distribution")
            if not df_no_cmt.empty:
                counts = df_no_cmt['Type'].value_counts()
                st.bar_chart(counts)

        # ── Errors ────────────────────────────────────────────────────
        if not df_errors.empty:
            st.subheader("🚨 Lexical Errors")
            st.dataframe(df_errors, use_container_width=True)
        else:
            st.success("✅ No lexical errors detected.")

        # ── Comments (collapsed) ──────────────────────────────────────
        if not df_comments.empty:
            with st.expander(f"💬 Comments ({total_cmts} found — excluded from stats)"):
                st.dataframe(df_comments, use_container_width=True)
