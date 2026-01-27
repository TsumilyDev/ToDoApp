"""Provides a fast, no-dependancy, local cache to use for any purpose by just creating a
instance of the Memory class."""

from time import time


class BackendMemoryError(Exception):
    """This is the base class for all backend memory errors."""

    pass


class ObjectNotFoundError(BackendMemoryError):
    """Referenced object does not exist in backend memory."""

    pass


class ObjectAlreadyExistsError(BackendMemoryError):
    """Object already exists in backend memory"""

    pass


class DataError(BackendMemoryError):
    """Can not store or retrieve specified data"""

    pass


class DataExpiredError(BackendMemoryError):
    """Data is unreachable because it expired."""

    pass


# UPDATE : Consider a DataNotFound error. Consider creating two secondary base
# classes for objects and data. Clearly define the difference between them,
# both to yourself and in documentation.


class Payload:
    """
    The wrapper for all data inside memory.

    Payload data, expiration time, and note can be directly accesed and
    modified reliably. Container and identifier information are much more
    sensitive, they shouldn't be modified, although they can be read.
    """

    def __init__(
        self,
        container: str,
        identifier: str,
        data,
        ttl: int = 30,
        /,
        *,
        note: str = "",
    ):
        self.data = data
        self.expiration_time = int(time()) + ttl
        self.note = note

        self._container = container
        self._identifier = identifier

    def __repr__(self) -> str:
        return f"""Container: '{self._container}' Identifier:'
        {self._identifier}'\n Expires at: '{self.expiration_time}'\n Data:
        '{self.data}'\n Notes: '{self.note}'"""

    def __str__(self) -> str:
        return f"Data: '{self.data}'."

    def get_location(self) -> dict:
        """Returns the exact location of the payload by returning the
        container and identifier."""
        return {
            "container": "self._container",
            "identifier": "self._identifier",
        }

    def description(self) -> dict:
        """Returns a dictionary with the data, note, and location."""
        return {
            "data": self.data,
            "note": self.note,
            "container": self._container,
            "identifier": self._identifier,
        }

    def is_expired(self):
        return self.expiration_time <= int(time())


