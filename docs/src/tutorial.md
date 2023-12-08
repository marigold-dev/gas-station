# Tutorial

To understand the potential and how to use the Gas Station, let's walk through the simple example of NFTs available at this [address](https://ghostnet.gas-station-nft-example.marigold.dev).

## Template

The first step is to retrieve the code template located [here](https://github.com/marigold-dev/gas-station-lib).
Once retrieved, you can run the following commands:
```
npm install
npm run check
```
To test that everything works well, you can use:
```
npm run dev
```

The files of interest are located in `src/lib`. You will find Svelte components and a `tezos.ts` file that contains utility functions such as wallet connection, etc.

## Minting

We'll start with minting an NFT by a user. The contract we'll use is available at this address on Ghostnet: `KT199yuNkHQKpy331A6fvWJtQ1uan9uya2jx`.
The goal here is for the user to initiate the mint action and retrieve their NFT without having to pay gas fees. For this, we will use the TypeScript SDK, and you can find more information [here](./library.md).

First, we'll setup the GasStation SDK as follows:
```ts
const gasStationAPI = new GasStation({
  apiURL: PUBLIC_GAS_STATION_API
})
```
ℹ️ `PUBLIC_GAS_STATION_API` is an environment variable available in `.env`

Next, we'll retrieve an instance of our contract, using [Taquito](https://tezostaquito.io/).

```ts
const contract = await Tezos.wallet.at(PUBLIC_PERMIT_CONTRACT);
```

ℹ️ The `Tezos` instance of Taquito is already initialized in the `tezos.ts` file, so it can be directly imported.

ℹ️ `PUBLIC_PERMIT_CONTRACT` is also an environment variable corresponding to the address of your NFT contract.

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
- `owner` : the future owner of the NFT
- `token_id` : l'ID of the token (NFT) that we are going to mint
- `amount_` : the quantity of tokens we want to mint.

Finally, once the operation is forged, we can send it to the Gas Station API:
```ts
const response = await gasStationAPI.postOperation(userAddress, {
            destination: mintOperation.to,
            parameters: mintOperation.parameter
          });
```

The operation will take a few seconds to be processed by the Gas Station (usually 12/15 seconds) if everything is correct.
If an error occurs (insufficient funds, authorization issue for minting the NFT, etc.), an error code will be returned, which you can handle in your dApp to inform the user.


## Staking

For staking, we need a permit. Staking involves transferring our freshly minted NFT to the contract. As we own the NFT, it is appropriate to sign a permit (authorization) to perform this transfer.

To facilitate the development of this new feature, we will also use the TypeScript SDK (for reference, you have all the information [here](./library.md))

To start, let's initialize the `GasStation` and `PermitContract`  classes from the SDK:
```ts
const gasStationApi = new GasStation({
        apiURL: PUBLIC_GAS_STATION_API
      });
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
- The variable `PUBLIC_STAKING_CONTRACT` contains the address of the staking contract (available at this address `KT1MLMXwFEMcfByGbGcQ9ow3nsrQCkLbcRAu` on Ghostnet).
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
ℹ️ `PUBLIC_STAKING_CONTRACT` is an environment variable containing the contract's address implementing the staking contract.

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

Here, we use `postOperations` to submit a batch of operations. This batch contains the operation to register the permit and the staking operation. When calling the staking contract's `stake` entrypoint, the permit will be revealed and consumed.

Similar to the minting operation, the Gas Station will respond in a few tens of seconds.