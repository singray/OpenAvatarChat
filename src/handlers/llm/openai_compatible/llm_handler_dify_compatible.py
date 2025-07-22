

import os
import re
from typing import Dict, Optional, cast
from loguru import logger
from pydantic import BaseModel, Field
from abc import ABC
from openai import OpenAI
from chat_engine.contexts.handler_context import HandlerContext
from chat_engine.data_models.chat_engine_config_data import ChatEngineConfigModel, HandlerBaseConfigModel
from chat_engine.common.handler_base import HandlerBase, HandlerBaseInfo, HandlerDataInfo, HandlerDetail
from chat_engine.data_models.chat_data.chat_data_model import ChatData
from chat_engine.data_models.chat_data_type import ChatDataType
from chat_engine.contexts.session_context import SessionContext
from chat_engine.data_models.runtime_data.data_bundle import DataBundle, DataBundleDefinition, DataBundleEntry
from handlers.llm.openai_compatible.chat_history_manager import ChatHistory, HistoryMessage
import json
import requests
from engine_utils.media_utils import ImageUtils

class LLMConfig(HandlerBaseConfigModel, BaseModel):
    model_name: str = Field(default="qwen-plus")
    system_prompt: str = Field(default="请你扮演一个 AI 助手，用简短的对话来回答用户的问题，并在对话内容中加入合适的标点符号，不需要加入标点符号相关的内容")
    api_key: str = Field(default=os.getenv("DASHSCOPE_API_KEY"))
    api_url: str = Field(default=None)
    enable_video_input: bool = Field(default=False)
    dify_chat_messages: str = Field(default=None)
    dify_code: str = Field(default=None)
    dify_upload: str = Field(default=None)

class LLMContext(HandlerContext):
    def __init__(self, session_id: str):
        super().__init__(session_id)
        self.config = None
        self.local_session_id = 0
        self.model_name = None
        self.system_prompt = None
        self.api_key = None
        self.api_url = None
        self.client = None
        self.input_texts = ""
        self.output_texts = ""
        self.current_image = None
        self.history = ChatHistory()
        self.enable_video_input = False
        # 这个是dify的会话id字段，保障dify的多轮对话
        self.conversation_id = None
        self.dify_chat_messages = None
        self.dify_code = None
        self.dify_upload = None


