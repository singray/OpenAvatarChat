import sys

import gradio
import uvicorn
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from loguru import logger
from engine_utils.directory_info import DirectoryInfo
from service.service_utils.logger_utils import config_loggers
from service.service_utils.service_config_loader import load_configs
from service.service_utils.ssl_helpers import create_ssl_context

project_dir = DirectoryInfo.get_project_dir()
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)


import argparse
import os

import gradio as gr

from chat_engine.chat_engine import ChatEngine


def parse_args():
    """
    解析命令行参数
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, help="service host address")
    parser.add_argument("--port", type=int, help="service host port")
    parser.add_argument("--config", type=str, default="config/glut.yaml", help="config file to use")
    parser.add_argument("--env", type=str, default="default", help="environment to use in config file")
    return parser.parse_args()


def setup_demo():
    """
    设置演示应用，创建 FastAPI 应用和 Gradio 界面
    """
    app = FastAPI()

    @app.get("/")
    def get_root():
        return RedirectResponse(url="/ui")

    @app.get("/ui/static/fonts/system-ui/system-ui-Regular.woff2")
    @app.get("/ui/static/fonts/ui-sans-serif/ui-sans-serif-Regular.woff2")
    @app.get("/favicon.ico")
    def get_font():
        # remove confusing error
        return {}

    css = """


    .app {
        @media screen and (max-width: 768px) {
            padding: 8px !important;
        }
    }
    footer {
        display: none !important;
    }
    """

    # 创建 Gradio 界面 用于前端的音视频输入
    with gr.Blocks(css=css) as gradio_block:
        with gr.Column():
            with gr.Group() as rtc_container:
                pass
    gradio.mount_gradio_app(app, gradio_block, "/ui")
    return app, gradio_block, rtc_container

def main():
    """
    主函数，程序入口点
    """
    # 解析命令行参数
    args = parse_args()
    # 加载配置文件，获取日志配置、服务配置和引擎配置
    logger_config, service_config, engine_config = load_configs(args)
    
    logger.info(f"service_config: {service_config}")
    logger.info(f"engine_config: {engine_config}")

    # 设置modelscope的默认下载地址
    # 设置模型缓存路径
    if not os.path.isabs(engine_config.model_root):
        os.environ['MODELSCOPE_CACHE'] = os.path.join(DirectoryInfo.get_project_dir(),
                                                      engine_config.model_root.replace('models', ''))

    config_loggers(logger_config)
    # 创建聊天引擎
    chat_engine = ChatEngine()
    # 设置演示应用，获取 FastAPI 应用、Gradio 界面和 RTC 容器
    demo_app, ui, parent_block = setup_demo()
    # 初始化聊天引擎，传入配置和应用信息
    chat_engine.initialize(engine_config, app=demo_app, ui=ui, parent_block=parent_block)

    ssl_context = create_ssl_context(args, service_config)
    # 启动 FastAPI 服务
    uvicorn.run(demo_app, host=service_config.host, port=service_config.port, **ssl_context)


if __name__ == "__main__":
    main()