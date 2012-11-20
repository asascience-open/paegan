# Increment setup.py version

# Update CHANGES.txt
git log --pretty=format:%s\ \(%an\) 0.9.0..HEAD >> CHANGES.txt

# Upload
python setup.py sdist upload