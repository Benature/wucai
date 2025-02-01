version=0.0.4a0
project=wucai

prepare:
	pip install -r requirements.txt

clean:
	rm -rf ./dist
	rm -rf ./build

uninstall:
	pip uninstall ${project} -y

install:
	pip install -U .

build:
	python setup.py sdist bdist_wheel

all: uninstall clean build
	pip install -U dist/${project}-${version}-py3-none-any.whl

upload:
	twine upload dist/*