"""
EkalavyaAI — PDF Ingestion CLI

Parses ICAI / NCERT / coaching PDFs into searchable RAG chunks and upserts them
to Pinecone + ElasticSearch via :class:`rag.ingestion.PDFIngestionPipeline`.

Layout convention (default discovery):
    data/source_pdfs/<EXAM>/<SUBJECT>/*.pdf
e.g. data/source_pdfs/CA_FOUNDATION/Business Mathematics/icai_bm.pdf

Usage
-----
# Discover & ingest everything under data/source_pdfs/<EXAM>/<SUBJECT>/
python -m scripts.ingest_pdfs

# Ingest a specific directory for an explicit exam/subject
python -m scripts.ingest_pdfs --dir data/source_pdfs/JEE/Physics --exam JEE --subject Physics

# Ingest a single file
python -m scripts.ingest_pdfs --file path/to/file.pdf --exam NEET --subject Biology

# Preview only (parse + chunk, no embeddings / no upsert — needs no API keys)
python -m scripts.ingest_pdfs --dry-run

Run from the backend/ directory (or via docker-compose exec backend ...).
"""
import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import SUPPORTED_EXAMS, settings  # noqa: E402
from rag.ingestion import PDFIngestionPipeline  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("ingest_pdfs")

DEFAULT_SOURCE_DIR = "data/source_pdfs"


def _discover(root: Path) -> list[tuple[Path, str, str]]:
    """
    Walk ``root/<EXAM>/<SUBJECT>/*.pdf`` and return (pdf_path, exam, subject).

    Only directories whose name matches a supported exam are considered.
    """
    jobs: list[tuple[Path, str, str]] = []
    if not root.exists():
        logger.warning("Source directory %s does not exist.", root)
        return jobs

    for exam_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        exam = exam_dir.name
        if exam not in SUPPORTED_EXAMS:
            logger.warning(
                "Skipping '%s' — not a supported exam (%s).", exam, SUPPORTED_EXAMS
            )
            continue
        for subject_dir in sorted(p for p in exam_dir.iterdir() if p.is_dir()):
            for pdf in sorted(subject_dir.glob("*.pdf")):
                jobs.append((pdf, exam, subject_dir.name))
    return jobs


async def _run(args: argparse.Namespace) -> int:
    pipeline = PDFIngestionPipeline()

    # Build the list of (pdf, exam, subject) jobs.
    jobs: list[tuple[Path, str, str]] = []
    if args.file:
        if not args.exam or not args.subject:
            logger.error("--file requires both --exam and --subject.")
            return 2
        jobs.append((Path(args.file), args.exam, args.subject))
    elif args.dir and args.exam and args.subject:
        jobs.extend(
            (pdf, args.exam, args.subject)
            for pdf in sorted(Path(args.dir).glob("*.pdf"))
        )
    else:
        root = Path(args.dir or DEFAULT_SOURCE_DIR)
        jobs = _discover(root)

    if not jobs:
        logger.warning(
            "No PDFs found to ingest. Place PDFs under %s/<EXAM>/<SUBJECT>/ "
            "or pass --file / --dir explicitly.",
            args.dir or DEFAULT_SOURCE_DIR,
        )
        return 1

    logger.info("Planned %d PDF(s) to %s.", len(jobs), "analyze" if args.dry_run else "ingest")

    ok, failed = 0, 0
    for pdf_path, exam, subject in jobs:
        if not pdf_path.exists():
            logger.error("File not found: %s", pdf_path)
            failed += 1
            continue
        try:
            if args.dry_run:
                report = await pipeline.analyze_pdf(str(pdf_path), exam, subject)
                logger.info(
                    "DRY-RUN %s [%s/%s]: %d pages, %d chapters, %d chunks",
                    report["file"], exam, subject,
                    report["pages"], len(report["chapters"]), report["chunks"],
                )
            else:
                await pipeline.ingest_pdf(str(pdf_path), exam, subject)
                logger.info("Ingested %s [%s/%s]", pdf_path.name, exam, subject)
            ok += 1
        except Exception as e:  # noqa: BLE001 — report and continue with next file
            logger.error("Failed on %s: %s", pdf_path.name, e, exc_info=True)
            failed += 1

    logger.info("Done. %d succeeded, %d failed.", ok, failed)
    return 0 if failed == 0 else 1


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest educational PDFs into the EkalavyaAI RAG knowledge base.",
    )
    parser.add_argument(
        "--dir",
        help=f"Directory to ingest (default discovery root: {DEFAULT_SOURCE_DIR}).",
    )
    parser.add_argument("--file", help="Ingest a single PDF file (requires --exam, --subject).")
    parser.add_argument("--exam", help=f"Exam code. One of: {SUPPORTED_EXAMS}.")
    parser.add_argument("--subject", help="Subject name (free text, matches seed chapters).")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse + chunk only; do not embed or upsert (no external services needed).",
    )
    args = parser.parse_args()

    if args.exam and args.exam not in SUPPORTED_EXAMS:
        parser.error(f"Invalid --exam '{args.exam}'. Must be one of: {SUPPORTED_EXAMS}")

    if not args.dry_run:
        logger.info(
            "Targets — Pinecone index '%s', ElasticSearch '%s'. "
            "Ensure PINECONE_API_KEY / embedding creds are set (use --dry-run to preview).",
            settings.PINECONE_INDEX_NAME, settings.ELASTICSEARCH_INDEX,
        )

    raise SystemExit(asyncio.run(_run(args)))


if __name__ == "__main__":
    main()
