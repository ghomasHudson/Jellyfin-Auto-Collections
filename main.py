from typing import cast
from utils.jellyfin import JellyfinClient
import pluginlib
from loguru import logger
from pyaml_env import parse_config

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

import argparse
parser = argparse.ArgumentParser(description='Jellyfin List Scraper')
parser.add_argument('--config', type=str, help='Path to config file', default='config.yaml')
args = parser.parse_args()

# Load config
config = parse_config(args.config, default_value=None)

def main(config):
    # Setup jellyfin connection
    jf_client = JellyfinClient(
        server_url=config['jellyfin']['server_url'],
        api_key=config['jellyfin']['api_key'],
        user_id=config['jellyfin']['user_id']
    )

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
                collection_id = jf_client.find_collection_with_name_or_create(list_info['name'], list_id, list_info.get("description", None), plugin_name)

                if config["plugins"][plugin_name].get("clear_collection", False):
                    # Optionally clear everything from the collection first
                    jf_client.clear_collection(collection_id)

                # Add items to the collection
                for item in list_info['items']:
                    jf_client.add_item_to_collection(collection_id, item, year_filter=config["plugins"][plugin_name].get("year_filter", True))


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
