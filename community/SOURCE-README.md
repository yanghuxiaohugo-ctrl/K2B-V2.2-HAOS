# Source and license material

The image is a community test build, not an official Home Assistant OS release.

`source-build-snapshot.tar.gz` contains the effective HAOS and Buildroot source checkout, board overlays, patches, build scripts, and this community build repository. Build outputs, Git databases and generated signing keys are excluded.

`licenses-package-sources.tar.gz` contains the complete output of Buildroot `make legal-info`, including its manifests, collected source archives and license notices. Consult its README and warnings for packages Buildroot cannot collect automatically; the collection is not a claim that every external prebuilt container or Debian package has been recompiled here. HAOS-ACE's original container recipes, image references and installer scripts remain in the source snapshot. Upstream component repositories and notices remain authoritative for those components.

Exact top-level source commits and the build URL are recorded in BUILD-INFO.json. The public repository records the workflow and board patches. Retain all original copyright and license notices when reusing individual components; this project does not relicense third-party code under a blanket new license.

If a source archive exceeds the release asset size limit it is split into `.part000`, `.part001`, etc. Verify every part with SHA256SUMS.txt, then concatenate them in numeric order to recover the original `.tar.gz`, for example:

    cat licenses-package-sources.tar.gz.part* > licenses-package-sources.tar.gz
    tar -tzf licenses-package-sources.tar.gz

Rebuilding: use the checked-in community workflow and its pinned dependencies. A manual run with mode `validate` runs native migration tests plus kernel/DTB/object validation. Mode `full` also builds the image, checks the effective U-Boot configuration and both Ethernet aliases, collects source/license material and creates a GitHub prerelease. Build-time generated signing keys are deliberately not published, so this is not a shared OTA trust chain. Embedded container content and network downloads retain the reproducibility limits of the pinned upstream build.
