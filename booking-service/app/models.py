from sqlalchemy import Boolean, Column, Integer, String

from .database import Base


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    event_name = Column(String, index=True, nullable=False)
    seat_number = Column(String, nullable=False)
    is_confirmed = Column(Boolean, default=False, nullable=False)