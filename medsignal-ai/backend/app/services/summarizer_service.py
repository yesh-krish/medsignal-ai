from functools import lru_cache
import re
from time import perf_counter

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.drug_label import DrugLabel
from app.models.safety_summary import SafetySummary

SAFETY_SUMMARY_DISCLAIMER = (
    "This AI-generated summary is educational and is not medical advice, "
    "diagnosis, or treatment guidance. Review the FDA label and talk with a "
    "qualified clinician or pharmacist about medication decisions."
)


class SummarizerUnavailableError(Exception):
    pass


def generate_and_save_safety_summary(
    drug_id: int,
    label: DrugLabel,
    db: Session,
) -> tuple[SafetySummary, str]:
    label_text = _build_label_text(label)
    if not label_text:
        raise ValueError("No label safety sections are available to summarize")

    settings = get_settings()
    model_input = _build_model_input(
        label_text[: settings.summarizer_max_input_chars],
        settings.summarizer_task,
    )
    started_at = perf_counter()
    generated_text = _generate_summary(model_input)
    latency_ms = int((perf_counter() - started_at) * 1000)
    summary_text = _clean_summary(generated_text)

    summary = SafetySummary(
        drug_id=drug_id,
        summary_text=summary_text,
        model_name=settings.summarizer_model_name,
        input_length=len(model_input),
        output_length=len(summary_text),
        latency_ms=latency_ms,
    )
    db.add(summary)
    db.commit()
    db.refresh(summary)
    return summary, SAFETY_SUMMARY_DISCLAIMER


def _build_label_text(label: DrugLabel) -> str:
    sections = [
        ("Boxed warning", label.boxed_warning),
        ("Warnings", label.warnings),
        ("Adverse reactions", label.adverse_reactions),
        ("Contraindications", label.contraindications),
    ]
    chunks: list[str] = []
    for title, values in sections:
        if values:
            chunks.append(f"{title}:\n" + "\n".join(values))
    return "\n\n".join(chunks)


def _build_model_input(label_text: str, task: str) -> str:
    if task == "summarization":
        return label_text
    return (
        "Summarize this medication label safety information in plain English. "
        "Use cautious language and avoid causal wording. "
        "Mention warnings, contraindications, and reported adverse reactions "
        "when present.\n\n"
        f"{label_text}"
    )


def _generate_summary(prompt: str) -> str:
    settings = get_settings()
    try:
        generator = _get_generator(settings.summarizer_task, settings.summarizer_model_name)
        if settings.summarizer_task == "summarization":
            result = generator(
                prompt,
                max_length=settings.summarizer_max_new_tokens,
                min_length=settings.summarizer_min_new_tokens,
                do_sample=False,
                truncation=True,
            )
        else:
            result = generator(
                prompt,
                max_new_tokens=settings.summarizer_max_new_tokens,
                truncation=True,
            )
    except Exception as exc:
        raise SummarizerUnavailableError("AI summarizer failed") from exc

    if not result:
        raise SummarizerUnavailableError("AI summarizer returned no output")

    generated = result[0].get("generated_text") or result[0].get("summary_text")
    if not generated:
        raise SummarizerUnavailableError("AI summarizer output was empty")
    return str(generated)


@lru_cache
def _get_generator(task: str, model_name: str):
    from transformers import pipeline

    return pipeline(task, model=model_name)


def _clean_summary(summary_text: str) -> str:
    cleaned = " ".join(summary_text.split())
    cleaned = re.sub(r"\bmay cause\b", "has warnings about", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bcauses\b", "label describes", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bcause\b", "be associated with", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bcaused\b", "associated with", cleaned, flags=re.IGNORECASE)
    cleaned = _trim_incomplete_sentence(cleaned)
    if cleaned and cleaned[-1] not in ".!?":
        cleaned = f"{cleaned}."
    return cleaned


def _trim_incomplete_sentence(summary_text: str) -> str:
    fragments = re.split(r"(?<=[.!?])\s+", summary_text)
    if len(fragments) < 2:
        return summary_text

    last_fragment = fragments[-1].strip()
    if re.search(r"\b(is|are|was|were|be|with|of|to|or|and)\.?$", last_fragment):
        return " ".join(fragments[:-1]).strip()
    return summary_text
