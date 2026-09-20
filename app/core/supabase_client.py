import os
from typing import Optional
from app.core.config import settings
from app.core.logging import logger


class SupabaseManager:
    """
    Manager for Supabase Client SDK and PostgreSQL SQLAlchemy connection.
    Includes sandbox fallback when credentials are not configured.
    """

    def __init__(self):
        self.url = settings.SUPABASE_URL
        self.key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY
        self.db_url = settings.SUPABASE_DB_URL
        self.client = None
        self.engine = None
        self.is_connected = False
        self._init_client()

    def _init_client(self):
        if self.url and self.key:
            try:
                from supabase import create_client, Client
                self.client: Optional[Client] = create_client(self.url, self.key)
                self.is_connected = True
                logger.info(f"Connected to Supabase Project: {self.url}")
            except Exception as e:
                logger.warning(f"Failed to initialize Supabase SDK client: {e}")
                self.is_connected = False

        if self.db_url:
            try:
                from sqlalchemy import create_engine
                self.engine = create_engine(self.db_url, pool_pre_ping=True)
                logger.info("Initialized SQLAlchemy engine for Supabase PostgreSQL.")
            except Exception as e:
                logger.warning(f"Failed to initialize Supabase SQLAlchemy engine: {e}")


supabase_manager = SupabaseManager()
