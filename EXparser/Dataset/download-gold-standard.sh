#! /bin/env bash

git clone --depth 1 https://github.com/exciteproject/Exparser.git tmp
cp -a ./tmp/EXparser/Dataset/* .
rm -rf ./tmp