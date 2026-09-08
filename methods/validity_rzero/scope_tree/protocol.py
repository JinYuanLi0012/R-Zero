"""Flat model field records -> canonical internal objects, without guessing values."""
import re


class FieldError(ValueError):
    pass


class Fields:
    def __init__(self, text):
        self.rows = []
        self.index = 0
        for number, line in enumerate(text.splitlines(), 1):
            if not line.strip():
                continue
            if line.startswith("  "):
                if not self.rows:
                    raise FieldError(f"final line {number}: continuation has no preceding field")
                key, value, start = self.rows[-1]
                self.rows[-1] = (key, value + "\n" + line[2:], start)
                continue
            match = re.fullmatch(r"([A-Z_]+):[ \t]*(.*)", line)
            if not match:
                raise FieldError(f"final line {number}: expected LABEL: value at column 1; indent value continuations by two spaces")
            self.rows.append((match[1], match[2].rstrip(), number))

    def peek(self):
        return self.rows[self.index][0] if self.index < len(self.rows) else None

    def take(self, key):
        if self.peek() != key:
            found = self.peek() or "end of final block"
            line = self.rows[self.index][2] if self.peek() else "end"
            raise FieldError(f"final line {line}: expected {key}, found {found}; field missing, duplicated, or out of order")
        _, value, line = self.rows[self.index]
        self.index += 1
        if not value.strip():
            raise FieldError(f"final line {line}: {key} requires a nonempty value")
        return value

    def boolean(self, key):
        value = self.take(key)
        if value not in ("YES", "NO"):
            raise FieldError(f"{key}: expected exactly YES or NO, got {value!r}")
        return value == "YES"

    def end(self):
        if self.peek():
            key, _, line = self.rows[self.index]
            raise FieldError(f"final line {line}: unexpected or duplicate field {key}")


def family(fields):
    return {"name": fields.take("NAME"), "scope": fields.take("SCOPE"),
            "distinguishing_feature": fields.take("DISTINCTION")}


def pairs(fields, global_review=False):
    rows = []
    while fields.peek() == "PAIR":
        endpoints = fields.take("PAIR").split()
        if len(endpoints) != 2:
            raise FieldError("PAIR: expected exactly two reference IDs separated by one space")
        row = {"a": endpoints[0], "b": endpoints[1], "relation": fields.take("RELATION")}
        if global_review:
            row["revise_id"] = fields.take("REVISE")
        row["reason"] = fields.take("REASON")
        rows.append(row)
    return rows


def parse_fields(text):
    fields = Fields(text)
    first = fields.peek()
    if first == "PRINCIPLE":
        principle = fields.take("PRINCIPLE")
        if fields.peek() == "NAME":
            children = []
            while fields.peek() == "NAME":
                children.append(family(fields))
            result = {"partition_principle": principle, "children": children}
        elif fields.peek() == "REPLACE":
            replacements = []
            while fields.peek() == "REPLACE":
                target = fields.take("REPLACE")
                action = fields.take("ACTION")
                if action not in ("REPLACE", "DELETE"):
                    raise FieldError("repair ACTION: expected REPLACE or DELETE")
                replacements.append({"id": target, "child": family(fields) if action == "REPLACE" else None})
            result = {"partition_principle": principle, "replacements": replacements}
        else:
            raise FieldError("PRINCIPLE must be followed by NAME family records or REPLACE records")
    elif first == "PRINCIPLE_OK":
        result = {"principle_ok": fields.boolean("PRINCIPLE_OK"),
                  "principle_feedback": fields.take("PRINCIPLE_REASON"), "children": []}
        while fields.peek() == "CHILD":
            row = {"id": fields.take("CHILD"), "fits_parent": fields.boolean("FIT"),
                   "follows_principle": fields.boolean("AXIS"), "comparable_breadth": fields.boolean("BREADTH")}
            if fields.peek() == "READY":
                row["generation_ready"] = fields.boolean("READY")
            row.update({"action": fields.take("ACTION"), "reason": fields.take("REASON")})
            result["children"].append(row)
        result["pairs"] = pairs(fields)
    elif first == "HAS_MAJOR_GAP":
        has_gap, gap = fields.boolean("HAS_MAJOR_GAP"), fields.take("GAP")
        if (has_gap and gap == "NONE") or (not has_gap and gap != "NONE"):
            raise FieldError("GAP: use NONE exactly when HAS_MAJOR_GAP is NO; YES requires a concrete description")
        result = {"has_major_gap": has_gap, "gap_description": gap if has_gap else None,
                  "reason": fields.take("REASON")}
    elif first == "NAME":
        result = {"child": family(fields)}
    elif first == "PARENT":
        result = {"parent_id": fields.take("PARENT"), "child": family(fields)}
    elif first == "PAIR":
        result = {"issues": pairs(fields, global_review=True)}
    elif first == "ISSUES":
        if fields.take("ISSUES") != "NONE":
            raise FieldError("ISSUES: only NONE is allowed; otherwise emit PAIR records")
        result = {"issues": []}
    else:
        raise FieldError(f"unknown first field {first!r}; use the field format specified for this action")
    fields.end()
    return result
