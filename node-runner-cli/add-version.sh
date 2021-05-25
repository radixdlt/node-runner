#!/bin/bash
LATEST_TAG=$(git describe --tags `git rev-list --tags --max-count=1`)
BASE_VERSION=$LATEST_TAG
DESCRIBED_TAG=$(git describe --tags)
if [ $LATEST_TAG == $DESCRIBED_TAG ] ; then
  VERSION=$LATEST_TAG
else
  VERSION=$DESCRIBED_TAG
fi
echo "__version__= \"$VERSION\"" > version/__init__.py
echo "__base_version__= \"$BASE_VERSION\"" >> version/__init__.py