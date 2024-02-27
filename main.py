from utils import load_app_config
from add_kermode_intro import update_mark_kermode_reviews_intros
from add_tcm import update_turner_classic_movies_extras
from imdb_chart import update_imdb_chart_collections
from imdb_list import update_imdb_list_collections
from kermode_list import update_mark_kermode_reviews_collection
from letterboxd_list import update_letterboxd_list_collections
from tspdt_list import update_top_1000_movies_collection

app_config = load_app_config()
do_kermode_intros = app_config["do_kermode_intros"]
do_kermode_lists = app_config["do_kermode_lists"]
do_turner_classic_movie_extras = app_config["do_turner_classic_movie_extras"]
do_top_1000_movies_list = app_config["do_top_1000_movies_list"]
do_imdb_charts = app_config["do_imdb_charts"]
do_imdb_lists = app_config["do_imdb_lists"]
do_letterboxd_lists = app_config["do_letterboxd_lists"]

if do_kermode_intros:
    update_mark_kermode_reviews_intros(app_config)

if do_kermode_lists:
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