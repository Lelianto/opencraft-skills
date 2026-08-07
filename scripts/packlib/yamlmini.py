"""Minimal YAML subset parser and emitter.

Dependency-free. Supports the subset used by Context Packs:
block mappings and sequences (indentation-based), plain/single-/double-quoted
scalars, ints, floats, booleans, null, inline flow sequences and maps, block
scalars (| and > with chomping), and comments. No anchors, aliases, tags, or
multi-document streams.
"""

from __future__ import annotations

import re

__all__ = ["YAMLError", "parse", "dump", "load_file"]


class YAMLError(ValueError):
    pass


MAX_DEPTH = 200


_BLOCK_MARKERS = {"|", ">", "|-", "|+", ">-", ">+"}
_PLAIN_NULL = {"null", "Null", "NULL", "~"}
_PLAIN_TRUE = {"true", "True", "TRUE"}
_PLAIN_FALSE = {"false", "False", "FALSE"}


def _indent_of(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _skip_blank(lines, i):
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if line.lstrip().startswith("#"):
            i += 1
            continue
        break
    return i


def _skip_ws(s: str, i: int) -> int:
    while i < len(s) and s[i] in " \t":
        i += 1
    return i


def _parse_quoted(s: str, i: int):
    """Parse a quoted string starting at s[i]. Returns (value, index_after)."""
    q = s[i]
    i += 1
    out = []
    while i < len(s):
        c = s[i]
        if q == "'":
            if c == "'":
                if i + 1 < len(s) and s[i + 1] == "'":
                    out.append("'")
                    i += 2
                    continue
                return "".join(out), i + 1
            out.append(c)
            i += 1
        else:
            if c == "\\":
                nxt = s[i + 1] if i + 1 < len(s) else ""
                mapping = {"n": "\n", "t": "\t", "\\": "\\", '"': '"', "0": "\0", "'": "'"}
                if nxt in mapping:
                    out.append(mapping[nxt])
                    i += 2
                elif nxt == "u":
                    out.append(chr(int(s[i + 2:i + 6], 16)))
                    i += 6
                elif nxt:
                    out.append(nxt)
                    i += 2
                else:
                    raise YAMLError("unterminated escape")
                continue
            if c == '"':
                return "".join(out), i + 1
            out.append(c)
            i += 1
    raise YAMLError("unterminated quoted string")


def _find_key_colon(s: str) -> int:
    """Return the index of the key/value ':' in a mapping line, or -1."""
    if not s:
        return -1
    if s[0] in "\"'":
        _, end = _parse_quoted(s, 0)
        while end < len(s) and s[end] == " ":
            end += 1
        return end if end < len(s) and s[end] == ":" else -1
    depth = 0
    i = 0
    while i < len(s):
        c = s[i]
        if c in "\"'":
            _, i = _parse_quoted(s, i)
            continue
        if c in "[{":
            depth += 1
        elif c in "]}":
            depth -= 1
        elif c == ":" and depth == 0:
            key = s[:i]
            nxt = s[i + 1:]
            if key and " " not in key and "://" not in key and (nxt == "" or nxt.startswith(" ")):
                return i
            return -1
        i += 1
    return -1


def _plain(s: str):
    if s in _PLAIN_NULL:
        return None
    if s in _PLAIN_TRUE:
        return True
    if s in _PLAIN_FALSE:
        return False
    if re.fullmatch(r"[-+]?[0-9]+", s):
        return int(s)
    if re.fullmatch(r"[-+]?(?:[0-9]+\.[0-9]*|\.[0-9]+|[0-9]+[eE][-+]?[0-9]+)", s):
        return float(s)
    return s


def _marker(rest: str):
    if rest in ("|", ">-", "|-", "|+", ">+"):
        literal = rest.startswith("|")
        chomp = "strip" if rest.endswith("-") else "keep" if rest.endswith("+") else "clip"
        return literal, chomp
    return rest == "|", "clip"


def _fold(lines):
    out = []
    prev_empty = True
    for ln in lines:
        if ln == "":
            out.append("")
            prev_empty = True
        else:
            if out and not prev_empty and out[-1] != "":
                out[-1] += " " + ln
            else:
                out.append(ln)
            prev_empty = False
    text = "\n".join(out)
    if lines:
        text += "\n"
    return text


def _scalar_body(lines, i, parent_indent, literal, chomp):
    """Collect indented block-scalar content; returns (text, next_index)."""
    raw = []
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            raw.append("")
            i += 1
            continue
        ind = _indent_of(line)
        if ind <= parent_indent:
            break
        raw.append(line)
        i += 1
    min_indent = None
    for ln in raw:
        if ln.strip():
            ind = _indent_of(ln)
            if min_indent is None or ind < min_indent:
                min_indent = ind
    body = []
    for ln in raw:
        if ln.strip():
            body.append(ln[min_indent:] if min_indent else ln.lstrip(" "))
        else:
            body.append("")
    while body and body[0] == "":
        body.pop(0)
    if chomp == "strip":
        while body and body[-1] == "":
            body.pop()
    if chomp == "clip":
        while body and body[-1] == "":
            body.pop()
    if literal:
        text = "\n".join(body)
        if body:
            text += "\n"
        return text, i
    return _fold(body), i


def _inline(s: str):
    s = s.strip()
    if not s:
        return None
    if s[0] == "[":
        v, _ = _flow_seq(s, 0)
        return v
    if s[0] == "{":
        v, _ = _flow_map(s, 0)
        return v
    if s[0] in "\"'":
        v, _ = _parse_quoted(s, 0)
        return v
    if " #" in s:
        s = s.split(" #", 1)[0].strip()
    return _plain(s)


def _flow_seq(s: str, i: int, _depth=0):
    if _depth > MAX_DEPTH:
        raise YAMLError(f"maximum nesting depth {MAX_DEPTH} exceeded")
    i = _skip_ws(s, i)
    if i >= len(s) or s[i] != "[":
        raise YAMLError("expected [ for flow sequence")
    i += 1
    result = []
    while True:
        i = _skip_ws(s, i)
        if i >= len(s):
            raise YAMLError("unterminated flow sequence")
        c = s[i]
        if c == "]":
            return result, i + 1
        if c == "[":
            v, i = _flow_seq(s, i, _depth + 1)
            result.append(v)
        elif c == "{":
            v, i = _flow_map(s, i, _depth + 1)
            result.append(v)
        elif c in "\"'":
            v, i = _parse_quoted(s, i)
            result.append(v)
        else:
            start = i
            while i < len(s) and s[i] not in ",]":
                i += 1
            tok = s[start:i].strip()
            if not tok:
                raise YAMLError("empty flow sequence item")
            result.append(_plain(tok))
        i = _skip_ws(s, i)
        if i >= len(s):
            raise YAMLError("unterminated flow sequence")
        if s[i] == ",":
            i += 1
            continue
        if s[i] == "]":
            return result, i + 1
        raise YAMLError("expected , or ] in flow sequence")


def _flow_map(s: str, i: int, _depth=0):
    if _depth > MAX_DEPTH:
        raise YAMLError(f"maximum nesting depth {MAX_DEPTH} exceeded")
    i = _skip_ws(s, i)
    if i >= len(s) or s[i] != "{":
        raise YAMLError("expected { for flow map")
    i += 1
    result = {}
    while True:
        i = _skip_ws(s, i)
        if i >= len(s):
            raise YAMLError("unterminated flow map")
        if s[i] == "}":
            return result, i + 1
        if s[i] in "\"'":
            key, i = _parse_quoted(s, i)
        else:
            start = i
            while i < len(s) and s[i] not in ":,}":
                i += 1
            key = s[start:i].strip()
        i = _skip_ws(s, i)
        if i >= len(s) or s[i] != ":":
            raise YAMLError("expected : in flow map")
        i = _skip_ws(s, i + 1)
        if i >= len(s):
            raise YAMLError("unterminated flow map")
        c = s[i]
        if c == "[":
            v, i = _flow_seq(s, i, _depth + 1)
        elif c == "{":
            v, i = _flow_map(s, i, _depth + 1)
        elif c in "\"'":
            v, i = _parse_quoted(s, i)
        else:
            start = i
            while i < len(s) and s[i] not in ",}":
                i += 1
            tok = s[start:i].strip()
            v = _plain(tok) if tok else None
        result[key] = v
        i = _skip_ws(s, i)
        if i >= len(s):
            raise YAMLError("unterminated flow map")
        if s[i] == ",":
            i += 1
            continue
        if s[i] == "}":
            return result, i + 1
        raise YAMLError("expected , or } in flow map")


def _assign(lines, i, indent, target, key, rest, _depth=0):
    """Consume a value for ``key`` at line ``i`` (indent ``indent``). Returns new index."""
    if rest in _BLOCK_MARKERS:
        literal, chomp = _marker(rest)
        body, i = _scalar_body(lines, i + 1, indent, literal, chomp)
        target[key] = body
        return i
    if rest == "":
        ni = _skip_blank(lines, i + 1)
        if ni < len(lines) and _indent_of(lines[ni]) > indent:
            if _depth > MAX_DEPTH:
                raise YAMLError(f"maximum nesting depth {MAX_DEPTH} exceeded")
            sub, i = _node(lines, ni, _indent_of(lines[ni]), _depth + 1)
            target[key] = sub
        else:
            target[key] = None
            i += 1
        return i
    target[key] = _inline(rest)
    return i + 1


def _node(lines, i, indent, _depth=0):
    i = _skip_blank(lines, i)
    if i >= len(lines):
        return None, i
    ind = _indent_of(lines[i])
    if ind < indent:
        return None, i
    content = lines[i][ind:]
    if content == "-" or content.startswith("- "):
        return _sequence(lines, i, ind, _depth)
    if _find_key_colon(content) >= 0:
        return _mapping(lines, i, ind, _depth)
    if not content.strip():
        return None, i
    raise YAMLError(f"cannot parse block at line {i + 1}: {content!r}")


def _mapping(lines, i, indent, _depth=0):
    result = {}
    while True:
        i = _skip_blank(lines, i)
        if i >= len(lines):
            break
        ind = _indent_of(lines[i])
        if ind != indent:
            break
        content = lines[i][ind:]
        if content == "-" or content.startswith("- "):
            break
        idx = _find_key_colon(content)
        if idx < 0:
            break
        key = content[:idx]
        if key[:1] in "\"'":
            key, _ = _parse_quoted(key, 0)
        key = key.strip()
        rest = content[idx + 1:].strip()
        i = _assign(lines, i, indent, result, key, rest, _depth)
    return result, i


def _sequence(lines, i, indent, _depth=0):
    result = []
    while True:
        i = _skip_blank(lines, i)
        if i >= len(lines):
            break
        ind = _indent_of(lines[i])
        if ind != indent:
            break
        content = lines[i][ind:]
        if content != "-" and not content.startswith("- "):
            break
        rest = content[2:].strip() if len(content) > 1 else ""
        if rest == "":
            ni = _skip_blank(lines, i + 1)
            if ni < len(lines) and _indent_of(lines[ni]) > indent:
                if _depth > MAX_DEPTH:
                    raise YAMLError(f"maximum nesting depth {MAX_DEPTH} exceeded")
                sub, i = _node(lines, ni, _indent_of(lines[ni]), _depth + 1)
                result.append(sub)
            else:
                result.append(None)
                i += 1
            continue
        idx = _find_key_colon(rest)
        if idx < 0:
            result.append(_inline(rest))
            i += 1
            continue
        item = {}
        key = rest[:idx].strip()
        if key[:1] in "\"'":
            key, _ = _parse_quoted(key, 0)
        r2 = rest[idx + 1:].strip()
        i = _assign(lines, i, indent, item, key, r2, _depth)
        key_indent = indent + 2
        while True:
            j = _skip_blank(lines, i)
            if j >= len(lines):
                i = j
                break
            if _indent_of(lines[j]) != key_indent:
                break
            c2 = lines[j][key_indent:]
            if c2 == "-" or c2.startswith("- "):
                break
            idx2 = _find_key_colon(c2)
            if idx2 < 0:
                break
            k2 = c2[:idx2].strip()
            if k2[:1] in "\"'":
                k2, _ = _parse_quoted(k2, 0)
            r3 = c2[idx2 + 1:].strip()
            i = _assign(lines, j, key_indent, item, k2, r3, _depth)
        result.append(item)
    return result, i


def parse(text: str):
    if not text:
        return None
    if text.startswith("\ufeff"):
        text = text[1:]
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    value, _ = _node(lines, 0, 0)
    return value


def load_file(path):
    with open(path, "r", encoding="utf-8") as handle:
        return parse(handle.read())


# ---------------------------------------------------------------------------
# Emitter
# ---------------------------------------------------------------------------

_NEEDS_QUOTE_RE = re.compile(r"[{}\[\],:&*#?|>!%@`\"'\\\n\t]")


def _plain_needs_quote(s):
    if s == "" or s != s.strip():
        return True
    if _NEEDS_QUOTE_RE.search(s):
        return True
    if s[0] in "-?:,[]{}#&*!|>'\"%@`":
        return True
    if re.fullmatch(r"[-+]?[0-9]+", s):
        return True
    if re.fullmatch(r"[-+]?(?:[0-9]+\.[0-9]*|\.[0-9]+|[0-9]+[eE][-+]?[0-9]+)", s):
        return True
    if s in _PLAIN_NULL or s in _PLAIN_TRUE or s in _PLAIN_FALSE:
        return True
    return False


def _quote(s):
    out = ['"']
    for c in s:
        if c == '"':
            out.append('\\"')
        elif c == "\\":
            out.append("\\\\")
        elif c == "\n":
            out.append("\\n")
        elif c == "\t":
            out.append("\\t")
        else:
            out.append(c)
    out.append('"')
    return "".join(out)


def _key_str(k):
    s = str(k)
    return _quote(s) if _plain_needs_quote(s) else s


def _val_str(v):
    if v is None:
        return "null"
    if v is True:
        return "true"
    if v is False:
        return "false"
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return str(v)
    s = str(v)
    return _quote(s) if _plain_needs_quote(s) else s


def _emit_block_lines(text, level, indent, out):
    pad = " " * (indent * level)
    for ln in text.split("\n"):
        out.append(pad + ln)


def _emit(value, level, indent, out):
    pad = " " * (indent * level)
    if isinstance(value, dict):
        if not value:
            out.append(pad + "{}")
            return
        for key, val in value.items():
            k = _key_str(key)
            if isinstance(val, dict):
                if not val:
                    out.append(f"{pad}{k}: {{}}")
                else:
                    out.append(f"{pad}{k}:")
                    _emit(val, level + 1, indent, out)
            elif isinstance(val, list):
                if not val:
                    out.append(f"{pad}{k}: []")
                else:
                    out.append(f"{pad}{k}:")
                    _emit_list(val, level + 1, indent, out)
            elif isinstance(val, str) and "\n" in val:
                out.append(f"{pad}{k}: |")
                _emit_block_lines(val, level + 1, indent, out)
            else:
                out.append(f"{pad}{k}: {_val_str(val)}")
    elif isinstance(value, list):
        _emit_list(value, level, indent, out)
    else:
        out.append(pad + _val_str(value))


def _emit_list(value, level, indent, out):
    pad = " " * (indent * level)
    for item in value:
        if isinstance(item, dict):
            if not item:
                out.append(f"{pad}- {{}}")
                continue
            first = True
            for key, val in item.items():
                k = _key_str(key)
                if first:
                    head = f"{pad}- {k}"
                else:
                    head = f"{pad}{' ' * indent}{k}"
                if isinstance(val, dict):
                    if not val:
                        out.append(f"{head}: {{}}")
                    else:
                        out.append(f"{head}:")
                        _emit(val, level + 2, indent, out)
                elif isinstance(val, list):
                    if not val:
                        out.append(f"{head}: []")
                    else:
                        out.append(f"{head}:")
                        _emit_list(val, level + 2, indent, out)
                elif isinstance(val, str) and "\n" in val:
                    out.append(f"{head}: |")
                    _emit_block_lines(val, level + 2, indent, out)
                else:
                    out.append(f"{head}: {_val_str(val)}")
                first = False
        elif isinstance(item, list):
            out.append(f"{pad}-")
            _emit_list(item, level + 1, indent, out)
        elif isinstance(item, str) and "\n" in item:
            out.append(f"{pad}- |")
            _emit_block_lines(item, level + 1, indent, out)
        else:
            out.append(f"{pad}- {_val_str(item)}")


def dump(data, indent: int = 2) -> str:
    out = []
    _emit(data, 0, indent, out)
    return "\n".join(out) + "\n"
