# Python Code Style Guide

- Leave one blank line after a function or method signature, or after its docstring when it has one. Place the docstring directly below the signature.
- For classes with a docstring, place it directly below the class signature and leave one blank line after it. For classes without a docstring, start the body immediately below the signature to match Ruff's formatting.
- Group statements by logical step and leave one blank line between steps.
- Place a brief single-line `#` comment directly above each logical block, at the same indentation. Describe what the block accomplishes as a whole.

```python
def read_label(path):
    """Read a label from disk."""

    # Load the saved label.
    text = path.read_text(encoding="utf-8")

    # Remove surrounding whitespace before displaying the label.
    return text.strip()
```
