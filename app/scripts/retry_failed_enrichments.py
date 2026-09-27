from __future__ import annotations

import argparse
import logging
import sys

from app.db import SessionLocal
from app.domain.bookmark import (
    EnrichmentStatus,
    list_pending_or_failed_enrichments,
)
from app.orchestration.save_bookmark import enrich_bookmark

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def retry_enrichments(limit: int = 50) -> tuple[int, int]:
    db = SessionLocal()
    try:
        bookmarks = list_pending_or_failed_enrichments(db, limit=limit)
        if not bookmarks:
            logger.info("Nessun bookmark in attesa o fallito da ri-arricchire.")
            return 0, 0

        logger.info("Trovati %d bookmark da arricchire.", len(bookmarks))
        success_count = 0
        fail_count = 0

        for bm in bookmarks:
            logger.info("Arricchimento bookmark id=%d (%s)...", bm.id, bm.url)
            try:
                enrich_bookmark(db, bm)
                success_count += 1
            except Exception as exc:
                logger.error("Arricchimento fallito per bookmark id=%d: %s", bm.id, exc)
                bm.enrichment_status = EnrichmentStatus.FAILED
                db.commit()
                fail_count += 1

        logger.info(
            "Completato: %d riusciti, %d falliti su %d totali.",
            success_count,
            fail_count,
            len(bookmarks),
        )
        return success_count, fail_count
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Riesegue l'arricchimento dei bookmark con stato pending o failed."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Numero massimo di bookmark da processare (default: 50)",
    )
    args = parser.parse_args()

    success, failed = retry_enrichments(limit=args.limit)
    if failed > 0 and success == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
