#!/bin/bash

for file in video*
do
    mv $file `(echo $file | awk -F 'video_' '{print $2}' | awk -F '_keypoints' '{print $1 $2}' | sed 's/0*\([0-9]*.json$\)/\1/g')`
done
