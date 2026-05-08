from dataclasses import dataclass
from typing import List, Optional, Tuple

from local_database import SessionLocal
from local_models import WatchedApplication
from tracking_service import add_or_get_watched_app


@dataclass
class AppInfo:
    exe_path: str
    exe_name: str
    total_focus_seconds: int
    total_lifetime_seconds: int


class AppRepository:

    @staticmethod
    def get_all_apps() -> List[AppInfo]:
        db = SessionLocal()
        try:
            apps = db.query(WatchedApplication).all()
            return [
                AppInfo(
                    exe_path=app.executable_path,
                    exe_name=app.executable_name,
                    total_focus_seconds=app.summary.total_focus_time_seconds if app.summary else 0,
                    total_lifetime_seconds=app.summary.total_lifetime_seconds if app.summary else 0,
                )
                for app in apps
            ]
        finally:
            db.close()

    @staticmethod
    def get_watched_apps_info() -> List[Tuple[str, str]]:
        db = SessionLocal()
        try:
            apps = db.query(WatchedApplication).all()
            return [(app.executable_path, app.executable_name) for app in apps]
        finally:
            db.close()

    @staticmethod
    def get_app_by_path(exe_path: str) -> Optional[WatchedApplication]:
        db = SessionLocal()
        try:
            return db.query(WatchedApplication).filter_by(executable_path=exe_path).first()
        finally:
            db.close()

    @staticmethod
    def delete_app_by_path(exe_path: str) -> None:
        db = SessionLocal()
        try:
            db.query(WatchedApplication).filter_by(executable_path=exe_path).delete()
            db.commit()
        finally:
            db.close()

    @staticmethod
    def add_app(exe_path: str, exe_name: str) -> None:
        db = SessionLocal()
        try:
            add_or_get_watched_app(db, exe_path, exe_name)
        finally:
            db.close()

    @staticmethod
    def app_exists(exe_path: str) -> bool:
        db = SessionLocal()
        try:
            return db.query(WatchedApplication).filter_by(executable_path=exe_path).first() is not None
        finally:
            db.close()
