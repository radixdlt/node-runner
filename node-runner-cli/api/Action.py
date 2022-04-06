from core_client.model.big_integer import BigInteger
from core_client.model.data import Data
from core_client.model.entity_identifier import EntityIdentifier
from core_client.model.operation import Operation
from core_client.model.operation_group import OperationGroup
from core_client.model.prepared_validator_fee import PreparedValidatorFee
from core_client.model.prepared_validator_owner import PreparedValidatorOwner
from core_client.model.prepared_validator_registered import PreparedValidatorRegistered
from core_client.model.resource_amount import ResourceAmount
from core_client.model.stake_unit_resource_identifier import StakeUnitResourceIdentifier
from core_client.model.sub_entity import SubEntity
from core_client.model.sub_entity_metadata import SubEntityMetadata
from core_client.model.token_resource_identifier import TokenResourceIdentifier
from core_client.model.validator_allow_delegation import ValidatorAllowDelegation
from core_client.model.validator_metadata import ValidatorMetadata
from core_client.model.validator_system_metadata import ValidatorSystemMetadata

class Action:
    @staticmethod
    def set_validator_metadata(name: str, url: str):
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
    def set_validator_registeration(registered):
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

    @staticmethod
    def set_validator_fee(fee):
        return lambda node_identifiers: [
            OperationGroup([
                Operation(
                    type="Data",
                    entity_identifier=node_identifiers.validator_entity_identifier,
                    data=Data(
                        action='CREATE',
                        data_object=PreparedValidatorFee(
                            type="PreparedValidatorFee",
                            fee=fee
                        )
                    )
                )
            ]),
        ]

    @staticmethod
    def set_validator_allow_delegation(allow_delegation):
        return lambda node_identifiers: [
            OperationGroup([
                Operation(
                    type="Data",
                    entity_identifier=node_identifiers.validator_entity_identifier,
                    data=Data(
                        action='CREATE',
                        data_object=ValidatorAllowDelegation(
                            type="ValidatorAllowDelegation",
                            allow_delegation=allow_delegation
                        )
                    )
                )
            ]),
        ]

    @staticmethod
    def set_validator_owner(owner):
        return lambda node_identifiers: [
            OperationGroup([
                Operation(
                    type="Data",
                    entity_identifier=node_identifiers.validator_entity_identifier,
                    data=Data(
                        action='CREATE',
                        data_object=PreparedValidatorOwner(
                            type="PreparedValidatorOwner",
                            owner=EntityIdentifier(address=owner)
                        )
                    )
                )
            ]),
        ]
    
    @staticmethod
    def vote():        
        return lambda node_identifiers: [
            OperationGroup([
                Operation(
                    type="Data",
                    entity_identifier=node_identifiers.validator_entity_identifier,
                    data=Data(
                        action='CREATE',
                        data_object=ValidatorSystemMetadata(
                            type="ValidatorSystemMetadata",
                            data=""
                        )
                    )
                )
            ]),
        ]
    
    @staticmethod
    def cancel_vote():
        return lambda node_identifiers: [
            OperationGroup([
                Operation(
                    type="Data",
                    entity_identifier=node_identifiers.validator_entity_identifier,
                    data=Data(
                        action='CREATE',
                        data_object=ValidatorSystemMetadata(
                            type="ValidatorSystemMetadata",
                            data="0" * 32
                        )
                    )
                )
            ]),
        ]

    @staticmethod
    def transfer_tokens(rri, amount, receiver):
        return lambda node_identifiers: [
            OperationGroup([
                Operation(
                    type="Resource",
                    entity_identifier=node_identifiers.account_entity_identifier,
                    amount=ResourceAmount(
                        BigInteger('-' + amount),
                        TokenResourceIdentifier(type="Token", rri=rri)
                    )
                ),
                Operation(
                    type="Resource",
                    entity_identifier=EntityIdentifier(address=receiver),
                    amount=ResourceAmount(
                        BigInteger(amount),
                        TokenResourceIdentifier(type="Token", rri=rri)
                    )
                )
            ])
        ]

    @staticmethod
    def stake_tokens(rri, amount, validator):
        return lambda node_identifiers: [
            OperationGroup([
                Operation(
                    type="Resource",
                    entity_identifier=node_identifiers.account_entity_identifier,
                    amount=ResourceAmount(
                        BigInteger('-' + amount),
                        TokenResourceIdentifier(type="Token", rri=rri)
                    )
                ),
                Operation(
                    type="Resource",
                    entity_identifier=EntityIdentifier(
                        address=node_identifiers.account_entity_identifier.address,
                        sub_entity=SubEntity(
                            address='prepared_stake',
                            metadata=SubEntityMetadata(
                                validator_address=validator
                            )
                        )
                    ),
                    amount=ResourceAmount(
                        BigInteger(amount),
                        TokenResourceIdentifier(type="Token", rri=rri)
                    )
                )
            ])
        ]

    @staticmethod
    def unstake_stake_units(amount, validator):
        return lambda node_identifiers: [
            OperationGroup([
                Operation(
                    type="Resource",
                    entity_identifier=node_identifiers.account_entity_identifier,
                    amount=ResourceAmount(
                        BigInteger('-' + amount),
                        StakeUnitResourceIdentifier(type="StakeUnit", validator_address=validator)
                    )
                ),
                Operation(
                    type="Resource",
                    entity_identifier=EntityIdentifier(
                        address=node_identifiers.account_entity_identifier.address,
                        sub_entity=SubEntity(
                            address='prepared_unstake'
                        )
                    ),
                    amount=ResourceAmount(
                        BigInteger(amount),
                        StakeUnitResourceIdentifier(type="StakeUnit", validator_address=validator)
                    )
                )
            ])
        ]
