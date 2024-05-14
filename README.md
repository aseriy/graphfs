# GraphFS

Imagine you drop all your files into a single "bucket," and this file store understands:

- How to best store all your files
- The content of the files
- Finds similar and related files
- Establishes data lineage

And much, much more. GraphFS leverages the power of graph and vector databases to accomplish just that.

## Running in Docker Container

Install Docker on your platform.

Create the data directory:

```bash
mkdir ./volumes/graphfs
```

This is where `graphfs` stores data internally, so make sure it has some space.

Create the config file by cloning `etc/config.yml.sample` and then customize based on your situation:

```yaml
environments:
  DEV:
    BINSTORE:
      path: /mnt/data
    NEO4J:
      password: binstore
      username: neo4j
local_url: <ip_addr>
milvus_url: <ip_addr>
graphfs_host: localhost
graphfs_port: 9000

```

Build the GraphFS image from the `Dockerfile`:

```bash
docker build -t graphfs .
```


Run the GraphFS server in a container. The server runs on port `9000`:

```bash
docker run -it --rm --name graphfssrv -p 127.0.0.1:9000:9000 -v ./volumes/graphfs:/mnt/data graphfs
```

## Dev Environment Setup

Python 3.12.3

On Windows, Python executable is not `python.exe` but `py.exe`

pip 24.0

On Windows, see https://www.geeksforgeeks.org/how-to-install-pip-on-windows/


Python Virtual Environment

```bash
python3 -m venv graphfs-env
source graphfs-evn/bin/activate
```


```bash
brew install libmagic
uvicorn main:app --host 0.0.0.0 --port 9000 --reload
```

Build and run as a Docker image:

```bash
docker build -t graphfs .
```

```bash
docker run -it --rm --name graphfssrv -p 127.0.0.1:9000:9000 graphfs
```



Neo4j Indexes

```
CREATE INDEX FOR (fn:FileNode) ON fn.sha256
CREATE INDEX FOR (fn:FileNode) ON fn.size
CREATE INDEX FOR (fn:FileNode) ON fn.mime
CREATE INDEX FOR (c:Container) ON c.sha256
CREATE INDEX FOR (c:Container) ON c.size
CREATE INDEX FOR (f:Regular) ON f.name
CREATE INDEX FOR (d:Directory) ON d.name
```



Useful Cypher Statements

Percentage of Containers similar to other Container:

```
MATCH (c:Container) WITH COUNT(c) AS total MATCH (c1:Container)-[r:SIMILAR_TO]->(c2:Container) WITH COUNT(r) AS similar, total RETURN similar, total, round(toFloat(similar)/toFloat(total), 2) AS similar_percent
```

Reverse SIMILAR_TO relationship

```
MATCH (c1:Container {sha256:"3121dde47289a0b742e4f3e0e28d95e6cc417cc5ff929cea2483447264c68c37"})-[r:SIMILAR_TO]->(c2:Container {sha256:"7c45a86584f192733f2dd8f7c99f3c9d9e127f2643ef71c0ea687ef38d9a63fe"})
MERGE (c2)-[rp:SIMILAR_TO]->(c1) SET rp.delta=r.delta, rp.ctime=r.ctime DELETE r
```

Find all SIMILAR_TO chains

```
MATCH (c1:Container)-[:SIMILAR_TO *]->(c2:Container) RETURN c1,c2
```

List file with the specified MIME type

```sql
MATCH (f:Regular)-[:REFERENCES]-(fn:FileNode {mime:"text/x-Algol68"}) WITH f MATCH p=shortestPath((r:Root)-[:HARD_LINK*]-(f:Regular)) RETURN [n in nodes(p) | n.name] AS path ORDER BY path
```

List the number of file of each MIME type:

```sql
MATCH (fn:FileNode) WITH DISTINCT fn.mime AS mime
UNWIND mime AS m
MATCH (fn:FileNode {mime: m})
RETURN m AS mime, COUNT(fn) AS count ORDER BY count DESC
```

Similarity Progress Stats

```sql
MATCH (c:Container) WITH COUNT(c) AS Total
MATCH (c:Container) WHERE c.simsearch IS NOT NULL OR (c)-[:SIMILAR_TO]->(:Container) WITH Total, COUNT(c) AS SimSearched
MATCH (c:Container)-[:SIMILAR_TO]-(:Container) WITH Total, SimSearched, COUNT(DISTINCT c) AS Similar
RETURN Total, SimSearched, round(100.0*SimSearched/Total,2) AS Progress, Similar, round(100.0*Similar/Total,2) AS Similarity
```

Find Files that share Containers with the given File:

```sql
MATCH (f:Regular)-[:REFERENCES]->(fn:FileNode)-[s:STORED_IN]->(c:Container) WHERE elementId(f)="4:e7e7f16b-f67f-4cbe-900f-1aec09af7472:1352649" RETURN fn.sha256, COUNT(c)
```

