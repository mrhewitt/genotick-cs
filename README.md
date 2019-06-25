# Genotick Continuous Simulator

Continuous simulation wrapper for the open-source [Genotick](https://genotick.com/) A.I. Trading Software project

![Python](https://img.shields.io/badge/python-3.5%20%7C%203.6%20%7C%203.7-blue.svg) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) ![GitHub last commit](https://img.shields.io/github/last-commit/mrhewitt/genotick-cs.svg) [![Build Status](https://travis-ci.org/mrhewitt/genotick-cs.svg?branch=master)](https://travis-ci.org/mrhewitt/genotick-cs)

Basic Python wrapper that executes Genotick in a continous loop using a randomly selected market and settings from the raw folder.

Script is in its infancy and being committed only for backup purposes. Currently script will run the simulations, and cache the results but further functionality is not yet fully implemented.

Will in future also support multiple markets in standard Genotick data, as well as training for trading a base market using inter-market relationships by merging randomly selected markets into the base market dataset as additional inputs (rather than being traded as seperate markets)  

### Genotick Notes

The Genotick version currently available from the website does not actually output the profit CSV data despite the setting. The functionality is available in the master but not yet actually implemented.

Additionally, Genotick money management is better suited to non-leveraged equity positions that margin trading, this simulator requires the output for analysis be in ticks, which makes more sense as it is both market and money independant. 

To use Genotick with this script you will need to build from the source using my fork that fixes both these issues. 

[https://gitlab.com/mrhewitt/genotick]
