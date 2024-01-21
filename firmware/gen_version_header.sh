#!/bin/sh
echo "generating version.c"
echo "const char GIT_COMMIT_HASH[] = \"`git log --pretty=format:'%h' -n 1``git diff --quiet --exit-code || echo +`\";" > version.c
echo "const char COMPILE_DATE[] =  \"`date`\";" >> version.c
