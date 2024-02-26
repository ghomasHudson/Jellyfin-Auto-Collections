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

## How to use

First, copy `example.env` to `.env` and change the values for your specific jellyfin instance.

Second, copy `example.config.yaml` to `config.yaml` and customize the ids of the imdb and letterbox lists that will be used.

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
