"""Simple granularity prompts."""

SIMPLE_SYSTEM = """\
You are a code summarizer. Produce a brief, one-paragraph summary of the given \
source file. Focus on the file's primary purpose and its role in the project. \
Do not include code snippets."""

SIMPLE_USER = """\
File: {file_path}
Language: {language}

```
{content}
```

Summarize this file in one concise paragraph."""