class HandlerLLM(HandlerBase, ABC):
    def __init__(self):
        super().__init__()

    def get_handler_info(self) -> HandlerBaseInfo:
        return HandlerBaseInfo(
            config_model=LLMConfig,
        )

    def get_handler_detail(self, session_context: SessionContext,
                           context: HandlerContext) -> HandlerDetail:
        definition = DataBundleDefinition()
        definition.add_entry(DataBundleEntry.create_text_entry("avatar_text"))
        inputs = {
            ChatDataType.HUMAN_TEXT: HandlerDataInfo(
                type=ChatDataType.HUMAN_TEXT,
            ),
            ChatDataType.CAMERA_VIDEO: HandlerDataInfo(
                type=ChatDataType.CAMERA_VIDEO,
            ),
        }
        outputs = {
            ChatDataType.AVATAR_TEXT: HandlerDataInfo(
                type=ChatDataType.AVATAR_TEXT,
                definition=definition,
            )
        }
        return HandlerDetail(
            inputs=inputs, outputs=outputs,
        )

    def load(self, engine_config: ChatEngineConfigModel, handler_config: Optional[BaseModel] = None):
        if isinstance(handler_config, LLMConfig):
            if handler_config.api_key is None or len(handler_config.api_key) == 0:
                error_message = 'api_key is required in config/xxx.yaml, when use handler_llm'
                logger.error(error_message)
                raise ValueError(error_message)

    def create_context(self, session_context, handler_config=None):
        if not isinstance(handler_config, LLMConfig):
            handler_config = LLMConfig()
        context = LLMContext(session_context.session_info.session_id)
        context.model_name = handler_config.model_name
        context.system_prompt = {'role': 'system', 'content': handler_config.system_prompt}
        context.api_key = handler_config.api_key
        context.api_url = handler_config.api_url
        context.enable_video_input = handler_config.enable_video_input
        context.user_id = session_context.session_info.user_id
        context.dify_chat_messages = handler_config.dify_chat_messages
        context.dify_code = handler_config.dify_code
        context.dify_upload = handler_config.dify_upload
        logger.info(f'llm dify_code {context.dify_code}')

        context.client = OpenAI(
            # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
            api_key=context.api_key,
            base_url=context.api_url,
        )
        return context
    
    def start_context(self, session_context, handler_context):
        pass

    def handle(self, context: HandlerContext, inputs: ChatData,
               output_definitions: Dict[ChatDataType, HandlerDataInfo]):
        output_definition = output_definitions.get(ChatDataType.AVATAR_TEXT).definition
        context = cast(LLMContext, context)
        text = None
        if inputs.type == ChatDataType.CAMERA_VIDEO and context.enable_video_input:
            context.current_image = inputs.data.get_main_data()
            return
        elif inputs.type == ChatDataType.HUMAN_TEXT:
            text = inputs.data.get_main_data()
        else:
            return
        speech_id = inputs.data.get_meta("speech_id")
        if (speech_id is None):
            speech_id = context.session_id
        if text is not None:
            context.input_texts += text

        text_end = inputs.data.get_meta("human_text_end", False)
        if not text_end:
            return
        chat_text = context.input_texts
        chat_text = re.sub(r"<\|.*?\|>", "", chat_text)
        if len(chat_text) < 1:
            return

        logger.info(f'llm input {chat_text} ')
        current_content = context.history.generate_next_messages(chat_text,
                                                                 [
                                                                     context.current_image] if context.current_image is not None else [])
        # logger.info(f'llm input {context.model_name} {current_content} ')

        # completion = context.client.chat.completions.create(
        #     model=context.model_name,
        #     messages=[
        #         context.system_prompt,
        #     ] + current_content,
        #     stream=True,
        #     stream_options={"include_usage": True}
        # )

        request_data = {
            "inputs": {},
            "query": chat_text,
            "response_mode": "streaming",
            "conversation_id": context.conversation_id or "",
            "user": context.user_id or "",
            "files": []
        }

        if context.current_image is not None:
            try:
                for image in [context.current_image]:
                    import base64
                    if isinstance(image, bytes):
                        binary_image = image
                    else:
                        base64image = ImageUtils.format_image(image)
                    if isinstance(base64image, str) and base64image.startswith('data:image'):
                        image_data = base64image.split(',')[1]
                        binary_image = base64.b64decode(image_data)

                    files = {
                        'file': ('image.jpg', binary_image, 'image/jpeg')
                    }
                    data = {
                        'user': 'user'
                    }
                    upload_url = context.dify_upload
                    try:
                        upload_response = requests.post(
                            upload_url,
                            headers={
                                'Authorization': f'Bearer {context.dify_code}'
                            },
                            files=files,
                            data=data,
                            timeout=(30, 120)  # Add timeout
                        )

                        if upload_response.status_code in [200, 201]:
                            file_info = upload_response.json()
                            request_data["files"].append({
                                "type": "image",
                                "transfer_method": "local_file",
                                "upload_file_id": file_info['id']
                            })
                            logger.info(f"upload image. Status code: {upload_response.status_code}")
                        else:
                            logger.error(f"Failed to upload image. Status code: {upload_response.status_code}")
                            logger.error(f"Response: {upload_response.text}")
                    except requests.exceptions.RequestException as e:
                        logger.error(f"Error uploading image: {str(e)}")
            except Exception as e:
                logger.error(f"Unexpected error handling image upload: {str(e)}")
                # Continue with text-only request if image upload fails

        logger.info(f"Sending chat message request with data: {json.dumps(request_data, ensure_ascii=False)}")
        try:
            response = requests.post(
                context.dify_chat_messages,
                headers={
                    'Authorization': f'Bearer {context.dify_code}',
                    'Content-Type': 'application/json'
                },
                json=request_data,
                stream=True
            )
            logger.info(f"Chat message response received. Status code: {response.status_code}")
            if response.status_code != 200:
                logger.error(f"Chat message request failed. Response: {response.text}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send chat message: {str(e)}")
            return

        context.current_image = None
        context.input_texts = ''
        context.output_texts = ''

        # for chunk in completion:
        #     if (chunk and chunk.choices and chunk.choices[0] and chunk.choices[0].delta.content):
        #         output_text = chunk.choices[0].delta.content
        #         context.output_texts += output_text
        #         logger.info(output_text)
        #         # 生成输出数据包
        #         output = DataBundle(output_definition)
        #         output.set_main_data(output_text)
        #         output.add_meta("avatar_text_end", False)
        #         output.add_meta("speech_id", speech_id)
        #         yield output

        for line in response.iter_lines():
            if line:
                try:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        line_str = line_str[6:]

                    json_response = json.loads(line_str)

                    if json_response.get('event') == 'message':
                        output_text = json_response.get('answer', '')
                        if output_text:
                            context.output_texts += output_text
                            logger.info(f"Received message: {output_text}")
                            output = DataBundle(output_definition)
                            output.set_main_data(output_text)
                            output.add_meta("avatar_text_end", False)
                            output.add_meta("speech_id", speech_id)
                            yield output
                    elif json_response.get('event') == 'message_end':
                        logger.info("Message stream ended")
                        context.conversation_id = json_response.get('conversation_id')
                        if 'metadata' in json_response:
                            logger.info(f"Message metadata: {json_response['metadata']}")
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    continue

        context.history.add_message(HistoryMessage(role="avatar", content=context.output_texts))
        context.output_texts = ''
        logger.info('avatar text end')

        end_output = DataBundle(output_definition)
        end_output.set_main_data('')
        end_output.add_meta("avatar_text_end", True)
        end_output.add_meta("speech_id", speech_id)
        yield end_output

    def destroy_context(self, context: HandlerContext):
        pass

