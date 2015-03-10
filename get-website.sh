#!/bin/zsh

if test -d website
then
	echo "Directory 'website' already exists..."
	exit 1
else
	git clone TODO
fi
