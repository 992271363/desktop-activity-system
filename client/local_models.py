from sqlalchemy import Column, Integer, String, DateTime, Boolean 
from sqlalchemy.orm import declarative_base
Base = declarative_base()
class ActivityLog(Base):
    __tablename__ = 'activity_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, default=0)
    process_name = Column(String, nullable=False)
    window_title = Column(String, nullable=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    duration_seconds = Column(Integer, nullable=False)

    synced = Column(Boolean, default=False, nullable=False)
    def __repr__(self):
        return (f"<ActivityLog(id={self.id}, process='{self.process_name}', "
                f"duration={self.duration_seconds}s, synced={self.synced})>") 