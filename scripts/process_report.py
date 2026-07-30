"""Trigger processing for an uploaded report."""
import asyncio, os, sys, logging
from uuid import UUID
from pathlib import Path

# Ensure we can import from apps/backend
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "apps" / "backend"))

from src.config.settings import get_settings
from src.database import session as db_session
from src.storage import LocalStorageProvider
from src.document_processing.cleaners.artifacts import PageArtifactCleaner
from src.document_processing.cleaners.base import CleaningPipeline
from src.document_processing.cleaners.unicode import UnicodeCleaner
from src.document_processing.cleaners.whitespace import WhitespaceCleaner
from src.document_processing.metadata import MetadataExtractor
from src.document_processing.parsers.docx import DOCXParser
from src.document_processing.parsers.pdf import PDFParser
from src.document_processing.parsers.registry import ParserRegistry
from src.document_processing.parsers.text import TextParser
from src.document_processing.pipeline import ProcessingPipeline
from src.services import ProcessingService

logging.basicConfig(level=logging.INFO)

async def main():
    report_id_str = sys.argv[1] if len(sys.argv) > 1 else "3fa08aad-e92f-4ef1-9a7a-a1bbcaefe0ec"
    pdf_source = sys.argv[2] if len(sys.argv) > 2 else "test_data/StudentGradeHistory_23BCE10311.pdf"

    report_id = UUID(report_id_str)

    # Init DB
    os.environ["APP_ENV"] = "development"
    from src.config.settings import AppSettings
    settings = AppSettings(_env_file="apps/backend/.env.local")

    await db_session.init_db(settings.DATABASE_URL)

    # Build processing service
    registry = ParserRegistry()
    registry.register(PDFParser)
    registry.register(DOCXParser)
    registry.register(TextParser)
    cleaners = CleaningPipeline([
        WhitespaceCleaner(), UnicodeCleaner(), PageArtifactCleaner(),
    ])
    pipeline = ProcessingPipeline(
        parser_registry=registry,
        cleaner_pipeline=cleaners,
        metadata_extractor=MetadataExtractor(),
    )
    storage = LocalStorageProvider(base_path=str(Path.cwd() / "apps/backend/data/storage"))

    # Copy PDF to storage location for this report
    storage_dir = Path("apps/backend/data/storage/reports") / report_id_str
    storage_dir.mkdir(parents=True, exist_ok=True)
    dest = storage_dir / "StudentGradeHistory_23BCE10311.pdf"
    import shutil
    shutil.copy2(pdf_source, dest)
    print(f"Copied PDF to {dest}")

    service = ProcessingService(
        pipeline=pipeline,
        storage=storage,
        db_factory=db_session.async_session_factory,
    )

    print(f"Processing report {report_id} with recursive chunking...")
    await service.process_report(report_id, preferences={"chunking_strategy": "recursive"})
    print("Done!")

if __name__ == "__main__":
    asyncio.run(main())
