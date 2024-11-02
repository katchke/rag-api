from abc import abstractmethod


class IConnectionStringFactory:
    @abstractmethod
    def create(self) -> str:
        pass


class ConnectionStringFactory:
    def __init__(
        self,
        host: str,
        port: str,
        db: str,
        username: str,
        password: str
    ) -> None:
        self._host = host
        self._port = port
        self._db = db
        self._username = username
        self._password = password

    def create(self) -> str:
        connection_string = ("postgresql://"
                             "%(POSTGRES_USER)s:%(POSTGRES_PASSWORD)s"
                             "@%(POSTGRES_HOST)s:%(POSTGRES_PORT)s/"
                             "%(POSTGRES_DB)s") % {
            "POSTGRES_HOST": self._host,
            "POSTGRES_PORT": self._port,
            "POSTGRES_DB": self._db,
            "POSTGRES_USER": self._username,
            "POSTGRES_PASSWORD": self._password
        }
        return connection_string
