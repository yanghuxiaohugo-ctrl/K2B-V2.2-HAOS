#!/bin/sh
# Called only by hassos-overlay during boot, BEFORE the config bind mount.
# Never rewrite a mounted/live board's config with this helper.
# Missing files are initialized by the existing hassos-overlay code afterwards.
if [ "$#" -ne 2 ]; then
    printf '%s\n' 'usage: k2b-timesync-defaults PERSISTENT_CONFIG IMAGE_DEFAULT' >&2
    exit 2
fi

config=$1
defaults=$2
legacy_sha=67be8c7b9f10d4ef26fa84c480a828808ea68647241a635b931aa7b518099ad0
backup="${config}.pre-k2b-ntp-v1"
keep="${config}.k2b-keep"

note() {
    printf 'k2b-timesync-defaults: %s\n' "$*" >&2
}

file_sha() {
    value=$(sha256sum "$1" 2>/dev/null) || return 1
    printf '%s\n' "${value%% *}"
}

# Symlinks and opt-outs are deliberately preserved, including their targets.
if [ -L "$config" ] || [ -e "$keep" ]; then
    note 'preserving explicit configuration/opt-out'
    exit 0
fi
[ -f "$config" ] || exit 0
current=$(file_sha "$config") || {
    note 'cannot verify persistent file; preserving it'
    exit 0
}
[ "$current" = "$legacy_sha" ] || exit 0

if [ ! -s "$defaults" ]; then
    note 'image default missing or empty; preserving legacy file'
    exit 0
fi

# Never overwrite an existing backup or follow a backup symlink.
if [ -L "$backup" ]; then
    note 'backup is a symlink; preserving configuration'
    exit 0
elif [ -e "$backup" ]; then
    saved=$(file_sha "$backup") || saved=
    if [ "$saved" != "$legacy_sha" ]; then
        note 'existing backup differs; preserving configuration'
        exit 0
    fi
elif ! cp -p "$config" "$backup"; then
    note 'backup failed; preserving configuration'
    exit 0
fi

temp=$(mktemp "${config}.k2b-ntp.XXXXXX") || {
    note 'cannot stage replacement; preserving configuration'
    exit 0
}
trap 'rm -f "$temp"' 0
trap 'exit 1' HUP INT TERM
if cp -p "$defaults" "$temp" && mv "$temp" "$config"; then
    note 'migrated byte-identical legacy default; backup retained'
else
    note 'replacement failed; inspect persistent file and retained backup'
fi
# A migration failure must not stop the rest of overlay initialization.
exit 0
