"""Phase B question filters; the historical substring rule remains the default."""
import re


def question_skip_reason(question, majority_answer, box_filter="legacy"):
    if box_filter not in {"legacy", "latex_only"}:
        raise ValueError("RZERO_QUESTION_BOX_FILTER must be legacy or latex_only")
    if "证明" in question:
        return "proof_question"
    if ("box" in question.lower() if box_filter == "legacy"
            else re.search(r"\\boxed(?![A-Za-z])", question) is not None):
        return "box_substring" if box_filter == "legacy" else "latex_boxed_question"
    if "text" in majority_answer.lower():
        return "text_answer"
    return None
