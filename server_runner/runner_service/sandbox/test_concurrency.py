"""Integration tests for concurrent sandbox startup.

These tests use real PostgreSQL connections.

Run only against a dedicated test database.
"""

import os
import unittest

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from server_runner.runner_service.models import SandboxRecord

from server_runner.runner_service.sandbox.repository import (
    claim_sandbox_start,
)


class TestConcurrentSandboxStartup(unittest.TestCase):
    """Verify PostgreSQL prevents duplicate sandbox startup claims."""

    @classmethod
    def setUpClass(cls):
        """Connect to an explicitly configured test database."""

        # Require a dedicated test database URL.
        database_url = os.environ.get(
            "CODEVIEW_TEST_DATABASE_URL"
        )

        if not database_url:
            raise unittest.SkipTest(
                "Set CODEVIEW_TEST_DATABASE_URL to run integration tests."
            )

        # Prevent accidentally testing against the production database.
        if "codeview_test_db" not in database_url:
            raise RuntimeError(
                "Integration tests require codeview_test_db."
            )

        cls.engine = create_engine(
            database_url,
            pool_pre_ping=True,
        )

        cls.SessionLocal = sessionmaker(
            bind=cls.engine,
            expire_on_commit=False,
        )

    @classmethod
    def tearDownClass(cls):
        """Close PostgreSQL connections."""

        if hasattr(cls, "engine"):
            cls.engine.dispose()

    def setUp(self):
        """Create a temporary sandbox record."""

        self.sandbox_id = uuid4()

        self.developer_id = 12
        self.group_id = 5

        with self.SessionLocal() as db:

            sandbox = SandboxRecord(
                sandbox_id=self.sandbox_id,
                developer_id=self.developer_id,
                group_id=self.group_id,
                status="prepared",
            )

            db.add(sandbox)
            db.commit()

    def tearDown(self):
        """Remove the temporary sandbox record."""

        with self.SessionLocal() as db:

            sandbox = db.get(
                SandboxRecord,
                self.sandbox_id,
            )

            if sandbox is not None:
                db.delete(sandbox)
                db.commit()

    def test_only_one_request_can_claim_startup(self):
        """Two simultaneous startup claims must not both succeed."""

        # Coordinate both worker threads.
        barrier = Barrier(2)

        def attempt_start():
            """Try to claim the same sandbox from a separate connection."""

            with self.SessionLocal() as db:

                # Wait until both workers are ready.
                barrier.wait(timeout=10)

                try:
                    claim_sandbox_start(
                        db=db,
                        sandbox_id=self.sandbox_id,
                        developer_id=self.developer_id,
                        group_id=self.group_id,
                    )

                    return "success"

                except ValueError:
                    return "rejected"

        # Run both attempts concurrently.
        with ThreadPoolExecutor(max_workers=2) as executor:

            futures = [
                executor.submit(attempt_start)
                for _ in range(2)
            ]

            results = [
                future.result(timeout=20)
                for future in futures
            ]

        # Exactly one startup claim should succeed.
        self.assertEqual(
            results.count("success"),
            1,
        )

        # Exactly one startup claim should be rejected.
        self.assertEqual(
            results.count("rejected"),
            1,
        )

        # Verify the final database status.
        with self.SessionLocal() as db:

            sandbox = db.get(
                SandboxRecord,
                self.sandbox_id,
            )

            self.assertEqual(
                sandbox.status,
                "starting",
            )


if __name__ == "__main__":
    unittest.main()