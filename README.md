# Jellyfin-Collections
Automatically make jellyfin collections based on internet lists.

## How to use
First, copy `config.ini.EXAMPLE` to `config.ini` and change the values for your specific jellyfin instance.

Then run the python files for each type of collection:

- `imdb_list.py` makes collections based on [IMDb](www.imdb.com) lists.
- `letterboxd_list.py` makes collections based on [Letterboxd lists]([www.imdb.com](https://letterboxd.com/lists/)).
- `tspdt_list.py` makes collections based on the [They shoot pictures greatest films starting list](https://www.theyshootpictures.com/gf1000_startinglist_table.php)

There are also experimental scripts to add the [BFI 'Mark Kermode Introduces'](https://www.youtube.com/watch?v=2duv-rLkt0U&list=PLXvkgGofjDzhx-h7eexfVbH3WslWrBXE9) videos to your library and collections:
- `add_kermode_intro.py` adds matching intros to your movies as `extras`. This requires the script to have access to your movies library and `youtube-dl` installed.
- `kermode_list.py` after running the previous script, this adds any movies with a Kermode intro into a collection.
