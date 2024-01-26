import json
import requests
import asyncio

from pytezos.contract.interface import ContractInterface
from pytezos.michelson.types import MichelsonType
from pytezos.crypto.key import blake2b_32
import pytezos


def tezos_hex(s):
    return f"0x{bytes(s, 'utf-8').hex()}"


# TODO: could be part of the Python library
def deploy_permit(admin):
    fa2_contract = ContractInterface.from_file("permit-contract.tz")
    fa2_initial_storage = fa2_contract.storage.dummy()
    fa2_initial_storage["metadata"] = {
        "": tezos_hex("tezos-storage:m"),
        "m": json.dumps({
            "name": "Weapons",
            "interfaces": ["TZIP-12"]
        }).encode("utf-8")
    }

    fa2_initial_storage["token_metadata"] = {
        0: {
            "token_id": 0,
            "token_info": {
                "name": tezos_hex("Rusty sword"),
                "description": tezos_hex("a rusty sword"),
                "interfaces": tezos_hex(json.dumps(["TZIP-12"])),
                "symbol": tezos_hex("TCK1"),
                "decimals": tezos_hex("0"),
                "thumbnailUri": tezos_hex("ipfs://QmdPmCiyNRUJiWAzRcd2UMUAnpFDhZVxujvPHg1xCx1GZb"),
                "displayUri": tezos_hex("ipfs://QmdPmCiyNRUJiWAzRcd2UMUAnpFDhZVxujvPHg1xCx1GZb"),
                "artifactUri": tezos_hex("ipfs://QmdPmCiyNRUJiWAzRcd2UMUAnpFDhZVxujvPHg1xCx1GZb")
            }
        },
        1: {
            "token_id": 1,
            "token_info": {
                "name": tezos_hex("Pirate sword"),
                "description": tezos_hex("a pirate sword"),
                "interfaces": tezos_hex(json.dumps(["TZIP-12"])),
                "symbol": tezos_hex("TCK1"),
                "decimals": tezos_hex("0"),
                "thumbnailUri": tezos_hex("ipfs://QmPdwAqgBhM65fzzYT4FQmCELAej8Mei6QQZiBZ93M4Acq"),
                "displayUri": tezos_hex("ipfs://QmPdwAqgBhM65fzzYT4FQmCELAej8Mei6QQZiBZ93M4Acq"),
                "artifactUri": tezos_hex("ipfs://QmPdwAqgBhM65fzzYT4FQmCELAej8Mei6QQZiBZ93M4Acq")
            }
        },
        2: {
            "token_id": 2,
            "token_info": {
                "name": tezos_hex("Small knife"),
                "description": tezos_hex("a small knife"),
                "interfaces": tezos_hex(json.dumps(["TZIP-12"])),
                "symbol": tezos_hex("TCK1"),
                "decimals": tezos_hex("0"),
                "thumbnailUri": tezos_hex("ipfs://QmV9RAPyo4xnPQG3qJLjHMmxJBjLWyyPKLiNdkzcmNB31c"),
                "displayUri": tezos_hex("ipfs://QmV9RAPyo4xnPQG3qJLjHMmxJBjLWyyPKLiNdkzcmNB31c"),
                "artifactUri": tezos_hex("ipfs://QmV9RAPyo4xnPQG3qJLjHMmxJBjLWyyPKLiNdkzcmNB31c")
            }
        },
        3: {
            "token_id": 3,
            "token_info": {
                "name": tezos_hex("Frying pan"),
                "description": tezos_hex("a frying pan"),
                "interfaces": tezos_hex(json.dumps(["TZIP-12"])),
                "symbol": tezos_hex("TCK1"),
                "decimals": tezos_hex("0"),
                "thumbnailUri": tezos_hex("ipfs://QmWFiyrm9byfefPFAhsUdAQg6Q42CMj1ux8Jwo4fECRjNw"),
                "displayUri": tezos_hex("ipfs://QmWFiyrm9byfefPFAhsUdAQg6Q42CMj1ux8Jwo4fECRjNw"),
                "artifactUri": tezos_hex("ipfs://QmWFiyrm9byfefPFAhsUdAQg6Q42CMj1ux8Jwo4fECRjNw")
            }
        },
        4: {
            "token_id": 4,
            "token_info": {
                "name": tezos_hex("Slingshot"),
                "description": tezos_hex("a slingshot"),
                "interfaces": tezos_hex(json.dumps(["TZIP-12"])),
                "symbol": tezos_hex("TCK1"),
                "decimals": tezos_hex("0"),
                "thumbnailUri": tezos_hex("ipfs://QmQZuirmonLR7uPFCfidX6vELLP6CLmD657qUdQUij8RhG"),
                "displayUri": tezos_hex("ipfs://QmQZuirmonLR7uPFCfidX6vELLP6CLmD657qUdQUij8RhG"),
                "artifactUri": tezos_hex("ipfs://QmQZuirmonLR7uPFCfidX6vELLP6CLmD657qUdQUij8RhG")
            }
        },
        5: {
            "token_id": 5,
            "token_info": {
                "name": tezos_hex("Claymore"),
                "description": tezos_hex("a claymore"),
                "interfaces": tezos_hex(json.dumps(["TZIP-12"])),
                "symbol": tezos_hex("TCK1"),
                "decimals": tezos_hex("0"),
                "thumbnailUri": tezos_hex("ipfs://QmQYwBm31CJzAyGfYajLMULQHZUUYSrfAzJZgjZ7XurZZe"),
                "displayUri": tezos_hex("ipfs://QmQYwBm31CJzAyGfYajLMULQHZUUYSrfAzJZgjZ7XurZZe"),
                "artifactUri": tezos_hex("ipfs://QmQYwBm31CJzAyGfYajLMULQHZUUYSrfAzJZgjZ7XurZZe")
            }
        }
    }

    fa2_initial_storage["extension"]["extension"] = {
        i: 0 for i in range(len(fa2_initial_storage["token_metadata"]))
    }

    fa2_initial_storage["extension"]["admin"] = admin.key.public_key_hash()
    fa2_initial_storage["extension"]["max_expiry"] = 3600
    fa2_initial_storage["extension"]["default_expiry"] = 3600
    orig = admin.origination(fa2_contract.script(
        initial_storage=fa2_initial_storage)
    ).autofill().sign().inject(min_confirmations=1)
    nft_contract_address = orig["contents"][0]["metadata"]["operation_result"]["originated_contracts"][0]
    nft_contract = admin.contract(nft_contract_address)
    return nft_contract


