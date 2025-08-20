from pydantic import BaseModel, EmailStr, model_validator, field_validator, Field
from models.enums import Auditory, Discipline, Gender, Role, TrainingType, UserType
from typing import List, Optional
from datetime import datetime, timedelta, time, date as _date

from schemas.exceptions import RegistrationError, TimeValidationError, BusinessRulesValidationError

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

class UserRegisterDTO(BaseModel):
    name: str = Field(default="Your name")
    email: EmailStr
    password: str
    password_confirmation: str
    role: Role = Field(description="Specify your role: a coach or a student")
    birth_date: _date = Field(description="Your birthdate")
    gender: Gender = Field(description="Your gender")
    level: UserType = Field(description="Your level")

    @model_validator(mode="after")
    def verify_passwords_matching(self):
        if self.password != self.password_confirmation:
            raise RegistrationError("Passwords must match")
        return self
    
class UserLoginDTO(BaseModel):
    email: EmailStr
    password: str

    @model_validator(mode="after")
    def verify_email_format(self):
        if not self.email or "@" not in self.email:
            raise RegistrationError("Email must be a valid email address")
        return self
    
class AccessToken(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    identifier: str | None = None

class TrainingOnInputDTO(BaseModel):
    title: str = Field(default="New training", description="A title of a new training")
    description: Optional[str] = Field(default=" ", description="Description of a training")
    date: _date = Field(..., example="2025-12-31")
    time_start: time = Field(..., example="9:00:00")
    time_end: time = Field(..., example="18:00:00")
    type: TrainingType = Field(default=TrainingType.GROUP, description="A type of a training: group or individual. For a individual training the parameter individual_for_id is required")
    discipline: Discipline = Field(default=Discipline.MMA, description="Discipline of a training: MMA, striking, boxe feminin, wrestling, BJJ, physical_preparation")
    individual_for_id: Optional[int] = Field(default=None, description="Id of a person for whom this training is dedicated. Should be specified only if the type is 'individual'")
    target_auditory: Optional[Auditory] = Field(default=None, example="adults", description="For clients of which specific age group this training is dedicated. Shold be specified if type is 'grpoup'. If not specified, training is dedicated for all age groups")  # e.g., "adults", "children"
    target_gender: Optional[Gender] = Field(default=None, example="men", description="For clients of which specific gender this training is dedicated. Shold be specified if type is 'grpoup'. If not specified, training is dedicated for all genders")

    @field_validator("date", mode="before")
    def validate_date(cls, v):
        try:
            if v is not None:
                datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise TimeValidationError("Date must be in a format 'YYYY-MM-DD'")
        return v
    
    @field_validator("time_start", "time_end", mode="before")
    def validate_time(cls, v):
        try:
            if v is not None:
                datetime.strptime(v, "%H:%M:%S")
            return v
        except ValueError:
            raise TimeValidationError("Time should be in a format 'HH:MM:SS'")
        
    @model_validator(mode="after")
    def check_time_and_business_rules(self):
        #check time
        if self.time_start is not None and self.time_end is not None:
            if self.time_start > self.time_end:
                raise TimeValidationError("The time of the end of a training should be grater then the time of the start of the training")
        
        #check business rules
        type_ = self.type
        individual_for_id = self.individual_for_id
        target_auditory = self.target_auditory
        target_gender = self.target_gender

        if type_ == TrainingType.INDIVIDUAL and not individual_for_id:
            raise BusinessRulesValidationError("Individual training must have an id of a specific student")
        if type_ == TrainingType.INDIVIDUAL and (target_auditory or target_gender):
            raise BusinessRulesValidationError("An individual traoining can not have a target auditory or target gender. It is for a specific user specified by individual_for_id")
        if type_ == TrainingType.GROUP and individual_for_id:
            raise BusinessRulesValidationError("Group training cannot have an id of a specific student")
        
        return self
    

class TrainingOnInputToUpdateDTO(TrainingOnInputDTO):
    title: Optional[str] = None
    description: Optional[str] = None
    date: Optional[_date] = Field(default=None, example="2025-12-31")
    time_start: Optional[time] = Field(default=None, example="9:00:00")
    time_end: Optional[time] = Field(default=None, example="18:00:00")
    type: Optional[TrainingType] = None
    discipline: Optional[Discipline] = None
    individual_for_id: Optional[int] = None
    target_auditory: Optional[Auditory] = Field(default=None, example="adults")  # e.g., "adults", "children"
    target_gender: Optional[Gender] = Field(default=None, example="men")

class TrainingSearchDTO(BaseModel):
    title: Optional[str] = Field(default=None, description="A title of a new training")
    description: Optional[str] = Field(default=None, description="Description of a training")
    date_start_search: Optional[_date] = Field(default_factory=lambda: datetime.today().date(), example="2024-12-31")
    date_end_search: Optional[_date] = Field(default=None, example="2025-12-31")
    time_start_search: Optional[time] = Field(default=datetime.strptime("00:00:00", "%H:%M:%S").time(), example="9:00:00")
    time_end_search: Optional[time] = Field(default=datetime.strptime("23:59:59", "%H:%M:%S").time(), example="18:00:00")
    type: Optional[TrainingType] = Field(default=None, description="A type of a training: group or individual. For a individual training the parameter individual_for_id is required")
    discipline: Optional[Discipline] = Field(default=None, description="Discipline of a training: MMA, striking, boxe feminin, wrestling, BJJ, physical_preparation")
    individual_for_id: Optional[int] = Field(default=None, description="Id of a person for whom this training is dedicated. Should be specified only if the type is 'individual'")
    target_auditory: Optional[Auditory] = Field(default=None, example="adults", description="For clients of which specific age group this training is dedicated. Shold be specified if type is 'grpoup'. If not specified, training is dedicated for all age groups")  # e.g., "adults", "children"
    target_gender: Optional[Gender] = Field(default=None, example="men", description="For clients of which specific gender this training is dedicated. Shold be specified if type is 'grpoup'. If not specified, training is dedicated for all genders")

    @field_validator("date_start_search", "date_end_search", mode="before")
    def validate_date(cls, v):
        if isinstance(v, _date):
            return v
        if isinstance(v, str):
            try:
                return datetime.strptime(v, "%Y-%m-%d").date()
            except ValueError:
                raise TimeValidationError("Date must be in a format 'YYYY-MM-DD'")
        return v

    @field_validator("time_start_search", "time_end_search", "time_start_search", "time_end_search", mode="before")
    def validate_time(cls, v):
        if isinstance(v, time):
            return v
        if isinstance(v, str):
            try:
                return datetime.strptime(v, "%H:%M:%S").time()
            except ValueError:
                raise TimeValidationError("Time should be in a format 'HH:MM:SS'")
        return v

    @model_validator(mode="after")
    def set_date_end_search_default_value(self):
        if self.date_start_search and not self.date_end_search:
            self.date_end_search = self.date_start_search + timedelta(days=7)
        return self
        
    @model_validator(mode="after")
    def check_time_and_business_rules(self):
        #check time
        if self.time_start_search is not None and self.time_end_search is not None:
            if self.time_start_search > self.time_end_search:
                raise TimeValidationError("The time of the end of a training should be grater then the time of the start of the training")
            
        if self.date_start_search is not None and self.date_end_search is not None:
            if self.date_start_search > self.date_end_search:
                raise TimeValidationError("The date of the end of a search period should be grater then the date of the start of the search period")
        
        #check business rules
        type_ = self.type
        individual_for_id = self.individual_for_id
        target_auditory = self.target_auditory
        target_gender = self.target_gender

        if type_ == TrainingType.INDIVIDUAL and (target_auditory or target_gender):
            raise BusinessRulesValidationError("An individual traoining can not have a target auditory or target gender. It is for a specific user specified by individual_for_id")
        if type_ == TrainingType.GROUP and individual_for_id:
            raise BusinessRulesValidationError("Group training cannot have an id of a specific student")
        
        return self

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