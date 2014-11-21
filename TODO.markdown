TODO
====

* Add comments to RequestCreator class
* Check if setuptools is needed anymore
* Check changes in python pacaking

* Make little helper for making a release
    git tag "v$(cat VERSION)"
    git push --tags
    python setup.py sdist bdist upload
    echo "Now increase version in VERSION"
