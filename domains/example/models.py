from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from typing import Type

Base: Type = declarative_base()


class ExampleModel(Base):
    __tablename__ = 'examples'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

    def __repr__(self) -> str:
        return (f"{self.__class__.__name__}("
                f"_id={self.id!r}, "
                f"_name={self.name!r})")
