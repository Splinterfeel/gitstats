# Django tool for parsing Git repository stats into Postgres DB

## Load stats from ZIP
1. Place repository ZIP file into project folder
2. Run `py manage.py generate_stats --file filename.zip`

Note:  ZIP file must contain `.git` folder

## Load stats from GitLab integration
(TODO)

## Examples of metrics you can build (i.e. using Apache Superset):
* Commit count by date
* Average commit size by author
* Cumulative code base size
* Changes by author per date
* Additions VS Deletions

![metric example](https://github.com/Splinterfeel/gitstats/blob/main/staticfiles/metric_example_1.jpg?raw=true)
![metric example](https://github.com/Splinterfeel/gitstats/blob/main/staticfiles/metric_example_2.jpg?raw=true)
