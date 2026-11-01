# Kavita showed only the last volume of a series split across two folders

- **Date:** 2026-11-01
- **Status:** resolved
- **Service:** Kavita
- **Runbook:** none (first occurrence)

## Symptom

"No Matter How I Look at It, It's You Guys' Fault I'm Not Popular!" showed a single card, Volume 26, though all 26 volumes were on disk. Before that it showed v01–v25 without v26. It switched after another manga was added and Kavita rescanned.

## Cause

The series had two folders in `media/manga`, one with v01–v25 and one with v26. Kavita parses the series name from the file names, so both folders gave the same series. A Kavita series has one folder, so each scan bound it to one folder and removed the other folder's volumes. The 02:00 scan on 2026-11-01 logged:

```
Updating No Matter How I Look at It, It's You Guys' Fault I'm Not Popular! FolderPath to /manga/<v26 folder>
Volume cleanup code was trying to remove a volume with a file still existing on disk (usually volume marker removed) File: /manga/<v01–v25 folder>/… v25 (2025).cbz
```

Ruled out:
- **Files missing from Kavita's view:** `docker exec kavita find /manga /lns -ipath '*no matter*' -type f | wc -l` gave 26.
- **ComicInfo overriding the names:** the v26 CBZ has no ComicInfo, and the log shows Kavita parsed every file into its volume.
- **Unparseable names:** every file name has a `v##` token.
- **Unreadable files:** Kavita read all 26 (the log names each volume).
- **Not scanned yet:** a scan ran at 02:00, after the files were added (v26 dated 2026-10-28).
- **Other series split the same way:** no other folder in `media/manga` or `media/lns` parses to the same series as another, and no other folder appears in the "file still existing on disk" log lines.

## Fix

Moved all 26 files (`mv`, same disk) into one folder with the plain series name, `media/manga/No Matter How I Look at It, It's You Guys' Fault I'm Not Popular!`, and removed the two old folders. The old layout is in `~/kavita-nomatter-layout.bak-20261101.txt`. After a library scan, Kavita showed all 26 volumes (user, 2026-11-01). Reading progress for v01–v25 was probably lost when Kavita removed those volumes (unverified).
