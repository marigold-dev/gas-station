#import "../permit-cameligo/src/main.mligo" "FA2"

type storage = {
  nft_address: address;
  stashed: (address, nat) big_map;
}

(* We need to provide the address of the NFT's owner so that the transfer can be done by someone
 * else (we don't rely on Tezos.get_sender ()) *)

[@entry]
let stash (qty, sender: nat * address) (storage: storage): operation list * storage =
  let stashed = match Big_map.find_opt sender storage.stashed with
    | None -> Big_map.add sender qty storage.stashed
    | Some n -> Big_map.update sender (Some (n + qty)) storage.stashed
  in
  let contract = match (Tezos.get_contract_opt storage.nft_address: (FA2 parameter_of) contract option) with
    | None -> failwith "Invalid NFT contract"
    | Some contract -> contract
  in
  let transfer = [{
    from_ = sender;
    txs = [{
      to_ = Tezos.get_self_address ();
      token_id = 0n;
      amount = qty;
    }]
  }]
  in
  let op = Tezos.transaction (Transfer transfer: FA2 parameter_of) 0tez contract in
  [op], { storage with stashed=stashed }

[@entry]
let unstash (_sender: address) (_storage: storage): operation list * storage =
  failwith "Not implemented"
