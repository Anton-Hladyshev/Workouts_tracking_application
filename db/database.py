import sys
import pathlib
from typing import Any, Dict, List, Sequence, Tuple


root_path = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_path))

from sqlalchemy import delete, exists, select, and_, or_
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload
from sqlalchemy.dialects.postgresql import insert as pg_insert
from app.config import settings
from models.models import Auditory, Gender, User, Training, TrainingType, Discipline, Subscription, AvailableTraining
from datetime import datetime
from schemas.schemas import *
from schemas.exceptions import ForbiddenActionError

async_engine = create_async_engine(
    url=settings.get_db_url_with_asyncpg, 
    echo=True,
    pool_size=5,
    max_overflow=10
)

async_session_factory = async_sessionmaker(bind=async_engine)

class ORMBase(): 
    @staticmethod
    async def get_all_users(session: AsyncSession | None = None) -> list[UserDTO]:
        if session is None:
            async with async_session_factory() as session:
                result = await session.execute(select(User))
                return [UserDTO.model_validate(user, from_attributes=True) for user in result.scalars().all()]
        else:
            result = await session.execute(
                select(
                    User
                )
            )
            return [UserDTO.model_validate(user, from_attributes=True) for user in result.scalars().all()]
        
    @staticmethod
    async def get_all_trainings(session: AsyncSession | None = None) -> List[TrainingDTO]:
        if session is None:
            async with async_session_factory() as session:
                query = select(
                    Training
                )

                result = await session.execute(query)
                return [TrainingDTO.model_validate(training, from_attributes=True) for training in result.scalars().all()]
            
        else:
            result = await session.execute(
                select(
                    Training
                )
            )
            return [TrainingDTO.model_validate(training, from_attributes=True) for training in result.scalars().all()]
        
    @staticmethod 
    async def get_user_by_id(id: int, session: AsyncSession | None = None) -> UserDTO | None:   # throws MultipleResultsFound
        if session is None:
            async with async_session_factory() as session:
                query = select(
                    User
                ).where(
                    User.id == id
                )

                result = await session.execute(query)
                return UserDTO.model_validate(result.scalar_one_or_none(), from_attributes=True)
        else:
            result = await session.execute(
                select(
                    User
                ).where(
                    User.id == id
                )
            )
            return UserDTO.model_validate(result.scalar_one_or_none(), from_attributes=True)
        
    @staticmethod
    async def get_user_by_email(email: str, session: AsyncSession | None = None) -> UserDTO | None: # throws MultipleResultsFound
        if session is None:
            async with async_session_factory() as session:
                query = select(
                    User
                ).where(
                    User.email == email
                )

                result = await session.execute(query)
                return UserDTO.model_validate(result.scalar_one_or_none(), from_attributes=True)
        
        else:
            result = await session.execute(
                select(
                    User
                ).where(
                    User.email == email
                )
            )
            return UserDTO.model_validate(result.scalar_one_or_none(), from_attributes=True)
        
    @staticmethod
    async def get_users_by_role(role: str, session: AsyncSession | None = None) -> Sequence[UserDTO]:
        if session is None:
            async with async_session_factory() as session:
                query = select(
                    User
                ).where(
                    User.role == role
                )

                result = await session.execute(query)
                return [UserDTO.model_validate(user, from_attributes=True) for user in result.scalars().all()]
        else:
            result = await session.execute(
                select(
                    User
                ).where(
                    User.role == role
                )
            )
            return [UserDTO.model_validate(user, from_attributes=True) for user in result.scalars().all()]
        
    @staticmethod
    async def user_exists(name: str, email: str) -> bool:
        async with async_session_factory() as session:
            query = select(
                exists().where(
                    (User.name == name) | (User.email == email)
                )
            )

            result = await session.execute(query)
            return result.scalar()
        
    @staticmethod
    async def get_training_by_id(id: int, session: AsyncSession | None = None) -> TrainingDTO | None:
        if session is None:
            async with async_session_factory() as session:
                query = select(
                    Training
                ).where(
                    Training.id == id
                )

                result = await session.execute(query)
                return TrainingDTO.model_validate(result.scalar_one_or_none(), from_attributes=True)
        else:
            result = await session.execute(
                select(
                    Training
                ).where(
                    Training.id == id
                )
            )
            return TrainingDTO.model_validate(result.scalar_one_or_none(), from_attributes=True)
    
    @staticmethod
    async def get_user_by(session: AsyncSession | None = None, **kwargs) -> UserDTO | None:
        filters = []

        for key, value in kwargs.items():
            if hasattr(User, key) and value is not None:
                filters.append(User.__dict__[key] == value)

        query = select(
                    User
                ).where(
                    and_(*filters)
                )

        if session is None:
            async with async_session_factory() as session:
                result = await session.execute(
                    query
                )

                result = result.scalar_one_or_none()

                if result is not None:
                    return UserDTO.model_validate(result, from_attributes=True)
                return None
            
        else:
            result = await session.execute(
                query
            )

            result = result.scalar_one_or_none()

            if result is not None:
                return UserDTO.model_validate(result, from_attributes=True)
            return None

    @staticmethod
    async def get_training_by(session: AsyncSession | None = None, **kwargs) -> List[TrainingDTO | None]:
        filters = []

        filter_map = {
            'title': Training.title,
            'time_start': Training.time_start, 
            'time_end': Training.time_end,
            'type': Training.type,
            'discipline': Training.discipline,
            'coach_id': User.id
        }

        for key, value in kwargs.items():
            column = filter_map.get(key)
            if column is not None and value is not None:
                filters.append(column == value) 

        query = select(
            Training
        ).where(
            and_(
                *filters
            )
        )
        
        if session is None:
            async with async_session_factory() as session:
                result = await session.execute(query)
                return [TrainingDTO.model_validate(training, from_attributes=True) for training in result.scalars().all()]
            
        else:
            result = await session.execute(query)
            return [TrainingDTO.model_validate(training, from_attributes=True) for training in result.scalars().all()]

    @staticmethod
    async def training_exists(session: AsyncSession | None = None, **kwargs) -> bool:
        filters = []

        filter_map = {
            'title': Training.title,
            'time_start': Training.time_start,
            'time_end': Training.time_end,
            'type': Training.type,
            'discipline': Training.discipline,
            'coach_id': User.id
        }

        for key, value in kwargs.items():
            column = filter_map.get(key)
            if column is not None and value is not None:
                filters.append(column == value)
        query = select(
            exists().where(
                and_(
                    *filters
                )
            )
        ).select_from(Training).join(User, User.id == Training.coach_id)

        if session is None:
            async with async_session_factory() as session:
                

                result = await session.execute(query)
                return result.scalar()
            
        else:
            result = await session.execute(query)
            return result.scalar()

    @staticmethod 
    async def register_new_user(user: UserAddDTO, session: AsyncSession | None = None) -> None:
        if not session:
            async with async_session_factory() as session:
                session.add(User.from_dto(user))
                await session.commit()

        else:
            session.add(User.from_dto(user))
            await session.commit()


