.PHONY: output
output-ubuntu-focal:
	$(shell chmod +x add-version.sh)
	$(shell ./add-version.sh)
	pipenv lock -r > requirements.txt
	DOCKER_BUILDKIT=1 docker build --output type=local,dest=out/ubuntu/focal --progress plain -f Dockerfile.ubuntufocal  .