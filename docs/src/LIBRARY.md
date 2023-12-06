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

#### Explanations

Le SDK est composé de deux classes : `GasStation` et `PermitContract`.

La classe `GasStation` permet de communiquer facilement avec l'API de la Gas Station, sans avoir à initiliaser soit-même la requete HTTP.

Pour initialiser cette classe, il faut lui donner une URL d'API de Gas Station. Pour le moment, vous pouvez donner `https://gas-station-api.marigold.dev/operation`.

La classe possède deux méthodes :
- `postOperation` prend en paramètre un `sender` (généralement l'adresse de l'utilisateur) et une `operation` de type
```ts
export type Operation = {
  destination: string;
  parameters: unknown;
};
```
Cette méthode va ensuite préparer la requête HTTP et l'envoyer sur le endpoint `/operation` de l'API, qui traiter l'operation.

- `postOperations` prend également un `sender` et un tableau d' `Operation` et permet d'envoyer plusieurs opérations à la fois.



La classe `PermitContract` permet de générer un permit [TZIP-17](https://tzip.tezosagora.org/proposal/tzip-17) pour un contrat donné.

> Un permis est une autorisation à appeler un endpoint spécifique d'un smart contrat avec un paramètre spécifié pour le compte d'une adresse donnée. Cette autorisation peut éventuellement expirer. Il est notamment utile pour la manipulation de tokens FA lorsque c'est l'utilisateur qui a le ownership (transfer, update_operation, approve)

Cette classe a deux méthodes :
- `generatePermit` permet de créer un permis à partir d'une operation de transfert. Elle retourne un objet contenant
```ts
{
  bytes: string, // les bytes contenant le permis
  transfer_hash: string, // le hash de l'operation de transfet
}
```

Suite à l'appel de `generatePermit`, vous devrez faire signer les bytes par le owner du token pour finaliser le permis.

- `permitCall` permet d'appeler l'entrypoint `permit` sur le contrat cible. Cela va permettre d'enregister le permis dans le storage du contrat (cf TZIP-17).
Cette méthode prend en paramètre un objet de type
```ts
type PermitOperation = {
  publicKey: string;
  signature: string;
  transferHash: string;
};
```
et retourne une opération de type `TransferParams`.

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