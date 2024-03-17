# GraphFS

Imagine you drop all your files into a single "bucket," and this file store understands:

- How to best store all your files
- The content of the files
- Finds similar and related files
- Establishes data lineage

And much, much more. GraphFS leverages the power of graph and vector databases to accomplish just that.


```
brew install libmagic
uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```


Neo4j Indexes

```
CREATE INDEX FOR (c:Container) ON c.sha256
CREATE INDEX FOR (f:Regular) ON f.name
CREATE INDEX FOR (d:Directory) ON d.name
```