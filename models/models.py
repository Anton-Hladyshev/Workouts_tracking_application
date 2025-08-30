import sys
import pathlib

from models.enums import Auditory, Discipline, Gender, Role, TrainingType, UserType
from schemas.schemas import TrainingAddDTO, UserAddDTO, UserDTO
root_path = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_path))

from typing import Annotated, Any, Dict, List
from sqlalchemy import Table, Column, Integer, String, MetaData, DateTime, ForeignKey, Index
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship
from enum import Enum


intpk = Annotated[int, mapped_column(primary_key=True, autoincrement=True)] # Primary key with autoincrement custom type
TrainingSchedule = Annotated[DateTime, mapped_column(DateTime(timezone=True))] # Custom type for training schedule with timezone


class Base(DeclarativeBase): # Base class for all models
    repr_cols_num = 3
    repr_cols = tuple()

    def __repr__(self) -> str:
        attrs = []

        for idx, key in enumerate(self.__table__.columns.keys()):
            if idx < self.repr_cols_num or key in self.repr_cols:
                value = getattr(self, key)
                attrs.append(f"{key}: {value}")
        return f"<{self.__class__.__name__} {', '.join(attrs)}>"


class User(Base): # Model for user
    __tablename__ = "users"

    id: Mapped[intpk]
    age: Mapped[int] = mapped_column(Integer, nullable=True)
    age_type: Mapped[Auditory] = mapped_column(SQLAlchemyEnum(Auditory), nullable=False, default=Auditory.ADULTS)
    gender: Mapped[Gender] = mapped_column(SQLAlchemyEnum(Gender), nullable=True)
    role: Mapped[Role]
    user_type: Mapped[UserType] = mapped_column(SQLAlchemyEnum(UserType), 
                                                               nullable=False, default=UserType.NON_COMPETITOR)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(128), nullable=False)

    subs: Mapped[List["Training"]] = relationship(
        back_populates="users_on_training",
        secondary="subscriptions",
    )

    avilable: Mapped[List["Training"]] = relationship(
        back_populates="targeted_users",
        secondary="available_trainings"
    )

    interests: Mapped[List["Interest"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("user_age_type_index", "age_type"),
        Index("user_gender_index", "gender")
    )

    @classmethod
    def from_dto(cls, data: UserAddDTO) -> "User":
        data = data.model_dump() # Convert Pydantic model to dict
        return cls(
            **data
        )

    #reps_cols = ("id", "name", "subs")


class Training(Base): # Model for training
    __tablename__ = 'trainings'

    id: Mapped[intpk]
    title: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    time_start: Mapped[TrainingSchedule]
    time_end: Mapped[TrainingSchedule]
    target_auditory: Mapped[Auditory] = mapped_column(SQLAlchemyEnum(Auditory), nullable=True, default=None) # Target auditory for training, if None then it's for all
    target_gender: Mapped[Gender] = mapped_column(SQLAlchemyEnum(Gender), nullable=True, default=None) # Target gender for training, if None then it's for all
    target_user_type: Mapped[UserType] = mapped_column(SQLAlchemyEnum(UserType), nullable=True, default=None) # Target user type for training, if None then it's for all
    type: Mapped[TrainingType]
    individual_for_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True) # Individual training for a specific user, if None then it's a group training
    discipline: Mapped[Discipline]
    coach_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE")) # In a logic i need to check if a user with this idis a coach

    users_on_training: Mapped[List[User]] = relationship(
        back_populates="subs",
        secondary="subscriptions",
    )

    targeted_users: Mapped[List["User"]] = relationship(
        back_populates="avilable",
        secondary="available_trainings"
    )

    __table_args__ =(
        Index("training_target_auditory_index", "target_auditory"),
        Index("training_target_gemder_index", "target_gender")
    )

    @classmethod
    def from_dto(cls, data: "TrainingAddDTO") -> "Training":
        data = data.model_dump()
        return cls(
            **data
        )

    #repr_cols = ("id", "title", "description", "type", "discipline")
    


class Subscription(Base): # Model for subscription
    __tablename__ = 'subscriptions'

    student_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    training_id: Mapped[int] = mapped_column(ForeignKey("trainings.id", ondelete="CASCADE"), primary_key=True)


class AvailableTraining(Base): # Represents available training for a specific user. The evaluation is based on the type of training, target auditory, target gender, and user type.
    __tablename__ = 'available_trainings'

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    training_id: Mapped[int] = mapped_column(ForeignKey("trainings.id", ondelete="CASCADE"), primary_key=True)

    __table_args__ = (
        Index("available_trainings_training_id_index", "training_id"),
        Index("available_trainings_user_id_index", "user_id")
    )

class Interest(Base): # Model for user interests
    __tablename__ = 'interests'

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    discipline: Mapped[Discipline] = mapped_column(SQLAlchemyEnum(Discipline), primary_key=True)

    user: Mapped["User"] = relationship(
        back_populates="interests"
    )

    __table_args__ = (
        Index("interest_user_id_index", "user_id"),
        Index("interest_discipline_index", "discipline")
    )