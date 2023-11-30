# Gas Station Webapp

Pour faciliter l'expérience utilisateur avec la Gas Station et notamment l'interaction avec les contrats et le management du budget pour payer les fees, nous avons développer une webapp, disponible [ici](https://gas-station.marigold.dev/).

⚠️ Note : disponible seulement sur Ghostnet pour le moment ⚠️

## Usage

### Wallet connexion

Comme toutes les dApps, une des premières choses à faire est de connecter votre wallet en cliquant sur le bouton en haut à droite.

![Wallet connection](./assets/wallet_connection.png)

### Your contracts

Sur la homepage vous pourrez retrouver tous vos contracts enregistrés sur la Gas Station ainsi que leurs entrypoints activés.

![Homepage](./assets/homepage.png)

### Add a new contract

Pour ajouter un nouveau contract, cliquer sur `Add contract` et remplissez les informations demandées.
Remplissez en premier l'adresse du contrat afin de récupérer les entrypoints associés à votre contrat.
Donnez ensuite un nom et activer les entrypoints pour lesquels vous voulez payer les fees.

![Add contract](./assets/add-contract.png)

### Add credits on your vault

Pour ajouter des crédits dans votre vault, aller sur la page `My credits`. Renseignez ensuite le nombre de XTZ que vous voulez envoyer sur votre vault et valider. Après quelques dizaines de secondes, le montant de votre vault et votre balance vont se mettre à jour et le transfert sera effectif.

![Add credits](./assets/add-credits.png)


### Withdraw

Vous pouvez également withdraw des XTZ de votre vault. Pour cela, sur la page `My credits`, renseigner le nombre de XTZ que vous voulez withdraw et valider.
Vous allez devoir signer la transaction avec votre wallet pour que nous nous assurons que les credits vont à la bonne adresse.


### Test

Une fois le contrat ajouté et les crédits transférés sur votre vault, vous pouvez intégrer la Gas Station dans votre dApps en suivant ce [guide](./WELCOME.md). Vous pourrez ainsi testé la bonne intégration de la Gas Station avec votre dApps