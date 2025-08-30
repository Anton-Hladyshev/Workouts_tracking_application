import sys
import pathlib

root_path = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_path))

from typing import Any, Dict, List, Sequence
from schemas.exceptions import InvalidPermissionsError
from sqlalchemy import delete, exists, select, and_, or_, cast, Date, Time
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload
from sqlalchemy.dialects.postgresql import insert as pg_insert
from app.config import settings
from models.models import Interest, User, Training, TrainingType, Subscription, AvailableTraining
from datetime import date, datetime, time
from schemas.schemas import *
from argon2 import PasswordHasher

async_engine = create_async_engine(
    url=settings.get_db_url_with_asyncpg, 
    echo=True,
    pool_size=5,
    max_overflow=10
)

ph = PasswordHasher()

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
    async def user_exists(name: str, email: str, session: AsyncSession | None = None) -> bool:
        query = select(
                exists().where(
                    (User.name == name) | (User.email == email)
                )
            )
        
        if session is None:
            async with async_session_factory() as async_session:
                result = await async_session.execute(query)
                return result.scalar()
        else:
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
            'id': Training.id,
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
    async def subscription_exists(session: AsyncSession | None, user_id: int, training_id: int):
        query = select(
                exists().where(
                    Subscription.student_id == user_id,
                    Subscription.training_id == training_id
                )
            )
        if not session:
            async with async_session_factory() as session:
                subscription_exeists = await session.execute(query)
                
        else:
            subscription_exeists = await session.execute(query)

        return subscription_exeists.scalar()


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
            
    async def unsubscribe_from_training(self, training_id: int) -> SubscriptionDTO:
        async with async_session_factory() as session:
            subscription_exists = await ORMBase.subscription_exists(session=session, user_id=self.user.id, training_id=training_id)
            
            if not subscription_exists:
                raise ValueError(f"Training with id={training_id} was not found in your subscriptions")
            
            subscription_dto = SubscriptionDTO(
                user_id = self.user.id,
                training_id=training_id
            )
            
            query = delete(
                Subscription
            ).where(
                and_(
                    Subscription.training_id == subscription_dto.training_id,
                    Subscription.student_id == subscription_dto.user_id
                )
            )

            await session.execute(query)
            available_training_insert_stmt = pg_insert(
                AvailableTraining
            ).values(
                user_id = self.user.id,
                training_id = training_id
            ).on_conflict_do_nothing(
                index_elements=["user_id", "training_id"]
            )

            await session.execute(available_training_insert_stmt)
            await session.commit()

            return subscription_dto


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

    async def get_my_interests(self, session: AsyncSession | None = None) -> List[Discipline]:
        query = select(
                User
            ).options(
                selectinload(User.interests)
            ).where(
                User.id == self.user.id
            )
        if session is None:
            async with async_session_factory() as session:
                result = await session.execute(query)
                user = result.scalar_one_or_none()
                return user.interests if user else []
            
        else:
            result = await session.execute(query)
            user = result.scalar_one_or_none()
            return user.interests if user else []

    def get_user(self) -> UserDTO:
        return self.user
        

