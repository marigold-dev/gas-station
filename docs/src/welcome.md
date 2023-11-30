TODO :
PRODUCTS :
- API
- WEBAPP
- SDK TS
- SDK Unity

# Welcome on Gas Station

## Introduction

 The Gas Station is a tool for developers who want to offer feeless transactions to their users. It can be used to facilitate user onboarding, or with a specific economic model in mind (e.g., the user can mint a NFT freely, but pays a fee when reselling it).

The gas station would typically be used by video game developers who want to subsidize activity for users who do not own have any tez in their wallet. It does not require these users to do any transaction or reveal their account, as the gas station account posts those transactions itself. However, this workflow may require the use of specific smart contracts patterns, such as permit (TZIP 17).

Actuellement, l'URL de l'API pour Ghostnet est : `https://gas-station-api.marigold.dev`
La Gas Station n'est pas encore disponible sur Mainnet.

## Getting started

Afin de faciliter l'expérience utilisateur, nous avons developpé deux SDKs (pour le moment) à intégrer dans vos webapps.
Ils permettront d'interagir avec la Gas Station facilement.
Pour le moment nous avons développé un SDK pour Typescript et un SDK pour Unity.

### Typescript

#### Installation

Pour installer le SDK Typescript, il faut executer :

```bash
npm install --save @marigold-dev/gas-station-lib
```

#### Usage

Pour commencer, il faut importer et initialiser l'objet `GasStation` du SDK :

```ts
import { GasStation } from '@marigold-dev/gas-station-lib'

const gasApi = new GasStation({
  apiURL: 'https://gas-station-api.marigold.dev/'
})
```

Vous pouvez ensuite forger votre operation, par exemple mint un NFT (ici le contrat possède un entrypoint `mint_token`):

```ts
const mintOperation = await contract.methodsObject.mint_token([{
              owner: userAddress,
              token_id: tokenId,
              amount_: 1
          }]).toTransferParams()
```

Et enfin, vous pouvez envoyer votre operation à la Gas Station avec :
```ts
const response = await gasApi.postOperation(userAddress, {
            destination: mintOperation.to,
            parameters: mintOperation.parameter
          });
```

### Unity

🚧 Work in Progress 🚧