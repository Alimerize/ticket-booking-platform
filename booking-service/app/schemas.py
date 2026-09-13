from pydantic import BaseModel, ConfigDict, Field


class BookingBase(BaseModel):
    user_id: int = Field(..., gt=0, description="ID пользователя (положительное число)")
    event_name: str = Field(..., min_length=1, max_length=200, description="Название события")
    seat_number: str = Field(..., min_length=1, max_length=20, description="Номер места")


class BookingCreate(BookingBase):
    pass


class BookingRead(BookingBase):
    id: int
    is_confirmed: bool

    model_config = ConfigDict(from_attributes=True)