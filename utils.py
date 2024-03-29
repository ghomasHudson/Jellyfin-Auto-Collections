'''Handy utility functions for other scripts'''
import requests

def get_all_collections(server_url, user_id, headers=None):
    '''Find list of all collections'''
    params = {
        "enableTotalRecordCount": "false",
        "enableImages": "false",
        "Recursive": "true",
        "includeItemTypes": "BoxSet"
    }
    print("Getting collections list...")
    res = requests.get(f'{server_url}/Users/{user_id}/Items',headers=headers, params=params)
    collections = {r["Name"]:r["Id"] for r in res.json()["Items"]}
    return collections

def find_collection_with_name_or_create(server_url, list_name, collections, headers=None):
    '''Find a collection with name `list_name` or create one if
    it doesn't exist'''
    # Try and find the collection with name `list_name`
    collection_id = None
    for collection in collections:
        if list_name == collection:
            print("found", list_name, collections[collection])
            collection_id = collections[collection]
            break

    if collection_id is None:
        # Collection doesn't exist -> Make a new one
        print(f"Creating {list_name}...")
        res2 = request_repeat_post(f'{server_url}/Collections',headers=headers, params={"name": list_name})
        collection_id = res2.json()["Id"]
    return collection_id

def find_movie(server_url, user_id, title, year=None, headers=None):
    params = {
        "searchTerm": title,
        "includeItemTypes": "Movie",
        "Recursive": "true",
        "enableTotalRecordCount": "false",
        "enableImages": "false",
    }
    if year is not None:
        params["years"] = year
    while True:
        try:
            res = requests.get(f'{server_url}/Users/{user_id}/Items',headers=headers, params=params)
            if len(res.json()["Items"]) > 0:
                return res.json()["Items"][0]
            else:
                return None
        except:
            pass

def request_repeat_get(url, headers=None, params=None):
    '''Do a GET request, repeat if err'''
    while True:
        try:
            res = requests.get(url, headers=headers, params=params)
            return res
        except:
            pass

def request_repeat_post(url, headers=None, params=None):
    '''Do a POST request, repeat if err'''
    while True:
        try:
            res = requests.post(url, headers=headers, params=params)
            return res
        except:
            pass

# https://stackoverflow.com/a/65407083
def get_env_variable(name: str, default_value: bool | None = None) -> bool:
    import os
    
    true_ = ('true', '1', 't')  # Add more entries if you want, like: `y`, `yes`, `on`, ...
    false_ = ('false', '0', 'f')  # Add more entries if you want, like: `n`, `no`, `off`, ...
    value: str | None = os.getenv(name, None)
    if value is None:
        if default_value is None:
            raise ValueError(f'Variable `{name}` not set!')
        else:
            value = str(default_value)
    if value.lower() in true_ + false_:
        return value in true_
    return value

def load_env_config():
    '''Load environment variables from .env file'''
    from dotenv import load_dotenv
    load_dotenv()
    
    config_dict = {}
    config_dict["server_url"] = get_env_variable("JELLYFIN_SERVER_URL")
    config_dict["api_key"] = get_env_variable("JELLYFIN_API_KEY")
    config_dict["user_id"] = get_env_variable("JELLYFIN_USER_ID")
    config_dict["movies_dir"] = get_env_variable("JELLYFIN_MOVIES_DIR")
    
    config_dict["disable_tv_year_filter"] = get_env_variable("DISABLE_TV_YEAR_CHECK", default_value=False)
    
    is_scheduling_enabled = get_env_variable("SCHEDULING_ENABLED", default_value=False)
    config_dict["scheduling_enabled"] = is_scheduling_enabled
    config_dict["scheduling_crontab"] = get_env_variable("SCHEDULING_CRONTAB") if is_scheduling_enabled else ""
    config_dict["scheduling_timezone"] = get_env_variable("SCHEDULING_TIMEZONE") if is_scheduling_enabled else ""
    config_dict["run_scheduled_task_immediately"] = get_env_variable("RUN_SCHEDULED_TASK_IMMEDIATELY", default_value=False)
    
    config_dict["do_kermode_intros"] = get_env_variable("DO_KERMODE_INTROS", default_value=False)
    config_dict["do_kermode_list"] = get_env_variable("DO_KERMODE_LIST", default_value=False)
    config_dict["do_turner_classic_movie_extras"] = get_env_variable("DO_TURNER_CLASSIC_MOVIE_EXTRAS", default_value=False)
    config_dict["do_top_1000_movies_list"] = get_env_variable("DO_TOP_1000_MOVIES_LIST", default_value=False)
    config_dict["do_imdb_charts"] = get_env_variable("DO_IMDB_CHARTS", default_value=False)
    config_dict["do_imdb_lists"] = get_env_variable("DO_IMDB_LISTS", default_value=False)
    config_dict["do_letterboxd_lists"] = get_env_variable("DO_LETTERBOXD_LISTS", default_value=False)
    
    running_in_docker = get_env_variable("RUNNING_IN_DOCKER", default_value=False)
    config_dict["running_in_docker"] = running_in_docker
    config_dict["docker_config_dir"] = "/app/config/" if running_in_docker else ""
    
    return config_dict

def get_yaml_variable_list(name: str, config) -> list:
    '''Get a list from a yaml config file, return empty list if not found'''
    try:
        return config[name]
    except KeyError:
        return []

def load_yaml_config(env_config: dict):
    '''Load config from config.yaml'''
    import yaml
    
    config_dir = env_config["docker_config_dir"]
    config_path = f"{config_dir}config.yaml"
    
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    config_dict = {}
    config_dict["imdb_list_ids"] = get_yaml_variable_list("imdb_list_ids", config)
    config_dict["imdb_chart_ids"] = get_yaml_variable_list("imdb_chart_ids", config)
    config_dict["letterboxd_list_ids"] = get_yaml_variable_list("letterboxd_list_ids", config)
    
    return config

def load_app_config():
    '''Load environment and yaml config'''
    env_config = load_env_config()
    yaml_config = load_yaml_config(env_config)
    
    app_config = {**env_config, **yaml_config}
    
    return app_config