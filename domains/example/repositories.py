from abc import ABCMeta, abstractmethod
from sqlalchemy.orm import Session

from domains.example.models import ExampleModel
from domains.errors import NotFoundException

class IExampleRepository(metaclass=ABCMeta):
    @abstractmethod
    def get_by_id(self,
             session: Session,
             id: int,
             ) -> ExampleModel:
        pass

class ExampleRepository(IExampleRepository):
    def __init__(self) -> None:
        pass

    def get_by_id(self, session: Session, id: int) -> ExampleModel:
        example = (session.query(ExampleModel)
              .filter_by(id=id)
              .first())
        if not example:
            raise NotFoundException("id not found")
        return example
