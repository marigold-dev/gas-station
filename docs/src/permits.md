# An introduction to off-chain permits

In the [Tutorial](./tutorial.md) chapter, we show how to transfer a NFT to a smart contract
through the Gas Station. As the corresponding operation is ultimately going to get posted by the Gas
Station account, there is an issue: how is NFT contract going to allow this transfer on behalf of
the user? While FA2 contracts, which are used to implement NFTs, support the concept of *operators*
accounts acting on the behalf of the user, only the original owner of the NFT can allow a new
operator to do so. The simplest way would be to modify the NFT contract to

* make the Gas Station account a super-user of the contract, and
* let this account [register third-party contracts as
  operators](https://tezostaquito.io/docs/fa2_parameters/#the-update_operators-entrypoint), which
  would allow the transfer to happen

This, of course, creates a security (and, potentially, legal) issue: if the key of Marigold Gas
Station account gets stolen, then several FA 2 contracts could be compromised as well. On the other
hand, users whose operations get sponsored are not supposed to have any tez in their wallet, and
thus cannot post the `update_operator` call on-chain themselves.

What is the solution, then?

## Off-chain permits

To solve this problem in a secure way, the notion of *off-chain permits* was introduced by [TZIP
17](https://tzip.tezosagora.org/proposal/tzip-17/). It extends the FA 2 standard with a few new
entrypoints. The most interesting one, itself called `permit`, can be called by anyone, and
expects a list of authorizations for transfers signed by the owners. Those transfers are signed
off-chain: this means that the application has to ask the users for their signature through the
usual ways (e.g. a Beacon-compatible wallet), but this signature has then to be stored and/or
sent to this entrypoint by another account.

Most of the time, however, these permits can be sent in the same transaction as the call to the
other contract, as we did in the previous chapter. When a permit is registered by the contract, it
acts as a one-time authorization for a transfer to a specific address, which can either be a
contract or a implicit account. The `transfer` entrypoint has the same interface as an ordinary FA 2
contract and of course supports the same usage as before, including regular operators. This means
that regular users, who don't need their transactions to be relayed by the gas station, can always
use their assets in a normal, permissionless way.

Let's define permits: they are signed bytes, formed from 4 parameters:

* the chain identifier, such that a permit signed for a given chain (such as Ghostnet) cannot be
  used on a different chain;
* the address of the permit FA2 contract, such that a permit signed for a given NFT collection
  cannot be used on another one;
* a counter (nonce) defined inside the contract, such as a permit can only be used once;
* and, finally, a hash of the allowed operation, which is going to be checked when the
  transfer takes place.

If you recall [the previous chapter](./tutorial.md), this byte string was computed by the library
with the following call:

```ts
const permitData = await permitContract.generatePermit({
  from_: userAddress,
  txs: [{
    to_: RECIPIENT,
    token_id,
    amount: 1
  }]
});
```

Indeed, it can be a little bit complicated to form by hand, and the slightest error makes the permit
fail silently.

Once it is signed by the user, the permit can be registered in the contract by calling the `permit`
entrypoint, which expects a list of parameters of the form `(public_key, signature, transfer_hash)`
where `public_key` is the user's public key, which is necessary to check the `signature`. This
`signature` is computed from the whole byte string, not just the `transfer_hash`.

i If you choose to compute permits by hand, be mindful that they are actually computed by forming
the following couple: `((chain_identifier, contract_address), (contract_counter, transfer_hash))`.
Check the documentation of the contract library that you are using to be sure.

## How to deploy a permit contract

The most up-to-date implementation of TZIP 17-style permits is [the permit-cameligo Ligo
package](https://github.com/aguillon/permit-cameligo/), which is currently maintained outside of
Ligo Package Registry website. To use it, it is recommended to clone the following repository and
use the Ligo compiler to install the dependencies:

```bash
$ git clone https://github.com/aguillon/permit-cameligo
$ cd permit-cameligo/
$ make install
$ make compile
```

Note that the Makefile assumes that you run the dockerized version of Ligo. To use another one, for
instance a local one, you can prefix the `make` commands with `ligo_compiler=ligo `. For instance:

```bash
$ ligo_compiler=ligo make install
$ ligo_compiler=ligo make compile
```

This installs the dependencies in `.ligo/`, and compiles the code to produce two files in `compiled/`.
The first of those files is a JSONized version of the second, which is ready to be deployed by the
scripts in `deploy/`. In addition to the compiled code, this script requires two files:
`deploy/metadata.json` that contains the contract's metadata, and `deploy/.env` which contains the
secret key and the RPC node.

Let's create a minimal `deploy/metadata.json` file:

```json
{
  "name":"Example",
  "interfaces":[
    "TZIP-12"
  ]
}
```

Change this file according to your needs. If you just want to test the deployment script, you can
also use the pre-generated `deploy/metadata.json.dist` file and rename it to `deploy/metadata.json`.
In the same spirit, copy `deploy/.env.dist` to `deploy/.env` and edit the file to put your secret
key:

```bash
# Required: Your private key
PK=edsk...
# Required: see https://tezostaquito.io/docs/rpc_nodes/
RPC_URL=https://ghostnet.tezos.marigold.dev/
```

Finally, you should be able to

```
$ cd deploy/
$ npm i
$ npm run start
```

This workflow assumes that you're going to mint each token individually by calling the
`create_token` entrypoint. If you want to pre-mint some tokens, you need to edit the
`deploy/deploy.ts` script to start with a non-empty `token_metadata` map. The script should print
the address of the contract after origination.