class Memory:
    """
    Non-presistent local memory with time-based expiry and seperation of
    concerns through categories.

    The only units used are seconds and the internal system uses second-level
    percision too.

    Memory only contains alive data, once somethings expiry time has passed it
    becomes unreachable through function-based access.
    It is heavily encourged to only use CRUD operations for data in memory
    using the given functions, otherwise unexpected behaviour may occur.
    """

    def __init__(self, name):
        self.memory = {
            "process_information": {},
        }

        self.container_guides = {"process_information": """
            The backend and frontend may exchange several times to complete a
            singular process for the user, the information between each
            exchange will be saved here."""}

        self.memoryName = name
        self.documentation = ""
        self.list = ["hello", "bruh"]

    # -- CRUD and general-interactions
    def add_data(
        self,
        container: str,
        identity: str,
        ttl: int,
        data,
        /,
        *,
        note: str = "",
        overwrite: bool = False,
    ) -> None:
        """Creates a data entry and location inside the given container."""
        # Safety checks for container and identifier
        if container not in self.memory:
            raise ObjectNotFoundError(
                f"Container '{container}' does not exist."
            )
        self.clean_container(container)
        if identity in self.memory[container] and not overwrite:
            raise ObjectAlreadyExistsError(
                f"Can not overwrite. Identifier '{identity}' is already used."
            )

        # Container specific procedures
        # None currently, add the option to add them.

        # Payload construction and actually storing the value in memory now
        self.memory[container][identity] = Payload(
            container, identity, data, ttl, note=note
        )
        return

    def retrieve_data(self, container: str, identifier: str):
        """
        Returns data that was stored under the given identifier in the given
        container.
        """
        if container not in self.memory:
            raise ObjectNotFoundError(
                f"Container '{container}' does not exist."
            )
        payload = self.memory.get(container).get(identifier)
        if not payload:
            raise ObjectNotFoundError(f"""Identifer '{identifier}'
                does not exist in container '{container}'""")
        if payload.is_expired():
            del self.memory[container][identifier]
            raise DataExpiredError(
                f"""Data at location: container, '{container}'; identifier,
                '{identifier}'."""
            )
        return payload.data

    def retrieve_identifiers_from_data(
        self, container: str, data: str
    ) -> list:
        """Returns a list of all the identifiers of the given data."""
        if container not in self.memory:
            raise ObjectNotFoundError(
                f"Container '{container}' does not exist."
            )
        self.clean_container(container)

        identifiers = []

        for identifier, payload in self.memory[container].items():
            if payload.data == data:
                identifiers.append(identifier)
        if not identifiers:
            raise ObjectNotFoundError(
                f"""Data, '{data}', does not exist inside container
                '{container}'."""
            )
        return identifiers

    def does_data_exist(self, container: str, data: str) -> bool:
        """
        Returns True if data exists in the given container,
        else returns False.
        """
        if container not in self.memory:
            raise ObjectNotFoundError(
                f"Container '{container}' does not exist."
            )
        self.clean_container(container)

        for payload in self.memory[container].values():
            if payload.data == data:
                return True
        return False

    def clean_memory(self) -> list:
        """Removes all expired data inside memory."""
        expired = []
        for container_name in list(self.memory.keys()):
            for identifier, payload in list(
                self.memory[container_name].items()
            ):
                if payload.is_expired():
                    expired.append(payload.description())
                    del self.memory[container_name][identifier]

        return expired

    def clean_container(self, container: str) -> list:
        """Removes all expired data inside the given container."""
        expired = []
        if container not in self.memory:
            raise ObjectNotFoundError(
                f"There is no '{container}' container."
            )
        for identifier, payload in list(self.memory[container].items()):
            if payload.is_expired():
                expired.append(payload.description())
                del self.memory[container][identifier]
        return expired

    def delete_data(self, container: str, identifier: str) -> None:
        """Instantly deletes the identifier and the data."""
        if not self.memory.get(container, {}).get(identifier):
            raise ObjectNotFoundError(
                f"""Identifier '{identifier}' does not exist in container
                '{container}'."""
            )
        del self.memory[container][identifier]
        return

    # -- Listing
    def list_all_data_in_memory(self) -> list:
        """
        Returns a list of all data inside memory in arbitary order.\n
        This does not return any other payload or memory information.
        """
        self.clean_memory()
        data = []
        for container_data in self.memory.values():
            for payload in container_data.values():
                data.append(payload.data)

        return data

    def list_all_data_in_container(self, container: str) -> list:
        """
        Returns a list of all data inside the specified container in
        arbitary order.\n
        This does not return any other payload or memory information.
        """
        if container not in self.memory:
            raise ObjectNotFoundError(
                "Container does not exist in memory."
            )
        self.clean_container(container)

        data = []
        for identifier in self.memory[container]:
            data.append(self.memory[container][identifier].data)

        return data

    # -- Guide
    def clean_guides(self) -> list:
        """
        Removes all guides that do not have a matching container then
        returns list of removed guides.
        """
        guides_cleaned = []

        for guide_name, guide in list(self.container_guides.items()):
            if guide_name not in self.memory.keys():
                guides_cleaned.append((guide_name, guide))
                del self.container_guides[guide_name]

        return guides_cleaned

    # -- JSON
    # This function requires much more nuance due to Payload now being an
    # object. Additionally, I want to add structure enforcing and more
    # flexibility with importing.

    # I'll have to create a complex parser, which I'll do later. UPDATE.

    # def export_to_json(self) -> str:
    #     """
    #     Returns a JSON-object of all memory.\n\n Includes containers,
    #     identifiers, values, TTL's, and notes.
    #     """
    #     return json.dumps(self.memory)

    # def import_from_json(self, JSON: str) -> None:
    #     """
    #     Adds JSON-object inside memory.

    #     The JSON-object has to have the same paradigm as all other memory
    #     uses.

    #     The paradigm is three layers of dictionaries; first is the entire
    #     memory, the second is containers, and the third is the payload. There
    #     is no other structure to memory.
    #     """

    #     # UPDATE : THIS WILL CURRENTLY COMPLETELY REPLACE THE INSIDE OF ANY
    #     # OVERLAPPING CONTAINERS WTIH THE IMPORTED JSON, MAKE IT ADD, NOT REPLACE

    #     self.memory.update(json.loads(JSON))

    # extension methods, these were not part of the original class but were added for
    # convenience sake.

    def __setitem__(
        self, container_name: str, container_guide: str = ""
    ) -> None:
        """Creates a new container, which is just a plain dictionary inside memory.

        Containers are used as seperators of concerns regarding values.
        A guide will be created automatically and be empty by default.
        """
        if container_name in self.memory:
            raise ObjectAlreadyExistsError(
                f"Can not create container, {container_name}, because it already exists"
            )
        self.memory[container_name] = {}
        self.container_guides[container_name] = container_guide
        return None

    def add_container(
        self, container_name: str, container_guide: str = ""
    ) -> None:
        self[container_name] = container_guide
        return None

    def remove_container(self, container: str) -> None:
        """
        Removes a container, seperator of concern, from memory and the guide for that
        container.
        """
        if container not in self.memory:
            raise ObjectNotFoundError(
                f"Container {container} does not exist."
            )
        del self.memory[container]
        del self.container_guides[container]
        return None
