from pydantic import BaseModel, model_validator, field_validator, Field
from models.enums import Auditory, Discipline, Gender, TrainingType
from typing import List, Optional
from datetime import datetime, timedelta

class UserAddDTO(BaseModel):
    name: str
    email: str
    password: str
    role: str
    age: int
    gender: Gender
    age_type: Auditory = None

    @model_validator(mode="before")
    def validate_age_type(cls, values) -> dict:
        if isinstance(values, dict):
            age = values.get("age")
            age_type = values.get("age_type")

        else:
            age = values.age
            age_type = values.age_type

        if age_type is None:
            if age < 14:
                age = Auditory.CHILDREN
            elif age < 60:
                age_type = Auditory.ADULTS
            else:
                age_type = Auditory.SENIORS

        return values

class UserDTO(UserAddDTO):
    id: int

class TrainingOnInputDTO(BaseModel):
    title: str
    description: Optional[str] = None
    date: str = Field(..., example="2025-12-31")
    time_start: str = Field(..., example="9:00:00")
    time_end: str = Field(..., example="18:00:00")
    type: TrainingType
    discipline: Discipline
    coach_id: int
    individual_for_id: Optional[int] = None
    target_auditory: Optional[Auditory] = Field(default=None, example="adults")  # e.g., "adults", "children"
    target_gender: Optional[Gender] = Field(default=None, example="men")

    @field_validator("date")
    def validate_date(cls, v):
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Date must be in a format 'YYYY-MM-DD'")
        return v
    
    @field_validator("time_start", "time_end")
    def validate_time(cls, v):
        try:
            datetime.strptime(v, "%H:%M:%S")
        except ValueError: 
            raise ValueError("Time must be in a format 'HH:MM:SS'")
        return v

    @model_validator(mode="before")
    def validate_training_model(cls, values) -> dict:
        if isinstance(values, dict):
            type_ = values.get("type")
            individual_for_id = values.get("individual_for_id")
            target_auditory = values.get("target_auditory")
            target_gender = values.get("target_gender")
        
        else:
            type_ = values.type
            individual_for_id = values.individual_for_id
            target_auditory = values.target_auditory
            target_gender = values.target_gender

        if type_ == TrainingType.INDIVIDUAL and not individual_for_id:
            raise ValueError("Individual training must have an id of a specific student")
        if type_ == TrainingType.INDIVIDUAL and (target_auditory or target_gender):
            raise ValueError("An individual traoining can not have a target auditory or target gender. It is for a specific user specified by individual_for_id")
        if type_ == TrainingType.GROUP and individual_for_id:
            raise ValueError("Group training cannot have an id of a specific student")
    
        return values

class TrainingAddDTO(BaseModel):
    title: str
    description: Optional[str] = None
    time_start: datetime
    time_end: datetime
    type: TrainingType
    discipline: Discipline
    coach_id: int
    individual_for_id: Optional[int] = None
    target_auditory: Optional[Auditory] = None  # e.g., "adults", "children"
    target_gender: Optional[Gender] = None


class TrainingDTO(TrainingAddDTO):
    id: int

class UserRelWithSubscriptionsDTO(UserDTO):
    subs: list["TrainingDTO"]

class UserRelWithAvailableDTO(UserDTO):
    avilable: list["TrainingDTO"]

class TrainingRelDTO(TrainingDTO):
    users_on_training: list["UserDTO"]

class WorkloadOfEachCoachDTO(BaseModel):
    name: str
    workload: timedelta

class SubscriptionDTO(BaseModel):
    user_id: int
    training_id: int