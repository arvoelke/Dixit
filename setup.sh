#!/bin/bash

set -uex

base_dir=$(realpath "$(dirname "${BASH_SOURCE[0]}")")

cd "${base_dir}"
pip3 install -r requirements.txt

cards_dir="${base_dir}/static/cards/dixit"
tmp_dir=$(mktemp -d)
git clone https://github.com/jminuscula/dixit-online.git "${tmp_dir}"
cp "${tmp_dir}/cards/"*.jpg "$cards_dir/"
rm -rf $tmp_dir
