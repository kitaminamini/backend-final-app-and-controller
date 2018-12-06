#!/bin/bash

PARTS="rabbitmq minio mongo converter job_dispatcher packer web_app web_controller"

docker build -t k8s-p2-converter:v1 ./converter
docker build -t k8s-p2-job-dispatcher:v1 ./job_dispatcher
docker build -t k8s-p2-packer:v1 ./packer
docker build -t k8s-p2-frontend:v1 ./web_app
docker build -t k8s-p2-web-controller:v1 ./web_controller

for PART in $PARTS; do
	for DEPLOY in $(find ./$PART/*deployments.yaml 2> /dev/null); do
		kubectl create -f $DEPLOY
	done
	for SVC in $(find ./$PART/*service.yaml 2> /dev/null); do
		kubectl create -f $SVC
	done
done
