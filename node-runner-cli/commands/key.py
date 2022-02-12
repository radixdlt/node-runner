from argparse import ArgumentParser

from commands.subcommand import get_decorator, argument
from key_interaction.KeyInteraction import KeyInteraction

# Setup key subcommand parser
keycli = ArgumentParser(
    description='Key interaction commands')
key_parser = keycli.add_subparsers(dest="keycommand")


def keycommand(args=[], parent=key_parser):
    return get_decorator(args, parent)


@keycommand([
    argument("-p", "--password", required=True,
             help="Password of the keystore",
             action="store"),
    argument("-f", "--filelocation", required=True,
             help="Location of keystore on the disk",
             action="store"),
])
def info(args):
    key = KeyInteraction(keystore_password=str.encode(args.password), keystore_path=args.filelocation)
    print(f"Validator Address {key.get_validator_address()}")
    print(f"Validator hex public key  {key.get_validator_hex_public_key()}")


@keycommand([
    argument("-p", "--password", required=True,
             help="Password of the keystore",
             action="store"),
    argument("-f", "--filelocation", required=True,
             help="Location of keystore on the disk",
             action="store"),
    argument("-ps", "--payloadtosign", required=True,
             help="payload to sign",
             action="store")
])
def sign_payload(args):
    key = KeyInteraction(keystore_password=str.encode(args.password), keystore_path=args.filelocation)
    print(f"Signed DER from payload {key.sign_payload(args.payloadtosign)}")
