# SDKs

## Getting started

We propose two SDKs (in TypeScript and in Unity) to use the Gas Station from your applications.

### Typescript

#### Installation

To install the Typescript SDK in your project, run:

```bash
npm install --save @marigold-dev/gas-station-lib
```

#### Explanations

The SDK consists of two classes: `GasStation` and `PermitContract`.

There are also two variables:
  - `GAS_STATION_PUBLIC_API_GHOSTNET` which redirect to [https://ghostnet.gas-station-api.marigold.dev/operation](https://ghostnet.gas-station-api.marigold.dev/operation)
  - `GAS_STATION_PUBLIC_API_MAINNET` which redirect to [https://gas-station-api.marigold.dev/operation](https://gas-station-api.marigold.dev/operation) (Not available yet)

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

- `postOperations` also takes a `sender` and an array of `Operation`, allowing you to send multiple
  operations at once. These operations will be treated atomically by the API: if the simulation of
  one operation fails, then they are all discarded.

The `PermitContract` class allows the generation of a off-chain permit [TZIP-17](https://tzip.tezosagora.org/proposal/tzip-17) for a contract implementing TZIP-17.

> A permit is an authorization to call a specific endpoint of a smart contract with a specified parameter on behalf of a given address. This authorization may have an expiration. It is particularly useful for handling FA tokens when the user has ownership (transfer, update_operation, approve).

This class has two methods:
- `generatePermit` creates a permit from a transfer operation. It returns an object containing:
```ts
{
  bytes: string, // the bytes containing the permit
  transfer_hash: string, // the hash of the transfer operation
}
```

After calling `generatePermit`, you need to ask the token owner for their signature.

- `permitCall` generates the permit operation using the `permit` entrypoint on the target contract. This method takes an object of type:
```ts
type PermitOperation = {
  publicKey: string;
  signature: string;
  transferHash: string;
};
```
and returns an operation of type `TransferParams`, which can be sent using the GasStation class.

#### Usage

First import and initialize the `GasStation` object from the SDK:
```ts
import { GasStation } from '@marigold-dev/gas-station-lib'

const gasApi = new GasStation()
```

ℹ️ NOTE: By default, the Gas Station used by the SDK is the Marigold one on Ghostnet but you can also provide a `apiURL` like:
```ts
import { GasStation, GAS_STATION_PUBLIC_API_GHOSTNET} from '@marigold-dev/gas-station-lib'

const gasApi = new GasStation({
  apiURL: GAS_STATION_PUBLIC_API_GHOSTNET // or the URL directly
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
