from setuptools import setup, find_packages

setup(
	name="Genotick Continuous Simulator",
	version="0.2",
    author = "Mark Hewitt",
    author_email = "mr.mark.hewitt@gmail.com",
    description = ("A continous simulation wrapper and output graphing tool for Genotick Trading AI software"),
    license = "MIT",
    keywords = "trading ai genotick",
    url = "https://github.com/mrhewitt/genotick-cs",
	#packages=['simulate', 'advisor', 'ecurve', 'tests'],
	packages=find_packages(),
	install_requires=[
		'Click',
		'numpy',
		'pandas',
		'matplotlib',
	],
	 entry_points={ 
			'console_scripts': [
				'simulate=simulate:cli',
			#	'ecurve=ecurve:cli',
			#	'advisor=advisor:cli'
			],
		},
)		
