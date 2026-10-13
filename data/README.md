# Where the NASA files go

Do **not** commit the `.txt` files to GitHub (they are already gitignored under `data/raw/`). Put them on a Unity Catalog Volume.

## On your laptop (optional copy)

```
data/raw/
  train/train_FD001.txt
  test/test_FD001.txt
  rul/RUL_FD001.txt
```

Later add `*_FD002.txt`, `*_FD003.txt`, `*_FD004.txt` in the same three folders.

Also keep `readme.txt` and `Damage Propagation Modeling.pdf` next to the original download for your own reading. They are not ingested.

## On Databricks (required)

Volume path (dev): `/Volumes/pm_dev/cmapss/landing/`

```
/Volumes/pm_dev/cmapss/landing/train/train_FD001.txt
/Volumes/pm_dev/cmapss/landing/test/test_FD001.txt
/Volumes/pm_dev/cmapss/landing/rul/RUL_FD001.txt
```

Upload with the Catalog Explorer UI, or from a Databricks notebook:

```python
dbutils.fs.cp("file:/path/on/dbfs/train_FD001.txt",
              "/Volumes/pm_dev/cmapss/landing/train/train_FD001.txt")
```

If you cannot create catalog `pm_dev`, change `catalog` in `databricks.yml` to a catalog you already have, and upload under that catalog’s Volume instead.