# service for a coach
class CoachService():
    def __init__(self, user: UserDTO):
        self.user = user

    @staticmethod
    async def calculate_target_users(session: AsyncSession, training: TrainingDTO) -> Dict[str, int]:
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

    async def get_trainings(self, training_data: TrainingSearchDTO) -> List[TrainingDTO]:
        async with async_session_factory() as session:
            training_data_dict = training_data.model_dump(exclude_none=True)

            time_start_search = training_data_dict.get("time_start_search")
            time_end_search = training_data_dict.get("time_end_search")

            date_start_search = training_data_dict.get("date_start_search")
            date_end_search = training_data_dict.get("date_end_search")

            no_datetime_filters = []

            filter_map = {
                'title': Training.title,
                'description': Training.description,
                'type': Training.type,
                'discipline': Training.discipline,
                "individual_for_id": Training.individual_for_id,
                "target_auditory": Training.target_auditory,
                "target_gender": Training.target_gender
            }

            for key, value in training_data_dict.items():
                if not isinstance(value, date) and not isinstance(value, time):
                    no_datetime_filters.append(filter_map.get(key) == value)

            query = select(
                Training
            ).where(
                and_(
                    and_(
                        *no_datetime_filters
                    ), 
                    and_(
                        cast(Training.time_start, Time).between(time_start_search, time_end_search),
                        cast(Training.time_end, Time).between(time_start_search, time_end_search),
                        cast(Training.time_start, Date).between(date_start_search, date_end_search)
                    ),
                    Training.coach_id == self.user.id
                )
            )

            result = await session.execute(query)

            return [TrainingDTO.model_validate(training, from_attributes=True) for training in result.scalars().all()]


    async def create_training(self, training_data: TrainingAddDTO) -> TrainingAddDTO:
        async with async_session_factory() as session:

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

            
    async def update_training(self, training_id: int, **kwargs: Dict[str, Any]) -> TrainingDTO:
            async with async_session_factory() as session:
                try:
                    if not kwargs:
                        raise ValueError("No fields to update")
                    
                    training = await session.get(Training, training_id)
                    if not training:
                        raise ValueError("Training not found")

                    if training.coach_id != self.user.id:
                        raise InvalidPermissionsError("You can't modify this training because you are not a coach of this training")
                    
                    filter_params = {
                        "type": training.type,
                        "target_auditory": training.target_auditory,
                        "target_gender": training.target_gender
                    }

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

                    training_dto = TrainingDTO.model_validate(training, from_attributes=True)

                    #if the training type or target auditory, or target gender has changed, we need to recalculate the target users
                    if not (training_dto.type == filter_params["type"] and training_dto.target_auditory == filter_params["target_auditory"] and training_dto.target_gender == filter_params["target_gender"]):
                        data_target_users = []

                        # delete old target users for this training
                        await session.execute(
                            delete(
                                AvailableTraining
                                ).where(
                                    AvailableTraining.training_id == training_dto.id
                                )
                        )

                        # add new target users for this training
                        data_target_users = await self.calculate_target_users(session, training_dto)

                        if data_target_users:
                            stmt = pg_insert(AvailableTraining).values(data_target_users).on_conflict_do_nothing(index_elements=['user_id', 'training_id'])
                            await session.execute(stmt)

                    await session.commit()
                    return training_dto

                except Exception as ex:
                    await session.rollback()
                    raise ex
                
    async def get_students_of_training(self, training_id: int) -> List[UserDTO]:
        async with async_session_factory() as session:
            try:
                training_exists = await ORMBase.training_exists(session=session, id=training_id)
                if not training_exists:
                    raise ValueError("Training not found")
                query = select(
                    Training
                ).options(
                    selectinload(Training.users_on_training)
                ).where(
                    Training.id == training_id
                )

                result = await session.execute(query)

                return [UserDTO.model_validate(user, from_attributes=True) for user in result.scalar_one_or_none().users_on_training]
            except Exception as ex:
                await session.rollback()
                raise ex

                
    async def delete_training(self, training_id: int) -> None:
        async with async_session_factory() as session:
            try:
                training = await ORMBase.get_training_by_id(training_id)
                if not training:
                    raise ValueError("Training not found")
                if training.coach_id != self.user.id:
                    raise InvalidPermissionsError("You do not have permission to delete this training.")

                await session.execute(
                    delete(Training).where(Training.id == training_id)
                )
                await session.commit()
            except Exception as ex:
                await session.rollback()
                raise ex
            

    def get_user(self) -> UserDTO:
        return self.user

class RegistrationService():
    def __init__(self, new_user_dto: UserRegisterDTO):
        self.new_user_dto = new_user_dto

    def calculate_age(self) -> int:
        age = datetime.today().year - self.new_user_dto.birth_date.year

        if (datetime.today().month, datetime.today().day) < (self.new_user_dto.birth_date.month, self.new_user_dto.birth_date.day):
            age -= 1
        
        return age    

    async def add_new_user(self) -> UserAddDTO | None:
        async with async_session_factory() as session:
            all_emails_query = select(
                User.email
            ).distinct()

            all_emails = await session.execute(all_emails_query)
            all_emails = all_emails.scalars().all()

            if self.new_user_dto.email in all_emails:
                raise RegistrationError("The email you have entered is already used", 409)
            
            hashed_password = ph.hash(self.new_user_dto.password)

            age = self.calculate_age()

            user_add_dto = UserAddDTO(
                name=self.new_user_dto.name,
                email=self.new_user_dto.email,
                password=hashed_password,
                role=self.new_user_dto.role,
                age=age,
                gender=self.new_user_dto.gender
            )

            user = User.from_dto(user_add_dto)
            session.add(user)

            await session.flush()

            interests = []

            for i in self.new_user_dto.interests:
                interest = Interest(
                    discipline=i,
                    user_id=user.id
                )
                interests.append(interest)

            session.add_all(interests)

            await session.commit()

            return user_add_dto