def deploy_staking_contract(admin, nft_contract):
    staking_contract = ContractInterface.from_file("staking-contract.tz")
    staking_storage = staking_contract.storage.dummy()
    staking_storage["nft_address"] = nft_contract.address
    orig = admin.origination(
        staking_contract.script(initial_storage=staking_storage)
    ).autofill().sign().inject(min_confirmations=1)
    staking_address = orig["contents"][0]["metadata"]["operation_result"]["originated_contracts"][0]
    return admin.contract(staking_address)


class Demo:
    def __init__(self, nft_contract, staking_contract,
                 api_url="http://127.0.0.1:8000/operation"):
        self.nft_contract = nft_contract
        self.staking_contract = staking_contract
        self.api_url = api_url

    def post_op(self, op, sender):
        print(f"calling {self.api_url} with sender={sender}")
        req = requests.post(
            self.api_url,
            json={
                "sender": sender,
                "operations": op.contents
            }
        )
        return req

    # This functions is meant to be called from a notebook.
    def make_requests(self, func, args):
        async def main():
            loop = asyncio.get_event_loop()
            futures = [
                loop.run_in_executor(
                    None,
                    func,
                    *arg
                )
                for arg in args
            ]
            for response in await asyncio.gather(*futures):
                print(response)

        loop = asyncio.get_event_loop()
        return loop.create_task(main())

    def generate_mint(self, owner):
        return self.nft_contract.mint_token([{
            "owner": owner,
            "token_id": 0,
            "amount_": 100
        }]).as_transaction()

    def mint_requests(self, owners):
        mint_ops = [(self.generate_mint(owner), owner) for owner in owners]
        return self.make_requests(self.post_op, mint_ops)

    def permit_requests(self, keys):
        permits = [(self.generate_permit(key), key.public_key_hash())
                   for key in keys]
        return self.make_requests(self.post_op, permits)

    def stake_request(self, sender, qty=10):
        staking_op = self.staking_contract.stake(qty, sender).as_transaction()
        req = requests.post(
            self.api_url,
            json={
                "sender": sender,
                "operations": staking_op.contents
            }
        )
        return req

    # TODO: what happens if transfer is < 10?
    def generate_permit(self, key, qty=10):
        transfer = self.nft_contract.transfer([{
            "from_": key.public_key_hash(),
            "txs": [{
                "to_": self.staking_contract.address,
                "token_id": 0,
                "amount": 10
            }]
        }])

        matcher = MichelsonType.match(
            self.nft_contract.entrypoints["transfer"].as_micheline_expr()[
                "args"][0]
        )
        micheline_encoded = matcher.from_micheline_value(
            transfer.parameters["value"][0]["args"]
        )
        transfer_hash = blake2b_32(micheline_encoded.pack()).hexdigest()
        permit_hashed_type = {
            'prim': 'pair',
            'args': [
                {
                    'prim': 'pair',
                    'args': [
                        {'prim': 'chain_id'},
                        {'prim': 'address'}
                    ]
                },
                {
                    'prim': 'pair',
                    'args': [
                        {'prim': 'int'},
                        {'prim': 'bytes'}
                    ]
                }

            ]
        }
        permit_hashed_args = [
            [
                {"string": self.nft_contract.shell.block()["chain_id"]},
                {"string": self.nft_contract.address}
            ],
            [
                {"int": self.nft_contract.storage()["extension"]["counter"]},
                {"bytes": transfer_hash}
            ]
        ]
        matcher2 = MichelsonType.match(permit_hashed_type)
        permit_hash = matcher2.from_micheline_value(permit_hashed_args).pack()
        permit_signature = key.sign(permit_hash)
        permit_op = self.nft_contract.permit([(
            key.public_key(),
            permit_signature,
            transfer_hash
        )]).as_transaction()
        return permit_op
