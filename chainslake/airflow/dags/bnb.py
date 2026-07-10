# The DAG object; we'll need this to instantiate a DAG
from airflow.models.dag import DAG
from datetime import datetime
# Operators; we need this to operate!
from airflow.operators.bash import BashOperator
import os
with DAG(
    "BNB",
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
    description="BNB Smart Chain pipeline",
    start_date=datetime(2025, 10, 11, 0),
    # schedule="@continuous",
    schedule="10 0 * * *",
    # schedule="@once",
    max_active_runs=1,
    max_active_tasks=10,
    is_paused_upon_creation=True,
) as dag:

    ########################### ORIGIN ##########################################

    RUN_DIR = os.environ.get("CHAINSLAKE_HOME_DIR") + "/jobs/bnb"

    bnb_origin_transaction_blocks = BashOperator(
        task_id="bnb_origin.transaction_blocks",
        bash_command=f"cd {RUN_DIR} && ./origin/transaction_blocks.sh "
    )

    bnb_origin_blocks_receipt = BashOperator(
        task_id="bnb_origin.blocks_receipt",
        bash_command=f"cd {RUN_DIR} && ./origin/blocks_receipt.sh "
    )

    bnb_origin_transaction_blocks >> bnb_origin_blocks_receipt

    ############################################## EXTRACT #############################

    bnb_blocks = BashOperator(
        task_id="bnb.blocks",
        bash_command=f"cd {RUN_DIR} && ./extract/blocks.sh "
    )

    bnb_origin_blocks_receipt >> bnb_blocks

    bnb_logs = BashOperator(
        task_id="bnb.logs",
        bash_command=f"cd {RUN_DIR} && ./extract/logs.sh "
    )

    bnb_transactions = BashOperator(
        task_id="bnb.transactions",
        bash_command=f"cd {RUN_DIR} && ./extract/transactions.sh "
    )

    bnb_origin_blocks_receipt >> [bnb_transactions, bnb_logs]


    ############################################# DECODED ###########################################

    bnb_decoded_erc20_evt_transfer = BashOperator(
        task_id="bnb_decoded.erc20_evt_transfer",
        bash_command=f"cd {RUN_DIR} && ./contract/decoded_log.sh erc20_evt_transfer backward "
    )

    bnb_logs >> bnb_decoded_erc20_evt_transfer

    ############################################# Contract ###########################################

    bnb_contract_erc20_tokens = BashOperator(
        task_id="bnb_contract.erc20_tokens",
        bash_command=f"cd {RUN_DIR} && ./contract/erc20_tokens.sh "
    )

    bnb_decoded_erc20_evt_transfer >> bnb_contract_erc20_tokens

    ############################################# TOKEN ###########################################

    bnb_token_erc20_transfer = BashOperator(
        task_id="bnb_token.erc20_transfer",
        bash_command=f"cd {RUN_DIR} && ./token/erc20_transfer.sh "
    )

    [bnb_transactions, bnb_decoded_erc20_evt_transfer] >> bnb_token_erc20_transfer
    bnb_contract_erc20_tokens >> bnb_token_erc20_transfer
