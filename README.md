# Jellyfin Auto Collections

A collection of scripts to automatically make and update [jellyfin](jellyfin.org) collections based on internet lists such as IMDb and letterboxd.

```
Getting collections list...

found /r/TrueFilm Canon (1000 films) 015dee24c79dacfa80300afb7577fc37
************************************************

Can't find A Trip to the Moon
Can't find The Birth of a Nation
Can't find Intolerance: Love&#039;s Struggle Throughout the Ages
Can't find A Man There Was
Can't find The Cabinet of Dr. Caligari
Added Big Buck Bunny cc561c8b1d5da3a080cdb61ebe44d1a7
Added Big Buck Bunny 2 0515533b716e8fe76d3b630f9b9b6d51
Can't find Nosferatu
Can't find Dr. Mabuse, the Gambler
Can't find Häxan
Added Big Buck Bunny 3 9a6b8002ef8f12a0611e92f5104d8b8e
Can't find Sherlock, Jr.
Can't find Greed
Can't find The Last Laugh
Can't find Battleship Potemkin
Added Big Buck Bunny 5 98690cc73413b12593988687ee737a27
Can't find Ménilmontant
...
```

![pic-selected-220609-1405-13](https://user-images.githubusercontent.com/13795113/172853971-8b5ab33b-58a9-4073-8a28-c471e9710cdc.png)

## Usage

First, copy `example.env` to `.env` and change the values for your specific jellyfin instance.

Second, copy `example.config.yaml` to `config.yaml` and customize the ids of the imdb and letterbox lists that will be used.

### Running Scripts Individually

Make sure you have Python 3 and pip installed.

Install the requirements with `pip install -r requirements.txt`.

Then run the python files for each type of collection:

- `imdb_list.py` makes collections based on [IMDb](www.imdb.com) lists.
- `imdb_chart.py` makes collections based on [IMDb](www.imdb.com) charts (such as Top 250 Movies, Most Popular Movies, etc).
- `letterboxd_list.py` makes collections based on [Letterboxd lists](https://letterboxd.com/lists/).
- `tspdt_list.py` makes collections based on the [They shoot pictures greatest films starting list](https://www.theyshootpictures.com/gf1000_startinglist_table.php).

Running these scripts will make a collection on your jellyfin server with any matched movies. You can then customise the description/images to your liking. Running the scripts again will add new movies to this existing collection. You probably want to put them in some kind of cron job.

There are also scripts to add the [BFI 'Mark Kermode Introduces'](https://www.youtube.com/watch?v=2duv-rLkt0U&list=PLXvkgGofjDzhx-h7eexfVbH3WslWrBXE9) and [Turner Classic Movies](https://www.youtube.com/@tcmintrosandwrap-ups1994/videos) videos to your library and collections:

- `add_kermode_intro.py` downloads matching Mark Kermode intros to your movies as `extras`. This requires the script to have access to your movies library files and have `youtube-dl` installed.
- `add_tcm_intro.py` downloads matching Turner Classic movies intros and outros to your movies as `extras`. This requires the script to have access to your movies library files and have `youtube-dl` installed.
- `kermode_list.py` after running the previous script (rescan your library first), this adds any movies with a Kermode intro into a collection.

### Docker

The easiest way to get going is to use the provided `docker-compose.yml` configuration. Whatever directory you end up mapping to the config directory needs to contain your updated `config.yaml` file. Your `.env` file should be next to the `docker-compose.yml` file.

Run `docker compose --env-file .env up -d` to get going

The main difference of the Dockerized solution is it enables you to opt into which script gets run and it can be set up to run on an interval so your collections can automatically stay up to date (similar to if you ran the scripts directly on a cronjob). As well as all the other benefits of being able to install these in a container and all that jazz. If scheduling is not enabled when the Docker container runs it will fire off whatever scripts it is configured to run and then exit.

#### Configuration Options

| Environment Variable           | Docker Compose Default | Description                                                                                                  |
| ------------------------------ | ---------------------- | ------------------------------------------------------------------------------------------------------------ |
| CONFIG_DIR                     | N/A                    | Base configuration directory where your container will pull the `config.yaml` from                           |
| JELLYFIN_SERVER_URL            | N/A                    | The URL of your Jellyfin instance                                                                            |
| JELLYFIN_API_KEY               | N/A                    | Generated API Key                                                                                            |
| JELLYFIN_USER_ID               | N/A                    | UserID from the URL of your Profile in Jellyfin                                                              |
| JELLYFIN_MOVIES_DIR            | N/A                    | Filepath to your movies                                                                                      |
| DISABLE_TV_YEAR_CHECK          | false                  | Whether to filter by year when processing IMDB Lists                                                         |
| SCHEDULING_ENABLED             | true                   | Whether scheduling is enabled                                                                                |
| SCHEDULING_CRONTAB             | 0 6 \* \* \*           | The interval the scripts will be run on in crontab syntax. No effect if scheduling is disabled.              |
| SCHEDULING_TIMEZONE            | America/New_York       | Timezone the interval will be run in. No effect is scheduling is disabled                                    |
| RUN_SCHEDULED_TASK_IMMEDIATELY | true                   | Whether to run the scheduled task immediately on Docker container start. No effect is scheduling is disabled |
| DO_KERMODE_INTROS              | false                  | Whether to grab the Mark Kermode movie intros                                                                |
| DO_KERMODE_LIST                | false                  | Whether to update the "Mark Kermode Introduces" collection                                                   |
| DO_TURNER_CLASSIC_MOVIE_EXTRAS | false                  | Whether to grab the Turner Classic Movies movie extras                                                       |
| DO_TOP_1000_MOVIES_LIST        | false                  | Whether to update the "TSPDT Top 1000 Greatest" collection                                                   |
| DO_IMDB_CHARTS                 | false                  | Whether to update the collections defined in the `imdb_list_ids` portion of `config.yaml`                    |
| DO_IMDB_LISTS                  | false                  | Whether to update the collections defined in the `imdb_chart_ids` portion of `config.yaml`                   |
| DO_LETTERBOXD_LISTS            | false                  | Whether to update the collections defined in the `letterboxd_list_ids` portion of `config.yaml`              |