# service for a client
class ClientService(): 
    def __init__(self, user: UserDTO):
        self.user = user
        
    async def show_my_trainings(self) -> List[Training]:
        async with async_session_factory() as session:
            query = select(
                User
            ).options(
                selectinload(User.subs)
            ).where(
                User.id == self.user.id
            )

            result = await session.execute(query)
            return [TrainingDTO.model_validate(training, from_attributes=True) for training in result.scalar_one_or_none().subs]
        
    async def show_available_trainings(self, session: AsyncSession | None = None, **kwargs) -> List[TrainingDTO]:
        """Show available trainigs for the user by filtering with kwargs."""
        filters = []

        filter_map = {
            'title': Training.title,
            'description': Training.description,
            'time_start': Training.time_start,
            'time_end': Training.time_end,
            'type': Training.type,
            'discipline': Training.discipline,
            'coach_id': User.id,
            "individual_for_id": Training.individual_for_id,
            "target_auditory": Training.target_auditory,
            "target_gender": Training.target_gender
        }

        for key, value in kwargs.items():
            column = filter_map[key]
            if column is not None and value is not None:
                filters.append(column == value)

        query = select(
                Training
            ).join(
                User.avilable
            ).where(
                User.id == self.user.id, *filters
            )
        
        if session is None:
            async with async_session_factory() as session:
                result = await session.execute(query)
                return [TrainingDTO.model_validate(training, from_attributes=True) for training in result.scalars().all()]
            
        else:
            result = await session.execute(query)
            return [TrainingDTO.model_validate(training, from_attributes=True) for training in result.scalars().all()]
        

    async def subscribe_to_training(self, training_id: int) -> SubscriptionDTO:
        async with async_session_factory() as session:
            try:

                if not await self.available_training_exists(training_id, session):
                    raise ValueError("You are not available for this training")
                
                subscription_data = SubscriptionDTO(
                    user_id=self.user.id,
                    training_id=training_id
                )

                insert_stmt = pg_insert(
                    Subscription
                ).values(
                    student_id=subscription_data.user_id,
                    training_id=subscription_data.training_id
                ).on_conflict_do_nothing(
                    index_elements=['student_id', 'training_id']
                )

                delete_stmt = delete(
                    AvailableTraining
                ).where(
                    AvailableTraining.user_id == self.user.id,
                    AvailableTraining.training_id == training_id
                )

                # delete the training from available trainings
                await session.execute(
                    insert_stmt
                )
                await session.execute(
                    delete_stmt
                )

                await session.commit()

                return subscription_data

            except Exception as ex:
                await session.rollback()
                raise ex

    async def available_training_exists(self, training_id: int, session: AsyncSession | None = None) -> bool:
        """Check if a user is available for a specific training."""
        query = select(
            exists().where(
                AvailableTraining.user_id == self.user.id,
                AvailableTraining.training_id == training_id
            )
        )   
        if session is None:
            async with async_session_factory() as session:
                result = await session.execute(query)
                return result.scalar()
        else:
            result = await session.execute(query)
            return result.scalar()


    def get_user(self) -> UserDTO:
        return self.user
        

