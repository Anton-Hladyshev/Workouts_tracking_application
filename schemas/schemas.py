from pydantic import BaseModel, model_validator
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
            raise ValueError("Individual training must have an individual_for_id")
        if type_ == TrainingType.INDIVIDUAL and (target_auditory or target_gender):
            raise ValueError("An individual traoining can not have a target audiatory or target gender. It is for a specific user specified by individual_for_id")
        if type_ == TrainingType.GROUP and individual_for_id:
            raise ValueError("Group training cannot have an individual_for_id")
    
        return values

class TrainigSearchDTO(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    time_start: Optional[datetime] = None
    time_end: Optional[datetime] = None
    type: Optional[TrainingType] = None
    discipline: Optional[Discipline] = None
    coach_id: Optional[int] = None
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