from core_client.model.data import Data
from core_client.model.operation import Operation
from core_client.model.operation_group import OperationGroup
from core_client.model.prepared_validator_registered import PreparedValidatorRegistered
from core_client.model.validator_metadata import ValidatorMetadata


class Core:
    @staticmethod
    def set_validator_metadata(name, url):
        return lambda node_identifiers: [
            OperationGroup([
                Operation(
                    type="Data",
                    entity_identifier=node_identifiers.validator_entity_identifier,
                    data=Data(
                        action='CREATE',
                        data_object=ValidatorMetadata(
                            type="ValidatorMetadata",
                            name=name,
                            url=url
                        )
                    )
                )
            ]),
        ]

    @staticmethod
    def set_validator_registered(registered):
        return lambda node_identifiers: [
            OperationGroup([
                Operation(
                    type="Data",
                    entity_identifier=node_identifiers.validator_entity_identifier,
                    data=Data(
                        action='CREATE',
                        data_object=PreparedValidatorRegistered(
                            type="PreparedValidatorRegistered",
                            registered=registered
                        )
                    )
                )
            ])
        ]
