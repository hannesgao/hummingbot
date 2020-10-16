import importlib
from os import scandir
from os.path import (
    realpath,
    join,
)
from enum import Enum
from decimal import Decimal
from typing import List, NamedTuple, Dict
from hummingbot import get_strategy_list
from pathlib import Path
from hummingbot.client.config.config_var import ConfigVar

# Global variables
required_exchanges: List[str] = []

# Global static values
KEYFILE_PREFIX = "key_file_"
KEYFILE_POSTFIX = ".json"
ENCYPTED_CONF_PREFIX = "encrypted_"
ENCYPTED_CONF_POSTFIX = ".json"
GLOBAL_CONFIG_PATH = "conf/conf_global.yml"
TRADE_FEES_CONFIG_PATH = "conf/conf_fee_overrides.yml"
TOKEN_ADDRESSES_FILE_PATH = realpath(join(__file__, "../../wallet/ethereum/erc20_tokens.json"))
DEFAULT_KEY_FILE_PATH = "conf/"
DEFAULT_LOG_FILE_PATH = "logs/"
DEFAULT_ETHEREUM_RPC_URL = "https://mainnet.coinalpha.com/hummingbot-test-node"
TEMPLATE_PATH = realpath(join(__file__, "../../templates/"))
CONF_FILE_PATH = "conf/"
CONF_PREFIX = "conf_"
CONF_POSTFIX = "_strategy"
SCRIPTS_PATH = "scripts/"


class ConnectorType(Enum):
    Connector = 1
    Exchange = 2
    Derivative = 3


class ConnectorFeeType(Enum):
    Percent = 1
    FlatFee = 2


class ConnectorSetting(NamedTuple):
    name: str
    type: ConnectorType
    example_pair: str
    centralised: bool
    use_ethereum_wallet: bool
    fee_type: ConnectorFeeType
    fee_token: str
    default_fees: List[Decimal]
    config_keys: List[ConfigVar]


def _create_connector_settings() -> Dict[str, ConnectorSetting]:
    connector_exceptions = ["paper_trade"]
    connector_settings = {}
    package_dir = Path(__file__).resolve().parent.parent.parent
    type_dirs = [f for f in scandir(f'{str(package_dir)}/hummingbot/connector') if f.is_dir()]
    for type_dir in type_dirs:
        connector_dirs = [f for f in scandir(type_dir.path) if f.is_dir()]
        for connector_dir in connector_dirs:
            if connector_dir.name.startswith("_") or \
                    connector_dir.name in connector_exceptions or \
                    not any(f.name == f"{connector_dir.name}_utils.py" for f in scandir(connector_dir.path)):
                continue
            if connector_dir.name in connector_settings:
                raise Exception(f"Multiple connectors with the same {connector_dir.name} name.")
            path = f"hummingbot.connector.{type_dir.name}.{connector_dir.name}.{connector_dir.name}_utils"
            util_module = importlib.import_module(path)
            if util_module is None:
                raise Exception(f"{path} does not exist.")
            fee_type = ConnectorFeeType.Percent
            fee_type_setting = getattr(util_module, "FEE_TYPE", None)
            if fee_type_setting is not None:
                fee_type = ConnectorFeeType[fee_type_setting]
            connector_settings[connector_dir.name] = ConnectorSetting(
                name=connector_dir.name,
                type=ConnectorType[type_dir.name.capitalize()],
                centralised=getattr(util_module, "CENTRALIZED", True),
                example_pair=getattr(util_module, "EXAMPLE_PAIR", ""),
                use_ethereum_wallet=getattr(util_module, "USE_ETHEREUM_WALLET", False),
                fee_type=fee_type,
                fee_token=getattr(util_module, "FEE_TOKEN", ""),
                default_fees=getattr(util_module, "DEFAULT_FEES", []),
                config_keys=getattr(util_module, "KEYS", [])
            )
    return connector_settings


def ethereum_wallet_required() -> bool:
    return any(e in ETH_WALLET_CONNECTORS for e in required_exchanges)


MAXIMUM_OUTPUT_PANE_LINE_COUNT = 1000
MAXIMUM_LOG_PANE_LINE_COUNT = 1000
MAXIMUM_TRADE_FILLS_DISPLAY_OUTPUT = 100

CONNECTOR_SETTINGS = _create_connector_settings()
DERIVATIVES = {cs.name for cs in CONNECTOR_SETTINGS.values() if cs.type is ConnectorType.Derivative}
EXCHANGES = {cs.name for cs in CONNECTOR_SETTINGS.values() if cs.type is ConnectorType.Exchange}
OTHER_CONNECTORS = {cs.name for cs in CONNECTOR_SETTINGS.values() if cs.type is ConnectorType.Connector}
ETH_WALLET_CONNECTORS = {cs.name for cs in CONNECTOR_SETTINGS.values() if cs.use_ethereum_wallet}
ALL_CONNECTORS = {"exchange": EXCHANGES, "connector": OTHER_CONNECTORS, "derivative": DERIVATIVES}
EXAMPLE_PAIRS = {name: cs.example_pair for name, cs in CONNECTOR_SETTINGS.items()}
EXAMPLE_ASSETS = {name: cs.example_pair.split("-")[0] for name, cs in CONNECTOR_SETTINGS.items()}

STRATEGIES: List[str] = get_strategy_list()
