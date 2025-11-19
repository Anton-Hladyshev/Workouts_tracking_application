from datetime import datetime
from typing import Dict
from sqlalchemy import and_, delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import selectinload
from .base_repository import BaseRepository
from sqlalchemy.ext.asyncio import AsyncSession

from models.enums import Role, TrainingType
from models.models import AvailableTraining, Interest, Training, User
from schemas.schemas import TrainingAddDTO, TrainingDTO, UserDTO


class TrainingRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__()
        self.session = session

    async def add(self, item: TrainingAddDTO) -> Training:
        training = Training(
                title=item.title,
                description=item.description,
                time_start=item.time_start,
                time_end=item.time_end,
                type=item.type,
                discipline=item.discipline,
                coach_id=item.coach_id,
                individual_for_id=item.individual_for_id,
                target_auditory=item.target_auditory,
                target_gender=item.target_gender,
                target_usertype=item.target_usertype
        )

        self.session.add(training)
    
    async def get(self, item_id: int) -> TrainingDTO | None:
        request = select(
            Training
        ).where(
            Training.id == item_id
        )
            
        result = await self.session.scalar(request)
        return TrainingDTO.model_validate(result, from_attributes=True) if result else None

    async def remove(self, item_id: int) -> None:
        query_select = select(
            Training
        ).where(
            Training.id == item_id
        )

        training = await self.session.scalar(query_select)

        if training:
            await self.session.delete(training)

    async def get_students_of_training(self, training_id: int) -> list[User]:
        training_exists = await self.get(training_id)
        if not training_exists:
            raise ValueError("Training not found")
        
        query = select(
            Training
        ).options(
            selectinload(Training.users_on_training)
        ).where(
            Training.id == training_id
        )

        result = await self.session.execute(query)

        return [UserDTO.model_validate(user, from_attributes=True) for user in result.scalar_one_or_none().users_on_training]

    async def update(self, training: Training, **kwargs) -> None:
        updated_date = kwargs.get("date", training.time_start.date())
        updated_time_start = kwargs.get("time_start", training.time_start.time())
        updated_time_end = kwargs.get("time_end", training.time_end.time())

        new_time_start = datetime.combine(updated_date, updated_time_start)
        kwargs["time_start"] = new_time_start
        new_time_end = datetime.combine(updated_date, updated_time_end)
        kwargs["time_end"] = new_time_end


        for key, value in kwargs.items():
            if hasattr(training, key):
                setattr(training, key, value)

    async def list_all(self) -> list[TrainingDTO]:
        query_select = select(Training)
        result = await self.session.scalars(query_select)
        trainings = result.all()
        return [TrainingDTO.model_validate(training, from_attributes=True) for training in trainings]
    
    async def calculate_target_users(self, training: TrainingDTO) -> list[Dict[str, int]]:
        data = []

        # Case of individual training
        if training.type == TrainingType.INDIVIDUAL: 
            data.append({
                "user_id": training.individual_for_id,
                "training_id": training.id
            })
                
        # Case of group training
        else:
            filters = []
            filter_map = {
                "target_auditory": User.age_type,
                "target_gender": User.gender,
                "target_usertype": User.user_type
            }
            training_dict = training.model_dump(exclude_none=True)
            for key, value in training_dict.items():
                if key in filter_map:
                    filters.append(filter_map[key] == value)
            query = select(
                User.id
            ).join(
                Interest, Interest.user_id == User.id
            ).where(
                and_(
                    User.role == Role.STUDENT,
                    Interest.discipline == training.discipline,
                    *filters
                )
            )

            result_query = await self.session.execute(query)

            user_ids = [row.id for row in result_query]

            data.extend([{"user_id": uid, "training_id": training.id} for uid in user_ids])

        return data
    
    async def clear_target_users(self, training_id: int) -> None:
        query_delete = delete(
            AvailableTraining
        ).where(
            AvailableTraining.training_id == training_id
        )

        await self.session.execute(query_delete)

    async def add_target_users(self, data_target_users: list[Dict[str, int]]):
        if data_target_users:
            stmt = pg_insert(AvailableTraining).values(data_target_users).on_conflict_do_nothing(index_elements=['user_id', 'training_id'])
            await self.session.execute(stmt)