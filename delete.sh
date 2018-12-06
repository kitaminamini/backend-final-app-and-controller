#!/bin/bash

PARTS="rabbitmq minio mongo converter job_dispatcher packer web_app web_controller"

for PART in $PARTS; do
	for DEPLOY in $(find ./$PART/*deployments.yaml 2> /dev/null); do
		kubectl delete -f $DEPLOY
	done
	for SVC in $(find ./$PART/*service.yaml 2> /dev/null); do
		kubectl delete -f $SVC
	done
done
