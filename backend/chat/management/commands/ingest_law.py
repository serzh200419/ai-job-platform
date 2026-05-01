"""
Ingest an Armenian labor-law PDF into LawDocument chunks with embeddings.

Usage:
    python manage.py ingest_law path/to/arlis.pdf
    python manage.py ingest_law path/to/arlis.pdf --chunk-size 800 --title "ՀՀ Աշխատանքային Օրենսգիրք"
    python manage.py ingest_law path/to/arlis.pdf --clear
"""
import logging
import textwrap

from django.core.management.base import BaseCommand, CommandError

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Ingest a labor-law PDF into LawDocument chunks with OpenAI embeddings."

    def add_arguments(self, parser):
        parser.add_argument("pdf_path", type=str, help="Path to the PDF file")
        parser.add_argument(
            "--title",
            default="Armenian Labor Law",
            help="Title stored on every chunk (default: 'Armenian Labor Law')",
        )
        parser.add_argument(
            "--chunk-size",
            type=int,
            default=800,
            help="Approximate characters per chunk (default: 800)",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all existing LawDocument rows before ingesting",
        )

    def handle(self, *args, **options):
        try:
            from pypdf import PdfReader
        except ImportError:
            raise CommandError("pypdf is not installed. Run: pip install 'pypdf>=3.0'")

        from chat.models import LawDocument
        from chat.services.law_rag import embed_text

        pdf_path   = options["pdf_path"]
        title      = options["title"]
        chunk_size = options["chunk_size"]

        # ── Extract text ──────────────────────────────────────────────────────
        try:
            reader = PdfReader(pdf_path)
        except FileNotFoundError:
            raise CommandError(f"File not found: {pdf_path}")

        pages_text = []
        for page in reader.pages:
            text = page.extract_text() or ""
            pages_text.append(text)

        full_text = "\n".join(pages_text)
        self.stdout.write(f"Extracted {len(full_text):,} characters from {len(reader.pages)} pages.")

        if not full_text.strip():
            raise CommandError("PDF appears to be empty or image-only (no extractable text).")

        # ── Chunk ─────────────────────────────────────────────────────────────
        chunks = textwrap.wrap(full_text, chunk_size, break_long_words=False, break_on_hyphens=False)
        self.stdout.write(f"Split into {len(chunks)} chunks of ~{chunk_size} chars each.")

        # ── Optionally clear ──────────────────────────────────────────────────
        if options["clear"]:
            deleted, _ = LawDocument.objects.all().delete()
            self.stdout.write(f"Cleared {deleted} existing LawDocument rows.")

        # ── Embed & save ──────────────────────────────────────────────────────
        created = 0
        for i, chunk in enumerate(chunks):
            if not chunk.strip():
                continue

            self.stdout.write(f"  Embedding chunk {i + 1}/{len(chunks)}…", ending="\r")
            self.stdout.flush()

            try:
                embedding = embed_text(chunk)
            except Exception as exc:
                logger.warning("Skipping chunk %d — embedding failed: %s", i, exc)
                self.stdout.write(self.style.WARNING(f"\n  Skipped chunk {i}: {exc}"))
                continue

            LawDocument.objects.create(
                title=title,
                content=chunk,
                embedding=embedding,
                chunk_index=i,
            )
            created += 1

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"Done. Ingested {created} chunks into LawDocument."))