# service for a coach
class CoachService():
    def __init__(self, user: UserDTO):
        self.user = user

    @staticmethod
    async def calculate_target_users(session: AsyncSession, training: Training) -> Dict[str, int]:
        data = []

        # Case of individual training
        if training.type == TrainingType.INDIVIDUAL: 
            data.append({
                "user_id": training.individual_for_id,
                "training_id": training.id
            })
                
        # Case of group training
        else:
            query = select(
                User.id
            ).where(
                or_(training.target_auditory is None, 
                    training.target_auditory == User.age_type,),
                or_(training.target_gender is None, 
                    training.target_gender == User.gender)
            )

            result_query = await session.execute(query)

            user_ids = [row.id for row in result_query]

            data.extend([{"user_id": uid, "training_id": training.id} for uid in user_ids])

        return data


    async def create_training(self, **data: Dict) -> TrainingAddDTO:
        """
        Creates a new training session and stores it in the database.
        Parameters:
            **data (Dict): A dictionary containing the following keys:
                - title (str): The title of the training session.
                - description (str, optional): A description of the training session. Defaults to an empty string.
                - date (str): The date of the training session in the format 'YYYY-MM-DD'.
                - time_start (str): The start time of the training session in the format 'HH:MM:SS'.
                - time_end (str): The end time of the training session in the format 'HH:MM:SS'.
                - type (str): The type of training.
                - discipline (str): The discipline of the training.
                - individual_for_id (int, optional): The ID of the individual for whom the training is intended. Defaults to None.
                - target_auditory (str, optional): The target auditory for the training. Defaults to None.
                - target_gender (str, optional): The target gender for the training. Defaults to None.
        Returns:
            TrainingAddDTO: An object containing the details of the created training session.
        Raises:
            Exception: If there is an error during the creation of the training session.
        """
        async with async_session_factory() as session:
            date_time_start = datetime.strptime(f"{data["date"]} {data["time_start"]}", "%Y-%m-%d %H:%M:%S")
            date_time_end = datetime.strptime(f"{data["date"]} {data["time_end"]}", "%Y-%m-%d %H:%M:%S")

            training_data = TrainingAddDTO(
                title=data["title"],
                description=data.get("description", ""),
                time_start=date_time_start,
                time_end=date_time_end,
                type=TrainingType(data["type"]),
                discipline=Discipline(data["discipline"]),
                coach_id=self.user.id,
                individual_for_id=data.get("individual_for_id", None),
                target_auditory=Auditory(data.get("target_auditory")) if data.get("target_auditory") else None,
                target_gender=Gender(data.get("target_gender")) if data.get("target_gender") else None
            )

            training = Training(
                title=training_data.title,
                description=training_data.description,
                time_start=training_data.time_start,
                time_end=training_data.time_end,
                type=training_data.type,
                discipline=training_data.discipline,
                coach_id=training_data.coach_id,
                individual_for_id=training_data.individual_for_id,
                target_auditory=training_data.target_auditory,
                target_gender=training_data.target_gender
            )

            session.add(training)
            await session.flush()

            target_users_data = await self.calculate_target_users(session, training)
                    
            if target_users_data:
                stmt = pg_insert(AvailableTraining).values(target_users_data).on_conflict_do_nothing(index_elements=['user_id', 'training_id'])
                await session.execute(stmt)
                await session.commit()

                return training_data

            
            
    async def update_training(self, training_id: int, **kwargs: Dict[str, Any]) -> None:
            async with async_session_factory() as session:
                try:
                    if not kwargs:
                        raise ValueError("No fields to update")
                    
                    training = await ORMBase.get_training_by_id(training_id)
                    filter_params = {
                        "type": training.type,
                        "target_auditory": training.target_auditory,
                        "target_gender": training.target_auditory
                    }

                    if not training:
                        raise ValueError("Training not found")

                    for key, value in kwargs.items():
                        if hasattr(training, key):
                            setattr(training, key, value)

                    session.add(training)
                    await session.flush()

                    #if the training type or target auditory, or target gender has changed, we need to recalculate the target users
                    if not (training.type == filter_params["type"] and training.target_auditory == filter_params["target_auditory"] and training.target_gender == filter_params["target_gender"]):
                        data = []

                        # delete old target users for this training
                        await session.execute(
                            delete(
                                AvailableTraining
                                ).where(
                                    AvailableTraining.training_id == training.id
                                )
                        )

                        # add new target users for this training
                        data = await self.calculate_target_users(session, training)

                        if data:
                            stmt = pg_insert(AvailableTraining).values(data).on_conflict_do_nothing(index_elements=['user_id', 'training_id'])
                            await session.execute(stmt)

                    await session.commit()

                except Exception as ex:
                    await session.rollback()
                    raise ex
                
    async def delete_training(self, training_id: int) -> None:
        async with async_session_factory() as session:
            training = await ORMBase.get_training_by_id(training_id)
            if not training:
                raise ValueError("Training not found")
            if training.coach_id != self.user.id:
                raise ForbiddenActionError("You do not have permission to delete this training.")

            await session.execute(
                delete(Training).where(Training.id == training_id)
            )
            await session.commit()

    def get_user(self) -> UserDTO:
        return self.user
            