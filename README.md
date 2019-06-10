# Genotick Continuous Simulator

Continuous simulation wrapper for the open-source [Genotick](https://genotick.com/) A.I. Trading Software project

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) ![GitHub last commit](https://img.shields.io/github/last-commit/mrhewitt/genotick-cs.svg) 

Basic Python wrapper that executes Genotick in a continous loop using a randomly selected market and settings from the raw folder.

Script is in its infancy and being committed only for backup purposes, so while it runs the simulation if does not process the results.

It will be updated soon to parse the Genotick output and save the population and settings of the best and worst performing populations.

Will also support multiple markets in standard Genotick data, as well as training for trading a base market using inter-market relationships by merging randomly selected markets into the base market dataset as additional inputs (rather than being traded as seperate markets)  

Date range is currently hard-coded from 2010 to end of 2018 leaving 2019 for a walk-forward (notes to come) which suits my current purpose, will become configurable later.
