from typing import Dict, Union

import pydantic
from loguru import logger
from pydantic import BaseModel

from engine_utils.singleton import SingletonMeta
from service.rtc_service.turn_providers.twilio_service import TwilioTurnProvider
from service.service_data_models.service_config_data import ServiceConfigData
from service.rtc_service.turn_providers.turn_service import TurnServerProvider

class RTCProvider(metaclass=SingletonMeta):
    def __init__(self):
        self.rtc_turn_providers = {
            "twilio": TwilioTurnProvider(),
            "turn": TurnServerProvider()
        }

    def prepare_rtc_configuration(self, config: Union[ServiceConfigData, BaseModel, Dict]):
        turn_entity = None
        logger.info(f"Parsing config: {config}")
        if isinstance(config, ServiceConfigData):
            rtc_config = config.rtc_config
        elif isinstance(config, BaseModel):
            rtc_config = config.model_dump()
        elif isinstance(config, Dict):
            rtc_config = config
        else:
            rtc_config = None
        if rtc_config is not None:
            logger.info(f"Parsing RTC config: {rtc_config}")
            turn_provider_name = "turn"
            turn_provider = None
            turn_provider_config = None
            logger.info(f"turn_provider_name: {turn_provider_name}")
            if turn_provider_name is not None:
                turn_provider = self.rtc_turn_providers.get(turn_provider_name)
                if turn_provider is None:
                    logger.warning(f"Turn provider {turn_provider_name} is not supported.")
                    turn_provider_name = None
                else:
                    config_model = turn_provider.get_config_model()
                    #turn_provider_config = config_model.model_validate(config)
                    turn_provider_config = RtcConfig(
                        #urls=["turn:turn.120-224-27-114.turnserver:3478", "turns:turn.120-224-27-114.turnserver:5349"],
                        urls=["turn:120.224.27.114:3478", "turns:120.224.27.114:5349"],
                        username="admin",
                        credential="admin@123~"
                    )
                    logger.info(f"turn_provider_config: {turn_provider_config}")
            if turn_provider is None:
                for provider_name, provider in self.rtc_turn_providers.items():
                    config_model = provider.get_config_model()
                    logger.info(f"config_model: {config_model}")
                    try:
                        logger.info(f"turn_provider_config: {turn_provider_config}")
                    except pydantic.ValidationError:
                        continue
                    else:
                        turn_provider_name = provider_name
                        turn_provider = provider
                        break
            if turn_provider is not None:
                logger.info(f"Use {turn_provider_name} as rtc turn provider.")
                turn_entity = turn_provider.prepare_rtc_configuration(turn_provider_config)
        if turn_entity is None:
            logger.info("No valid123 rtc provider configuration found, STUN/TURN will not be valid. "
                        "Communication across networks may not be established.")
        return turn_entity

class RtcConfig(BaseModel):
    urls: list[str]
    username: str
    credential: str