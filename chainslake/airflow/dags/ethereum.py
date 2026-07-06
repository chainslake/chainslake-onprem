# The DAG object; we'll need this to instantiate a DAG
from airflow.models.dag import DAG
from datetime import datetime
# Operators; we need this to operate!
from airflow.operators.bash import BashOperator
import os
with DAG(
    "Ethereum",
    # These args will get passed on to each operator
    # You can override them on a per-task basis during operator initialization
    default_args={
        "depends_on_past": True,
        'wait_for_downstream': False,
        "email": ["lakechain.nguyen@gmail.com"],
        "email_on_failure": False,
        "email_on_retry": False,
        "retries": 2
    },
    description="Ethereum pipeline",
    start_date=datetime(2025, 10, 11, 0),
    # schedule="@continuous",
    schedule="10 0 * * *",
    # schedule="@once",
    max_active_runs=1,
    max_active_tasks=10,
    is_paused_upon_creation=True,
) as dag:

    ########################### ORIGIN ##########################################

    RUN_DIR = os.environ.get("CHAINSLAKE_HOME_DIR") + "/jobs/ethereum"

    ethereum_origin_transaction_blocks = BashOperator(
        task_id="ethereum_origin.transaction_blocks",
        bash_command=f"cd {RUN_DIR} && ./origin/transaction_blocks.sh "
    )

    ethereum_origin_blocks_receipt = BashOperator(
        task_id="ethereum_origin.blocks_receipt",
        bash_command=f"cd {RUN_DIR} && ./origin/blocks_receipt.sh "
    )

    ethereum_origin_transaction_blocks >> ethereum_origin_blocks_receipt

    ############################################## EXTRACT #############################

    ethereum_blocks = BashOperator(
        task_id="ethereum.blocks",
        bash_command=f"cd {RUN_DIR} && ./extract/blocks.sh "
    )

    ethereum_origin_blocks_receipt >> ethereum_blocks

    ethereum_logs = BashOperator(
        task_id="ethereum.logs",
        bash_command=f"cd {RUN_DIR} && ./extract/logs.sh "
    )

    ethereum_transactions = BashOperator(
        task_id="ethereum.transactions",
        bash_command=f"cd {RUN_DIR} && ./extract/transactions.sh "
    )

    ethereum_origin_blocks_receipt >> [ethereum_transactions, ethereum_logs]


    ############################################# DECODED ###########################################

    ethereum_decoded_erc20_evt_transfer = BashOperator(
        task_id="ethereum_decoded.erc20_evt_transfer",
        bash_command=f"cd {RUN_DIR} && ./contract/decoded_log.sh erc20_evt_transfer backward "
    )

    ethereum_logs >> ethereum_decoded_erc20_evt_transfer

    ############################################# Contract ###########################################

    ethereum_contract_erc20_tokens = BashOperator(
        task_id="ethereum_contract.erc20_tokens",
        bash_command=f"cd {RUN_DIR} && ./contract/erc20_tokens.sh "
    )

    ethereum_decoded_erc20_evt_transfer >> ethereum_contract_erc20_tokens

    ############################################# TOKEN ###########################################

    ethereum_token_erc20_transfer = BashOperator(
        task_id="ethereum_token.erc20_transfer",
        bash_command=f"cd {RUN_DIR} && ./token/erc20_transfer.sh "
    )

    [ethereum_transactions, ethereum_decoded_erc20_evt_transfer] >> ethereum_token_erc20_transfer
    ethereum_contract_erc20_tokens >> ethereum_token_erc20_transfer


