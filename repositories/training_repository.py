from sqlalchemy import select
from base_repository import BaseRepository
from sqlalchemy.ext.asyncio import AsyncSession

from models.models import Training
from schemas.schemas import TrainingAddDTO, TrainingDTO


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
