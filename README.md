# NHLFantasyAnalysis

This repository contains Jupyter notebooks and Python files I've created to analyse NHL data to make decisions in a head to head categories fantasy hockey league.

The notebooks can be found in analysis_notebooks and the python files are in base_python_files. The schedules for the hockey league are found in the schedules folder. There is also a side_projects folder which contains other fun experiments that I've been working on.

The API knowledge and access came from a combination of experimentation and using the following sources:
* https://stmorse.github.io/journal/espn-fantasy-v3.html (blog post, interesting but out of date)
* https://github.com/cwendt94/espn-api/blob/master/espn_api/hockey/league.py
* https://github.com/cwendt94/espn-api/discussions/150

One of the core difficulties is that ESPN changed their API many times over the past decade so there's lots of misinformation on it.

For use in other fantasy leagues you'll need to change:
* schedule files (use this_weeks_games.csv as an example).
* credentials file - see example_credentials.py and create a credentials.py file in that folder.

Note that most notebooks require a league on ESPN.

If any python packages are missing, use %pip install {package}. E.g. for tqdm, %pip install tqdm. Future releases will include a requirements file, but it's very minimal.