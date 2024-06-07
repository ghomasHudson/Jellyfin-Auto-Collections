from typing import cast
from utils.jellyfin import JellyfinClient
import pluginlib
import yaml
from loguru import logger

# Load config
config = yaml.safe_load(open("config.yaml"))

# Setup jellyfin connection
jf_client = JellyfinClient(
    server_url=config['jellyfin']['server_url'],
    api_key=config['jellyfin']['api_key'],
    user_id=config['jellyfin']['user_id']
)

# Load plugins
loader = pluginlib.PluginLoader(modules=['plugins'])
plugins = loader.plugins['list_scraper']

# Update jellyfin with lists
for plugin_name in config['plugins']:
    if config['plugins'][plugin_name]["enabled"] and plugin_name in plugins:
        for list_id in config['plugins'][plugin_name]["list_ids"]:
            list_info = plugins[plugin_name].get_list(list_id)
            logger.info(f"")
            logger.info(f"")
            collection_id = jf_client.find_collection_with_name_or_create(list_info['name'])

            if config["plugins"][plugin_name].get("clear_collection", False):
                jf_client.clear_collection(collection_id)

            for item in list_info['items']:
                jf_client.add_item_to_collection(collection_id, item)
