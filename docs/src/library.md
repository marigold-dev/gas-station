# SDKs

## Getting started

To enhance the user experience, we have developed two SDKs (for now) to integrate into your web applications. They will facilitate easy interaction with the Gas Station. Currently, we have developed an SDK for Typescript and another one for Unity.

### Typescript

#### Installation

To install the Typescript SDK, run :

```bash
npm install --save @marigold-dev/gas-station-lib
```

#### Explanations

The SDK consists of two classes : `GasStation` and `PermitContract`.

The `GasStation` class enables easy communication with the Gas Station API without the need to manually initialize the HTTP request.

To initialize this class, you need to provide it with a Gas Station API URL. For now, you can use `https://gas-station-api.marigold.dev/operation`.

The class has two methods:
- `postOperation` takes a `sender` parameter (usually the user's address) and an `operation` of the following type:
```ts
export type Operation = {
  destination: string;
  parameters: unknown;
};
```
This method then prepares the HTTP request and sends it to the `/operation` endpoint of the API, which processes the operation.

- `postOperations` also takes a `sender` and an array of `Operation`, allowing you to send multiple operations at once.


The `PermitContract` class allows the generation of a permit [TZIP-17](https://tzip.tezosagora.org/proposal/tzip-17) for a given contract.

> A permit is an authorization to call a specific endpoint of a smart contract with a specified parameter on behalf of a given address. This authorization may have an expiration. It is particularly useful for handling FA tokens when the user has ownership (transfer, update_operation, approve).

This class has two methods:
- `generatePermit` creates a permit from a transfer operation. It returns an object containing:
```ts
{
  bytes: string, // the bytes containing the permit
  transfer_hash: string, // the hash of the transfer operation
}
```

After calling `generatePermit`, you need to have the token owner sign the bytes to finalize the permit.

- `permitCall` allows calling the `permit` entrypoint on the target contract. This registers the permit in the contract storage (refer to [TZIP-17](https://tzip.tezosagora.org/proposal/tzip-17)). This method takes an object of type:
```ts
type PermitOperation = {
  publicKey: string;
  signature: string;
  transferHash: string;
};
```
and returns an operation of type `TransferParams`.

#### Usage

To begin, you need to import and initialize the `GasStation` object from the SDK:
```ts
import { GasStation } from '@marigold-dev/gas-station-lib'

const gasApi = new GasStation({
  apiURL: 'https://gas-station-api.marigold.dev/'
})
```

Next, you can forge your operation, for example, to mint an NFT (assuming the contract has a `mint_token` entrypoint):

```ts
const mintOperation = await contract.methodsObject.mint_token([{
              owner: userAddress,
              token_id: tokenId,
              amount_: 1
          }]).toTransferParams()
```

Finally, you can send your operation to the Gas Station with:
```ts
const response = await gasApi.postOperation(userAddress, {
            destination: mintOperation.to,
            parameters: mintOperation.parameter
          });
```

### Unity

🚧 Work in Progress 🚧