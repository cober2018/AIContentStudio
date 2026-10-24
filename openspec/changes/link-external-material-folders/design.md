## Context

Material bytes are content-addressed under `MEDIA_ROOT/material/`. `LocalMaterialStorage` resolves keys only inside its root; creative inputs are APFS clones of library files, with a bounded copy fallback. External drives are often exFAT or a different APFS volume, so clones are impossible and permissions may not be enforceable.

## Decisions

- **Source folder as a record, files linked individually.** The folder gives one place to rescan and one availability status; linking stays per file so each file gets its own rights.
- **Key namespace `external/<source_id>/<relative path>`.** Keeps `material_revision` unchanged apart from metadata; storage resolves the source root and rejects `..`, absolute parts and symlinks that escape the folder.
- **Availability = folder present + same volume identity.** The volume UUID (from `diskutil info`, falling back to device + root inode) stops a different drive mounted at the same path from being trusted.
- **Change detection is cheap first, exact when needed.** Size + mtime on every read; full SHA-256 when either differs and always before an execution output is submitted. Large videos are hashed by streaming.
- **Symlink inputs for external revisions.** Clone across volumes is impossible, and copying is what the user wants to avoid. A link keeps one copy of the bytes. Write protection cannot be guaranteed on exFAT, so integrity rests on the fingerprint checks, and a mismatch blocks the execution with `execution_input_hash_changed`.
- **Volume identity from the mount point.** `diskutil info` answers only for mount points, so the folder's mount point is found by walking up while the device stays the same.
- **No automatic relink.** A changed file never updates silently; the user links it again to create a new revision.

## Risks

- Unplugging the drive mid-render breaks the executor run; the execution reports a blocker, as for any missing input.
- Hashing large files at link time takes seconds per GB; it runs once per file and version.
- Testing uses a mounted disk image (`hdiutil`) to simulate plug and unplug.
