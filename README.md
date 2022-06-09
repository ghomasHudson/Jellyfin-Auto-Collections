# Jellyfin Auto Collections
A collection of scripts to automatically make and update jellyfin collections based on internet lists such as IMDb and letterboxd.
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

## How to use
First, copy `config.ini.EXAMPLE` to `config.ini` and change the values for your specific jellyfin instance. You can also customize the ids of the imdb and letterbox lists that will be used.

Install the requirements with `pip install -r requirements.txt`.

Then run the python files for each type of collection:

- `imdb_list.py` makes collections based on [IMDb](www.imdb.com) lists.
- `letterboxd_list.py` makes collections based on [Letterboxd lists](https://letterboxd.com/lists/).
- `tspdt_list.py` makes collections based on the [They shoot pictures greatest films starting list](https://www.theyshootpictures.com/gf1000_startinglist_table.php).

Running these scripts will make a collection on your jellyfin server with any matched movies. You can then customise the description/images to your liking. Running the scripts again will add new movies to this existing collection.

There are also experimental scripts to add the [BFI 'Mark Kermode Introduces'](https://www.youtube.com/watch?v=2duv-rLkt0U&list=PLXvkgGofjDzhx-h7eexfVbH3WslWrBXE9) videos to your library and collections:
- `add_kermode_intro.py` downloads matching Mark Kermode intros to your movies as `extras`. This requires the script to have access to your movies library and `youtube-dl` installed.
- `kermode_list.py` after running the previous script, this adds any movies with a Kermode intro into a collection.
