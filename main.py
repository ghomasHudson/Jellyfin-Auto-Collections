from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from utils import load_app_config

from add_kermode_intro import update_mark_kermode_reviews_intros
from add_tcm import update_turner_classic_movies_extras
from imdb_chart import update_imdb_chart_collections
from imdb_list import update_imdb_list_collections
from kermode_list import update_mark_kermode_reviews_collection
from letterboxd_list import update_letterboxd_list_collections
from tspdt_list import update_top_1000_movies_collection

def execute_collection_scripts(app_config: dict = None):
    do_kermode_intros = app_config["do_kermode_intros"]
    do_kermode_list = app_config["do_kermode_list"]
    do_turner_classic_movie_extras = app_config["do_turner_classic_movie_extras"]
    do_top_1000_movies_list = app_config["do_top_1000_movies_list"]
    do_imdb_charts = app_config["do_imdb_charts"]
    do_imdb_lists = app_config["do_imdb_lists"]
    do_letterboxd_lists = app_config["do_letterboxd_lists"]

    all_disabled = not (do_kermode_intros or do_kermode_list or do_turner_classic_movie_extras or do_top_1000_movies_list or do_imdb_charts or do_imdb_lists or do_letterboxd_lists)
    if all_disabled:
        print("All tasks are disabled. Enable at least one with environment settings. Please ensure config.yaml is populated as needed.")
        print()

    if do_kermode_intros:
        update_mark_kermode_reviews_intros(app_config)

    if do_kermode_list:
        update_mark_kermode_reviews_collection(app_config)

    if do_turner_classic_movie_extras:
        update_turner_classic_movies_extras(app_config)

    if do_top_1000_movies_list:
        update_top_1000_movies_collection(app_config)

    if do_imdb_charts:
        update_imdb_chart_collections(app_config)

    if do_imdb_lists:
        update_imdb_list_collections(app_config)

    if do_letterboxd_lists:
        update_letterboxd_list_collections(app_config)
        
if __name__ == "__main__":
    app_config = load_app_config()
    scheduling_enabled = app_config["scheduling_enabled"]
    scheduling_crontab = app_config["scheduling_crontab"]
    scheduling_timezone = app_config["scheduling_timezone"]
    run_scheduled_task_immediately = app_config["run_scheduled_task_immediately"]
    
    if scheduling_enabled:
        if run_scheduled_task_immediately:
            execute_collection_scripts(app_config)
    
        scheduler = BlockingScheduler()
    
        scheduler.add_job(func=execute_collection_scripts, trigger=CronTrigger.from_crontab(scheduling_crontab), timezone=scheduling_timezone, args=[app_config])
    else:
        execute_collection_scripts(app_config)
        exit()