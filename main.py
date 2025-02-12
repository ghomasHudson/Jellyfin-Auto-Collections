from typing import cast
from utils.jellyfin import JellyfinClient
from utils.jellyseerr import JellyseerrClient
import pluginlib
from loguru import logger
from pyaml_env import parse_config
import os
import sys

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

import argparse
parser = argparse.ArgumentParser(description='Jellyfin List Scraper')
parser.add_argument('--config', type=str, help='Path to config file', default='config.yaml')
args = parser.parse_args()

# Set logging level
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
# Configure Loguru logger
logger.remove()  # Remove default configuration
logger.add(sys.stderr, level=log_level)

# Load config
if not os.path.exists(args.config):
    logger.error(f"{args.config} does not exist.")
    logger.error(f"Copy config.yaml.example to {args.config} and add your jellyfin config.")
    raise Exception("No config file found.")
config = parse_config(args.config, default_value=None)

def main(config):
    # Setup jellyfin connection
    jf_client = JellyfinClient(
        server_url=config['jellyfin']['server_url'],
        api_key=config['jellyfin']['api_key'],
        user_id=config['jellyfin']['user_id']
    )

    if "jellyseerr" in config:
        js_client = JellyseerrClient(
            server_url=config['jellyseerr']['server_url'],
            api_key=config['jellyseerr'].get('api_key', None),
            email=config['jellyseerr'].get('email', None),
            password=str(config['jellyseerr'].get('password', None)),
            user_type=str(config['jellyseerr'].get('user_type', "local"))
        )
    else:
        js_client = None

    # Load plugins
    loader = pluginlib.PluginLoader(modules=['plugins'])
    plugins = loader.plugins['list_scraper']

    # If Jellyfin_api plugin is enabled - pass the jellyfin creds to it
    if "jellyfin_api" in config["plugins"] and config["plugins"]["jellyfin_api"].get("enabled", False):
        config["plugins"]["jellyfin_api"]["server_url"] = config["jellyfin"]["server_url"]
        config["plugins"]["jellyfin_api"]["user_id"] = config["jellyfin"]["user_id"]
        config["plugins"]["jellyfin_api"]["api_key"] = config["jellyfin"]["api_key"]

    # Update jellyfin with lists
    for plugin_name in config['plugins']:
        if config['plugins'][plugin_name]["enabled"] and plugin_name in plugins:
            for list_id in config['plugins'][plugin_name]["list_ids"]:
                logger.info(f"")
                logger.info(f"")
                logger.info(f"Getting list info for plugin: {plugin_name}, list id: {list_id}")

                # Match list items to jellyfin items
                list_info = plugins[plugin_name].get_list(list_id, config['plugins'][plugin_name])

                # Find jellyfin collection or create it
                collection_id = jf_client.find_collection_with_name_or_create(
                    list_info['name'],
                    list_id,
                    list_info.get("description", None),
                    plugin_name
                )

                if config["plugins"][plugin_name].get("clear_collection", False):
                    # Optionally clear everything from the collection first
                    jf_client.clear_collection(collection_id)

                # Add items to the collection
                for item in list_info['items']:
                    matched = jf_client.add_item_to_collection(
                        collection_id,
                        item,
                        year_filter=config["plugins"][plugin_name].get("year_filter", True),
                        jellyfin_query_parameters=config["jellyfin"].get("query_parameters", {})
                    )
                    if not matched and js_client is not None:
                        js_client.make_request(item)



if __name__ == "__main__":
    logger.info("Starting up")
    logger.info("Starting initial run")
    main(config)

    # Setup scheduler
    if "crontab" in config and config["crontab"] != "":
        scheduler = BlockingScheduler()
        scheduler.add_job(main, CronTrigger.from_crontab(config['crontab']), args=[config], timezone=config.get("timezone", "UTC"))
        logger.info("Starting scheduler using crontab: " + config["crontab"])
        scheduler.start()
