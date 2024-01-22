# Developing a web application with the Gas Station

This chapter walks through a simple example of a dapp using the Gas Station. You can [try it online at this address](https://ghostnet.gas-station-nft-example.marigold.dev).

## Template

The first step is to retrieve the code template located [here](https://github.com/marigold-dev/gas-station-nft-example-template).
Once retrieved, you can run the following commands:
```bash
npm install
npm run check
```

ℹ️ Note: If `npm run check` returns some errors, it's ok. It's just to initialize some Svelte tools.


To test that everything works well, you can use:
```bash
npm run dev
```

The files of interest are located in `src/lib`. You will find Svelte components and a `tezos.ts` file that contains utility functions such as wallet connection, etc.

To distinguish between a simple call to the Gas Station and a more complex examples involving permits, we develop two distinct components, `src/lib/MintingComponent.svelte` and `src/lib/StakingComponent.svelte`.
Let's go ! 💪

## Minting an NFT

We'll start with minting an NFT by a user. The contract we'll use is available at this address on Ghostnet: [`KT1HUdxmgZUw21ED9gqELVvCty5d1ff41p7J`](https://ghostnet.tzkt.io/KT1HUdxmgZUw21ED9gqELVvCty5d1ff41p7J/operations).
This contract has an admin, which is the only account allowed to mint NFTs. This is the same
settings as you would have in a video game, where the game decides when to mint an NFT for a user.
In this case, the contract admin has been set to be the Gas Station account, because the `mint`
entrypoint is always going to be called by the Gas Station.

The goal here is for the user to initiate the mint action and retrieve their NFT without having to
pay gas fees. For this, we will use the [TypeScript SDK](./library.md).

First, we'll setup the GasStation SDK as follows:
```ts
const gasStationAPI = new GasStation()
```
ℹ️ `GasStation` class will target the Gas Station deployed on Ghostnet by default.

Next, we'll retrieve an instance of our contract, using [Taquito](https://tezostaquito.io/).

```ts
const contract = await Tezos.wallet.at(PUBLIC_PERMIT_CONTRACT);
```

ℹ️ The `Tezos` instance of Taquito is already initialized in the `tezos.ts` file, so it can be directly imported.

ℹ️ `PUBLIC_PERMIT_CONTRACT` is an environment variable corresponding to the address of your NFT
contract. It is defined in the `.env` file.

Afterward, we will forge our operation to send to the Gas Station:
```ts
const mintOperation = await contract.methodsObject.mint_token([{
              owner: userAddress,
              token_id: 0,
              amount_: 1
          }]).toTransferParams()
```

Using Taquito, we forge a transfer operation on the `mint_token` entrypoint.
The parameters for this entrypoint are:
- `owner`: the future owner of the NFT
- `token_id`: ID of the token that we are going to mint
- `amount_`: the quantity of tokens we want to mint.

Finally, once the operation is forged, we can send it to the Gas Station API:
```ts
const response = await gasStationAPI.postOperation(userAddress, {
            destination: mintOperation.to,
            parameters: mintOperation.parameter
          });
```

The operation will take a few seconds to be processed by the Gas Station (usually 12/15 seconds) if everything is correct.
If an error occurs (insufficient funds, authorization issue for minting the NFT, etc.), an error code will be returned, which you can handle in your dApp to inform the user.


## Staking an NFT

Minting NFTs from a single address is a simple enough example to start. However, a complete
application would typically offer the possibility for the users to transfer or sell their NFTs. As
final users do not have tez in their wallet, all the transactions are posted by the Gas Station.

Despite this centralization, it is still possible to maintain security and non-custodiality using
permits. In this section, we call _staking_ the operation of sending an NFT to a contract. As the
user owns the NFT, it is appropriate to sign a permit (authorization) to perform this transfer.

To facilitate the development of this new feature, we will also use the TypeScript SDK (for reference, you have all the information [here](./library.md))

To start, let's initialize the `GasStation` and `PermitContract`  classes from the SDK:

ℹ️ `GasStation` class will target the Gas Station deployed on Ghostnet by default.

```ts
const gasStationApi = new GasStation();
const permitContract = new PermitContract(PUBLIC_PERMIT_CONTRACT, Tezos);
```

Now we can generate our permit using the `generatePermit` method:
```ts
const permitData = await permitContract.generatePermit({
        from_: userAddress,
        txs: [{
          to_: PUBLIC_STAKING_CONTRACT,
          token_id,
          amount: 1
        }]
      });
```
Some explanations:
- The variable `PUBLIC_STAKING_CONTRACT` contains the address of the staking contract (available at this address [`KT1VVotciVbvz1SopVfoXsxXcpyBBSryQgEn`](https://ghostnet.tzkt.io/KT1VVotciVbvz1SopVfoXsxXcpyBBSryQgEn/operations) on Ghostnet).
- The `token_id` corresponds to the ID of the token you want to stake.

`permitData` then contains the hash of the permit `bytes` and the hash of transfer operation `transfer_hash`:
```ts
{
    bytes: string;
    transfer_hash: string;
}
```

Next, we need to have the owner of the token sign this permit and retrieve the signature.

This is easily done using Taquito:
```ts
const signature = (await (await wallet.client).requestSignPayload({
          signingType: SigningType.MICHELINE,
          payload: permit_data.bytes
      })).signature;
```

Once we have the signed permit, we can register it with the contract that implements the `permit` entrypoint.

Again, we can use the SDK for this:
```ts
const permitOperation = await permitContract.permitCall({
          publicKey: activeAccount.publicKey,
          signature: signature,
          transferHash: permit_data.transfer_hash
      });
```

- `publicKey` is the public key of the token's owner
- `signature` is the signature of the permit obtained in the previous step
- `transferHash` is the hash of the transfer operation returned during the permit creation


At this point, we have all the necessary information regarding the permit. Now, we can forge the staking operation itself and send everything to the Gas Station.

To forge the staking operation, we follow the usual process: we retrieve the contract instance using Taquito and craft the operation to get the parameters.

```ts
const stakingContract = await Tezos.wallet.at(PUBLIC_STAKING_CONTRACT);
const stakingOperation = await stakingContract.methods.stake(
        1,
        userAddress
      ).toTransferParams();
```
ℹ️ `PUBLIC_STAKING_CONTRACT` is also an environment variable containing the staking contract's address.

All that remains is to send the operation to the Gas Station to have the gas fees covered:

```ts
const response = await gasStationApi.postOperations(userAddress,
          [
            {
              destination: permitOperation.to,
              parameters: permitOperation.parameter
            },
            {
              destination: stakingOperation.to,
              parameters: stakingOperation.parameter
            }
          ]);
```

Here, we use `postOperations` to submit a batch of operations. This batch contains the operation to
register the permit and the staking operation. When calling the staking contract's `stake`
entrypoint, the permit will be revealed and consumed.

Similar to the minting operation, the Gas Station will respond in a few tens of seconds.

## Conclusion

This simple example shows how a user without any tez can mint an NFT and transfer it to another
contract in a secure way. This is possible thanks to the Gas Station, which relays the transaction
by paying the fees.

Feel free to send us your feedback and comments on this tutorial. 😃
