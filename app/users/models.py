from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base

class User(Base):
    __tablename__ = 'users'

    id:Mapped[str] = mapped_column(primary_key=True)
    display_name:Mapped[str] = mapped_column(nullable=False)