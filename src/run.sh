#!/bin/bash
# shellcheck disable=SC2002

trap ctrl_c INT
function ctrl_c() {
	rm todo.html 2> /dev/null
	rm result.xml 2> /dev/null
}

if [ ! -d input ] ; then
  mkdir input
  read -p "[ERROR] input folder is empty. Press enter to exit"
  exit 1
fi

if [ ! -f input/todo.html ] ; then
  read -p "[ERROR] input folder is empty. Press enter to exit"
  exit 1
fi

if [ ! -d output ]; then
  mkdir output
fi

rm output/* 2> /dev/null

cat input/todo.html | tr -d '\n' | grep -o ">todo</H3>.*" | cut -c 11- > todo.html
python3 src/parser.py
mv result.xml output

rm todo.html 2> /dev/null
