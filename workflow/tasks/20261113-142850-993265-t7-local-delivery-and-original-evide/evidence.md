# T7 verification evidence

Base commit: 4fdc77a2817c860630cadd15065f6cc7d98bc8c8.

- Built precommit ZIP via scripts/package_delivery.py --working-tree: 166 files; explicit dirty snapshot, not a committed release.
- Verified manifest/member sizes and SHA256; exclusion examples rejected; existing ZIP overwrite rejected; altered README payload rejected.
- Extracted ZIP to .smoke/delivery/precommit-extracted; ran documented node scripts/start.mjs command on an available local port with clean dependencies/data.
- Real HTTP: health ready; index200; linked JS assets200; Alice12 and Bob4 initial certificates; Bob requesting East detail404.
- Stopped launcher and verified port closed. Startup log retained at ignored .smoke/delivery/precommit-startup.log.
- Existing application tests/browser/performance evidence referenced by docs/acceptance.md. No application source/lock/runtime changes in T7.
- Original AI full export remains pending; docs/ai-evidence.md records observed source and missing coverage. No raw logs copied or fabricated.
- Final clean-commit ZIP will be built and smoke-tested after local commit; final checksum supplied alongside archive. No remote action.

Review fix: removed remaining pending-confirmation wording; verifier now requires adjacent SHA256 match. Confirmed mismatched sidecar rejected and restored sidecar accepted; altered ZIP member rejected independently; Windows/POSIX unsafe paths and docs links checked.
