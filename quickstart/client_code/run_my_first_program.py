import asyncio
import py_nillion_client as nillion
import os

from py_nillion_client import NodeKey, UserKey
from dotenv import load_dotenv
from nillion_python_helpers import get_quote_and_pay, create_nillion_client, create_payments_config

from cosmpy.aerial.client import LedgerClient
from cosmpy.aerial.wallet import LocalWallet
from cosmpy.crypto.keypairs import PrivateKey

home = os.getenv("HOME")
load_dotenv(f"{home}/.config/nillion/nillion-devnet.env")

async def main():
    cluster_id = os.getenv("NILLION_CLUSTER_ID")
    grpc_endpoint = os.getenv("NILLION_NILCHAIN_GRPC")
    chain_id = os.getenv("NILLION_NILCHAIN_CHAIN_ID")
    seed = "my_seed"
    userkey = UserKey.from_seed(seed)
    nodekey = NodeKey.from_seed(seed)

    client = create_nillion_client(userkey, nodekey)

    party_id = client.party_id
    user_id = client.user_id

    program_name = "main"
    program_mir_path = f"../nada_quickstart_programs/target/{program_name}.nada.bin"

    payments_config = create_payments_config(chain_id, grpc_endpoint)
    payments_client = LedgerClient(payments_config)
    payments_wallet = LocalWallet(
        PrivateKey(bytes.fromhex(os.getenv("NILLION_NILCHAIN_PRIVATE_KEY_0"))),
        prefix="nillion",
    )

    receipt_store_program = await get_quote_and_pay(
        client,
        nillion.Operation.store_program(program_mir_path),
        payments_wallet,
        payments_client,
        cluster_id,
    )

    action_id = await client.store_program(
        cluster_id, program_name, program_mir_path, receipt_store_program
    )

    program_id = f"{user_id}/{program_name}"
    print("Stored program. action_id:", action_id)
    print("Stored program_id:", program_id)

    # Define and store secrets
    nr_people = 3
    attributes = ["age", "gender", "interested_in", "honesty", "humor", "adventure", "music", "cooking"]
    secrets = {}

    for p in range(nr_people):
        for attr in attributes:
            if attr == "age":
              prompt = f"Enter age for Person {p}: "
            elif attr == "gender":
                prompt = f"Enter gender (1 for male, 2 for female, 3 for other) for Person {p}: "
            elif attr == "interested_in":
                prompt = f"Enter gender interested in (1 for male, 2 for female, 3 for other, 4 for all) for Person {p}: "
            else:
                prompt = f"Enter {attr} score (1-10) for Person {p}: "
            value = int(input(prompt))
            key = f"p{p}_{attr}"
            secrets[key] = nillion.SecretUnsignedInteger(value)

    new_secret = nillion.NadaValues(secrets)

    receipt_store = await get_quote_and_pay(
        client,
        nillion.Operation.store_values(new_secret, ttl_days=5),
        payments_wallet,
        payments_client,
        cluster_id,
    )

    # Set permissions for the stored values
    permissions = nillion.Permissions.default_for_user(client.user_id)
    permissions.add_compute_permissions({client.user_id: {program_id}})

    store_id = await client.store_values(
        cluster_id, new_secret, permissions, receipt_store
    )
    print(f"Stored secrets. Store ID: {store_id}")

    # Setup compute
    compute_bindings = nillion.ProgramBindings(program_id)
    for p in range(nr_people):
        compute_bindings.add_input_party(f"Person{p}", party_id)

    compute_bindings.add_output_party("OutParty", party_id)

    receipt_compute = await get_quote_and_pay(
        client,
        nillion.Operation.compute(program_id, nillion.NadaValues({})),
        payments_wallet,
        payments_client,
        cluster_id,
    )
    compute_id = await client.compute(
        cluster_id,
        compute_bindings,
        [store_id],
        nillion.NadaValues({}),
        receipt_compute
    )
    print(f"Computation initiated. Compute ID: {compute_id}")

    while True:
        compute_event = await client.next_compute_event()
        if isinstance(compute_event, nillion.ComputeFinishedEvent) and compute_event.uuid == compute_id:
            print(f"✅ Compute complete for compute_id {compute_event.uuid}")
            print(f"🖥️ The result is {compute_event.result.value}")
            return compute_event.result.value

if __name__ == "__main__":
    asyncio.run(main())