```sql
MATCH (fn:FileNode {sha256:"b8c56bbfe8ac994db94f5702b48beb9ca64f9d003785388f5dd23fc05d81c932"})-[s:STORED_IN]->(c:Container) WHERE s.idx IN range(0,255) WITH fn, c AS containers, s.idx AS i ORDER BY s.idx UNWIND containers AS c MATCH (c)<-[:STORED_IN]-(t:FileNode) WHERE fn<>t WITH i, c, COUNT(t) AS t WHERE t > 1 RETURN i, c.sha256, t
```


List N FileNodes that haven't been searched for similarity yet:

```sql
MATCH (fn:FileNode) WHERE fn.simsearch IS NULL AND NOT (fn)-[:SIMILAR_TO]-(:FileNode) WITH fn AS fnlist LIMIT 10
UNWIND fnlist AS fn
RETURN fn
```


Determine if all Containers of a given FileNode have been processed for similarity:

```sql
MATCH (fn:FileNode {sha256:"b8c56bbfe8ac994db94f5702b48beb9ca64f9d003785388f5dd23fc05d81c932"})-[:STORED_IN]->(c:Container) WITH fn, COUNT(c) AS total MATCH (fn)-[:STORED_IN]-(c:Container) WHERE c.simsearch IS NOT NULL OR (c)-[:SIMILAR_TO]-(:Container) RETURN fn.sha256, total, COUNT(c) AS processed
```

Example:

```bash
╒══════════════════════════════════════════════════════════════════╤═════╤═════════╕
│fn.sha256                                                         │total│processed│
╞══════════════════════════════════════════════════════════════════╪═════╪═════════╡
│"b8c56bbfe8ac994db94f5702b48beb9ca64f9d003785388f5dd23fc05d81c932"│6076 │1948     │
└──────────────────────────────────────────────────────────────────┴─────┴─────────┘
```

Select the first {n} FileNodes that haven't been searched for similarity yet but have all its Containers searched for similarity:

```sql
MATCH (fn:FileNode) WHERE fn.simsearch IS NULL AND NOT (fn)-[:SIMILAR_TO]-(:FileNode) WITH fn AS fnlist
UNWIND fnlist AS fn
MATCH (fn)-[:STORED_IN]->(c:Container) WHERE c.size=1024 WITH fn, COUNT(c) AS total
MATCH (fn)-[:STORED_IN]-(c:Container) WHERE c.simsearch IS NOT NULL OR (c)-[:SIMILAR_TO]-(:Container)
WITH fn, total, COUNT(c) AS processed WHERE total=processed
RETURN fn.sha256 AS sha256, total, processed LIMIT {n}
```




Recommended Neo4j memory config:

```
neo4j-admin server memory-recommendation
```

```
server.memory.heap.initial_size=3g
server.memory.heap.max_size=3g
server.memory.pagecache.size=1g
```


## Demo Data

```
pip3 install yt-dlp
```

Check the downloadable file formats:

```bash
yt-dlp -F https://youtu.be/iM3kjbbKHQU?si=eyd-etzPFMe2uCkA
```

Download

```bash
yt-dlp -f 399  https://youtu.be/iM3kjbbKHQU?si=eyd-etzPFMe2uCkA
```

Split the downloaded MP4 into frames (images). See https://youtu.be/GrLQQVL4aKE?si=aPa3b8H4S2NrAsTV

```bash
ffmpeg -i Modern\ Graphical\ User\ Interfaces\ in\ Python\ \[iM3kjbbKHQU\].mp4 -filter:v fps=1 frames/%06d.png
```

The  `-filter:v fps=1` defines how many frames per second to capture.


Convert PNG's to BMP's:

```python
from PIL import Image
import os
for png in os.listdir('.'):
  bmp = f"{png.split('.')[0]}.bmp"
  Image.open(png).save(bmp)
```



## Replace archive files with their extracted content

```bash
for f in *.gz; do (mkdir tmp && cd tmp && tar xvfz ../$f && cd .. && rm $f &&mv tmp $f); done
```

```bash
for f in *.zip; do (mkdir tmp && cd tmp && unzip ../$f && cd .. && rm $f &&mv tmp $f); done
```

```bash
find . -maxdepth 2 -type f -name "accumulo-*.tar.gz" | xargs dirname | sort -u
```


## Hydrate with commits from a Git repo

```
nohup python3 -u flatten-git-repo.py -d ../demo-data -r https://github.com/hub4j/github-api -m 1000 > /mnt/volumes/graphfs/log/flatten-git-repo.log 2>&1 &
```

from `~/git/graphfs/demo` directory.


Containerize:

```
nohup python3 -u binstore/src/graphfs/containerizer.py > /mnt/volumes/graphfs/containerizer.log 2>&1
```

Scrub:

```

```
