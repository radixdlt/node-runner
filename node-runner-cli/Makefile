.PHONY: output
install:
	$(shell chmod +x add-version.sh)
	$(shell ./add-version.sh)
	pip install pipenv
	pipenv lock -r > requirements.txt

.PHONY: output
output-ubuntu-focal: install
	DOCKER_BUILDKIT=1 docker build --output type=local,dest=out/ubuntu/focal --progress plain -f Dockerfile.ubuntufocal  .