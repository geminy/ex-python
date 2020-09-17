#!/usr/bin/env bash

declare -i time_parsed error_sum
time_parsed=0
error_sum=0

while true
do
	make libQmlFramework -j8 &> make_result
	if [ $? = 0 ]
	then
		echo "make completed successfully."
		break
	fi

	cat make_result | grep -e "error:" | sort | uniq > errors
	error_sum=`wc -l errors | sed -e 's/^\([1-9][0-9]*\).*/\1/'`
	if [ $error_sum -le 10 ]
	then
		echo "error number <= 10: $error_sum"
		break
	fi

	time_parsed=time_parsed+1
	echo "time: $time_parsed"
	python membervars2.py --error
done
