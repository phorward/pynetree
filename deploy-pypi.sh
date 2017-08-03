#!/bin/sh
pandoc -t rst README.md | sed '3,6d' >README.rst
if [ $? -ne 0 ]
then
	exit 1
fi

echo "--- README.rst ---"
cat README.rst

echo "------------------"
echo -n "Type 'YES' to continue..."
read Y

if [ "$Y" != "YES" ]
then
	echo "Aborted."
	exit 1
fi


python2 setup.py sdist upload -r pypi
rm -f README.rst

echo "All done :)"

