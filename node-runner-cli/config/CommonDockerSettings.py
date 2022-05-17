from setup import Base


class CommonDockerSettings:
    network_id: int = None
    network_name: str = None
    genesis_json_location: str = None

    def __init__(self, settings: dict):
        for key, value in settings.items():
            setattr(self, key, value)

        if self.network_id:
            self.set_network_name()

    def set_network_id(self, network_id: int):
        self.network_id = network_id
        self.set_network_name()

    def set_genesis_json_location(self, genesis_json_location: str):
        self.genesis_json_location = genesis_json_location

    def set_network_name(self):
        if self.network_id == 1:
            self.network_name = "mainnet"
        elif self.network_id == 2:
            self.network_name = "stokenet"
        else:
            raise ValueError("Network id is set incorrect")

    def ask_network_id(self):
        if not self.network_id:
            self.set_network_id(Base.get_network_id())
        self.set_genesis_json_location(Base.path_to_genesis_json(self.network_id))

    def __iter__(self):
        for attr, value in self.__dict__.items():
            if value:
                yield attr, value
