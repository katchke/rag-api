import inject
from contextlib import contextmanager
from sqlalchemy.orm import sessionmaker

from domains.example.repositories import ExampleRepository
from domains.errors import BadRequestException

class ExampleService:
    
    @inject.params(
        session_maker=sessionmaker,
        example_repository=ExampleRepository
    )
    def __init__(
        self,
        session_maker: sessionmaker,
        example_repository: ExampleRepository,
    ) -> None:
        self.session_maker = session_maker
        self.example_repository = example_repository
        
    def get_example_by_id(self, id: int):
        with self.transactional_session() as session:
            example = self.example_repository.get_by_id(session, id)
            return example.to_dict() if example else None

    @contextmanager
    def transactional_session(self):
        session = self.session_maker()
        try:
            yield session
            session.commit()
        except Exception as ex:
            session.rollback()
            print(f"Transaction failed: {ex}")
            error_message = str(ex).split('DETAIL:')[0].strip()
            raise BadRequestException(error_message)
        finally:
            session.close()
