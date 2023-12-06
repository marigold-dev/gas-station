# Tutorial

Pour comprendre le potentiel et comment utiliser la Gas Station, nous allons reprendre l'exemple simple des NFT disponible à cette adresse : https://gas-station-nft-example.marigold.dev

## Template

La première chose à faire est de récupérer le template de code situé [ici](https://github.com/marigold-dev/gas-station-lib).
Une fois récupéré, vous pouvez run ces commandes :
```
npm install
npm run check
```
Pour tester que tout se lance correctement, vous pouvez utilise
```
npm run dev
```

Les fichiers qui vont nous intéressés se situent dans `src/lib`. Vous allez y trouver des composants en Svelte et un fichier `tezos.ts` qui regroupe des fonctions utilitaires comme la connexion au wallet, etc...

## Minting

Nous allons commencer par le mint d'un NFT par un utilisateur. Le contrat que nous allons utiliser est disponible à cette adresse sur Ghostnet : `KT199yuNkHQKpy331A6fvWJtQ1uan9uya2jx`
Le but ici est que l'utilisateur initie l'action de mint et puisse récupérer son NFT sans avoir à payer les frais de gas.
Pour cela nous allons utiliser le SDK Typescript dont vous pouvez retrouver les informations [ici](./LIBRARY.md)

D'abord nous allons initialiser le SDK GasStation comme suit:
```ts
const gasStationAPI = new GasStation({
  apiURL: PUBLIC_GAS_STATION_API
})
```
:info: `PUBLIC_GAS_STATION_API` est une variable d'environnement disponible dans le fichier `.env`

Ensuite nous allons récupérer une instance de notre contrat, à l'aide de [Taquito](taquito).
```ts
const contract = await Tezos.wallet.at(PUBLIC_PERMIT);
```
:info: L'instance `Tezos` de Taquito est déjà initialisé dans le fichier `tezos.ts`, on peut donc directement l'importer.
:info: `PUBLIC_PERMIT` est également une variable d'environnement qui correspond à l'adresse de votre contrat de NFT

Après cela nous allons forger notre opération à envoyer à la Gas Station
```ts
const mint_op = await contract.methodsObject.mint_token([{
              owner: user_address,
              token_id: 0, //TODO : Make the possibility to change token_id
              amount_: 1
          }]).toTransferParams()
```

A l'aide de Taquito, nous forgeons une opération de transfert sur l'entrypoint `mint_token`.
Les paramètres de cet entrypoint sont :
- `owner` : le futur propriétaire du NFT
- `token_id` : l'ID du token (NFT) que nous allons minté (sur le contrat pointé au dessus, il y en a 6 disponibles)
- `amount_` : la quantité de tokens que nous voulons minté. Ici 1 seul est déjà suffisant.

Enfin, une fois l'opération forgée, nous pouvons l'envoyer à l'API de la Gas Station :
```ts
const response = await gasStationAPI.postOperation(user_address, {
            destination: mint_op.to,
            parameters: mint_op.parameter
          });
```

L'opération va mettre quelques secondes à être traitée par la Gas Station (généralement 12/15 secondes) si tout va bien. Si une erreur s'est produite (fonds insuffisants, problème d'autorisation pour mint le NFT...), un code d'erreur sera renvoyé, que vous pourrez traiter dans votre dApp pour informer l'utilisateur.


## Staking

Pour le staking, nous avons besoin d'un permis. En effet, le staking consiste à transférer notre NFT fraîchement minté vers le contrat. Comme le NFT nous appartient, il convient de signer un permis (une autorisation) pour pouvoir effectuer ce transfert.

Pour faciliter le développement de cette nouvelle feature, nous allons également utiliser le SDK Typescript (pour rappel, vous avez toutes les informations [ici](./LIBRARY.md))

Pour commencer, nous allons initialiser les classes `GasStation` et `PermitContract` du SDK :
```ts
const gasStationApi = new GasStation({
        apiURL: PUBLIC_GAS_STATION_API
      });
const permitContract = new PermitContract(PUBLIC_PERMIT, Tezos);
```

Maintenant nous pouvons générer notre permis à l'aide de la méthode `generatePermit` :
```ts
const permit_data = await permit_contract.generatePermit({
        from_: user_address,
        txs: [{
          to_: PUBLIC_STAKING_CONTRACT,
          token_id,
          amount: 1
        }]
      });
```
Quelques explications :
- La variable `PUBLIC_STAKING_CONTRACT` contient l'adresse du contrat de staking (disponible à cette adresse `KT1MLMXwFEMcfByGbGcQ9ow3nsrQCkLbcRAu` sur Ghostnet)
- Le `token_id` correspond à l'ID du token que vous voulez stake

`permit_data` contient alors le hash du permis `bytes` et le hash de l'opération de transfert `transfer_hash`
```ts
{
    bytes: string;
    transfer_hash: string;
}
```

On doit ensuite faire signer ce permis par l'utilisateur propriétaire du token et récupérer cette signature.

Cela se fait facilement à l'aide de Taquito :
```ts
const signature = (await (await wallet.client).requestSignPayload({
          signingType: SigningType.MICHELINE,
          payload: permit_data.bytes
      })).signature;
```

Une fois que nous avons le permis signé, nous pouvons l'enregistrer auprès du contrat qui implémente l'entrypoint `permit`.

On va encore pouvoir utiliser le SDK pour faire cela :
```ts
const permit_op = await permit_contract.permitCall({
          publicKey: activeAccount.publicKey,
          signature: signature,
          transferHash: permit_data.transfer_hash
      });
```

- publicKey est la clé publique du propriétaire du token
- signature est la signature du permis récupérée à l'étape précédente
- transferHash est le hash de l'opération de transfert renvoyé lors de la création du permis


A ce stade, nous avons toutes les informations nécessaires concernant le permis. Nous allons maintenant pouvoir forgé l'opération de staking à proprement parler et envoyer le tout à la Gas Station.

Pour forger l'opération de staking, on fait comme d'habitude, on récupère l'instance du contrat à l'aide de Taquito et l'on craft l'opération pour récupérer les paramètres.

```ts
const staking_contract = await Tezos.wallet.at(PUBLIC_STAKING_CONTRACT);
const staking_op = await staking_contract.methods.stake(
        1,
        user_address
      ).toTransferParams();
```
:info: `PUBLIC_STAKING_CONTRACT` est une variable d'environnement contenant l'adresse du contrat implémentant l'entrypoint de staking

Il ne nous reste plus qu'à envoyer l'opération à la Gas Station afin que les frais de gas soient payés :

```ts
const response = await gas_api.postOperations(user_address,
          [
            {
              destination: permit_op.to,
              parameters: permit_op.parameter
            },
            {
              destination: staking_op.to,
              parameters: staking_op.parameter
            }
          ]);
```

Ici on utilise `postOperations` pour poster un batch d'opérations. Ce batch contient l'opération pour enregistrer le permis et l'opération de staking.
Lorsque l'on appelera l'entrypoint `stake` du contrat de staking, le permis sera revélé et consommé.

Comme pour l'opération de mint, la Gas Station répondra en qq dizaines de secondes.