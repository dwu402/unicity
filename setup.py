import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
	name='unicity',  
	version='0.3',
	py_modules=['unicity'],
	author="David Dempsey",
	author_email="ddempsey786@gmail.com",
	description="Batch testing and similarity checking of python code.",
	long_description=long_description,
	long_description_content_type="text/markdown",
	packages=setuptools.find_packages(),
	install_requires=['numpy','scipy','matplotlib','fuzzywuzzy',],
	url="https://github.com/ddempsey/unicity",
	classifiers=[
		 "Programming Language :: Python :: 3",
		 "License :: OSI Approved :: MIT License",
		 "Operating System :: OS Independent",
	 ],
 )